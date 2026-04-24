SUPPORTED_EWVM_PHASE1_TYPES = {'INTEGER', 'REAL', 'LOGICAL'}


def normalize_program(ast):
    if ast[0] != 'program':
        raise Exception("AST inválida")

    if len(ast) == 4:
        _, program_name, statements, function_nodes = ast
    else:
        _, program_name, statements = ast
        function_nodes = []

    return program_name, statements, function_nodes


def generate_program(ast):
    if supports_ewvm_phase1(ast):
        return generate_program_ewvm_phase1(ast)

    return generate_program_legacy(ast)


def build_global_layout(statements):
    layout = {}
    offset = 0

    for stmt in statements:
        if stmt[0] != 'declare':
            continue

        _, var_type, ids = stmt
        if var_type not in SUPPORTED_EWVM_PHASE1_TYPES:
            continue

        for item in ids:
            item_kind, name, size = get_decl_info(item)
            if name in layout:
                continue

            if item_kind == 'array':
                layout[name] = {
                    'scope': 'global',
                    'storage': 'global',
                    'kind': 'array',
                    'type': var_type,
                    'offset': offset,
                    'size': size,
                }
                offset += size
            else:
                layout[name] = {
                    'scope': 'global',
                    'storage': 'global',
                    'kind': 'scalar',
                    'type': var_type,
                    'offset': offset,
                    'size': 1,
                }
                offset += 1

    return layout


def iter_layout(layout):
    return sorted(layout.items(), key=lambda item: item[1]['offset'])


def supports_ewvm_phase1(ast):
    _, statements, function_nodes = normalize_program(ast)
    layout = build_global_layout(statements)
    functions = collect_functions_ewvm(function_nodes)

    if functions is None:
        return False

    if not all(statement_supported_ewvm_phase1(stmt, layout, functions) for stmt in statements):
        return False

    for function_node in function_nodes:
        _, _, name, _, body_statements = function_node
        function_info = functions[name]

        if not all(
            statement_supported_ewvm_phase1(stmt, function_info['layout'], functions)
            for stmt in body_statements
        ):
            return False

    return True


def statement_supported_ewvm_phase1(stmt, layout, functions):
    kind = stmt[0]

    if kind == 'label':
        return statement_supported_ewvm_phase1(stmt[2], layout, functions)

    if kind == 'declare':
        _, var_type, ids = stmt
        if var_type not in SUPPORTED_EWVM_PHASE1_TYPES:
            return False

        for item in ids:
            item_kind, _, _ = get_decl_info(item)
            if item_kind not in ('scalar', 'array'):
                return False

        return True

    if kind == 'assign':
        _, target, expr = stmt
        if isinstance(target, str):
            return is_scalar_symbol(layout, target) and expression_supported_ewvm_phase1(expr, layout, functions)

        if isinstance(target, tuple) and target[0] == 'array_access':
            return array_access_supported_ewvm_phase1(target, layout, functions) and expression_supported_ewvm_phase1(expr, layout, functions)

        return False

    if kind == 'print':
        _, items = stmt
        return all(
            isinstance(item, tuple) and item[0] == 'string' or expression_supported_ewvm_phase1(item, layout, functions)
            for item in items
        )

    if kind == 'read':
        _, ids = stmt
        return all(
            (isinstance(target, str) and is_scalar_symbol(layout, target))
            or array_access_supported_ewvm_phase1(target, layout, functions)
            for target in ids
        )

    if kind == 'if':
        _, cond, then_statements, else_statements = stmt

        if not condition_supported_ewvm_phase1(cond, layout, functions):
            return False

        if not all(statement_supported_ewvm_phase1(inner_stmt, layout, functions) for inner_stmt in then_statements):
            return False

        if else_statements is not None and not all(
            statement_supported_ewvm_phase1(inner_stmt, layout, functions) for inner_stmt in else_statements
        ):
            return False

        return True

    if kind == 'goto':
        return True

    if kind == 'call':
        return False

    if kind == 'continue':
        return True

    if kind == 'do':
        _, _, var, start_expr, end_expr, body_statements = stmt

        if not expression_supported_ewvm_phase1(start_expr, layout, functions):
            return False

        if not expression_supported_ewvm_phase1(end_expr, layout, functions):
            return False

        if not isinstance(var, str):
            return False

        if not is_scalar_symbol(layout, var):
            return False

        return all(statement_supported_ewvm_phase1(inner_stmt, layout, functions) for inner_stmt in body_statements)

    if kind == 'return':
        return True

    return False


def expression_supported_ewvm_phase1(expr, layout, functions):
    kind = expr[0]

    if kind in ('number', 'bool', 'id'):
        if kind == 'id':
            return is_scalar_symbol(layout, expr[1])
        return True

    if kind == 'indexed':
        if function_call_supported_ewvm_phase1(expr, layout, functions):
            return True
        return array_access_supported_ewvm_phase1(expr, layout, functions)

    if kind == 'binop':
        _, op, left, right = expr
        if op not in ('+', '-', '*', '/'):
            return False

        if not expression_supported_ewvm_phase1(left, layout, functions):
            return False

        if not expression_supported_ewvm_phase1(right, layout, functions):
            return False

        return (
            infer_expression_type_ewvm_phase1(left, layout, functions) != 'LOGICAL'
            and infer_expression_type_ewvm_phase1(right, layout, functions) != 'LOGICAL'
        )

    if kind == 'mod':
        _, left, right = expr
        return (
            expression_supported_ewvm_phase1(left, layout, functions)
            and expression_supported_ewvm_phase1(right, layout, functions)
            and infer_expression_type_ewvm_phase1(left, layout, functions) == 'INTEGER'
            and infer_expression_type_ewvm_phase1(right, layout, functions) == 'INTEGER'
        )

    return False


def array_access_supported_ewvm_phase1(expr, layout, functions):
    if not isinstance(expr, tuple) or expr[0] not in ('array_access', 'indexed'):
        return False

    if expr[0] == 'array_access':
        _, name, index_expr = expr
    else:
        _, name, args = expr
        if len(args) != 1:
            return False
        index_expr = args[0]

    if not is_array_symbol(layout, name):
        return False

    if not expression_supported_ewvm_phase1(index_expr, layout, functions):
        return False

    return infer_expression_type_ewvm_phase1(index_expr, layout, functions) == 'INTEGER'


def function_call_supported_ewvm_phase1(expr, layout, functions):
    if not isinstance(expr, tuple) or expr[0] != 'indexed':
        return False

    _, name, arg_exprs = expr
    function_info = functions.get(name)

    if function_info is None:
        return False

    param_types = function_info['param_types']
    if len(arg_exprs) != len(param_types):
        return False

    for arg_expr, param_type in zip(arg_exprs, param_types):
        if not expression_supported_ewvm_phase1(arg_expr, layout, functions):
            return False

        arg_type = infer_expression_type_ewvm_phase1(arg_expr, layout, functions)
        if not compatible_ewvm_types(param_type, arg_type):
            return False

    return True


def condition_supported_ewvm_phase1(cond, layout, functions):
    kind = cond[0]

    if kind == 'relop':
        _, _, left, right = cond
        if not expression_supported_ewvm_phase1(left, layout, functions):
            return False

        if not expression_supported_ewvm_phase1(right, layout, functions):
            return False

        return (
            infer_expression_type_ewvm_phase1(left, layout, functions) != 'LOGICAL'
            and infer_expression_type_ewvm_phase1(right, layout, functions) != 'LOGICAL'
        )

    if kind == 'logicop':
        _, _, left, right = cond
        return (
            condition_supported_ewvm_phase1(left, layout, functions)
            and condition_supported_ewvm_phase1(right, layout, functions)
        )

    if kind == 'not':
        return condition_supported_ewvm_phase1(cond[1], layout, functions)

    if kind in ('bool', 'id', 'indexed'):
        return (
            expression_supported_ewvm_phase1(cond, layout, functions)
            and infer_expression_type_ewvm_phase1(cond, layout, functions) == 'LOGICAL'
        )

    return False


def compatible_ewvm_types(target_type, expr_type):
    if target_type == expr_type:
        return True

    if target_type == 'REAL' and expr_type == 'INTEGER':
        return True

    return False


def emit_ewvm_type_conversion(source_type, target_type, code):
    if source_type == target_type:
        return

    if target_type == 'REAL' and source_type == 'INTEGER':
        code.append("ITOF")
        return

    raise NotImplementedError(f"Conversão EWVM não suportada: {source_type} -> {target_type}")


def ewvm_string(value):
    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"'


def get_global_info(layout, name):
    info = layout.get(name)
    if info is None:
        raise Exception(f"Símbolo '{name}' não encontrado no layout EWVM")

    return info


def is_scalar_symbol(layout, name):
    info = layout.get(name)
    return info is not None and info['kind'] == 'scalar'


def is_array_symbol(layout, name):
    info = layout.get(name)
    return info is not None and info['kind'] == 'array'


def collect_functions_ewvm(function_nodes):
    functions = {}

    for function_node in function_nodes:
        if function_node[0] != 'function':
            return None

        _, return_type, name, param_names, body_statements = function_node

        if return_type not in SUPPORTED_EWVM_PHASE1_TYPES:
            return None

        local_layout = {
            name: {
                'kind': 'scalar',
                'storage': 'local',
                'type': return_type,
                'offset': 0,
            }
        }
        local_offset = 1
        param_types_by_name = {param_name: None for param_name in param_names}

        for stmt in body_statements:
            kind = stmt[0]

            if kind == 'declare':
                _, var_type, ids = stmt
                if var_type not in SUPPORTED_EWVM_PHASE1_TYPES:
                    return None

                for item in ids:
                    item_kind, decl_name, _ = get_decl_info(item)
                    if item_kind != 'scalar':
                        return None

                    if decl_name in param_types_by_name:
                        param_types_by_name[decl_name] = var_type
                        continue

                    if decl_name == name or decl_name in local_layout:
                        continue

                    local_layout[decl_name] = {
                        'kind': 'scalar',
                        'storage': 'local',
                        'type': var_type,
                        'offset': local_offset,
                    }
                    local_offset += 1

        param_types = []
        param_count = len(param_names)
        for index, param_name in enumerate(param_names):
            param_type = param_types_by_name[param_name]
            if param_type not in SUPPORTED_EWVM_PHASE1_TYPES:
                return None

            param_types.append(param_type)
            local_layout[param_name] = {
                'kind': 'scalar',
                'storage': 'param',
                'type': param_type,
                'offset': index - param_count,
            }

        functions[name] = {
            'label': f"FUNC{name}",
            'return_type': return_type,
            'param_names': param_names,
            'param_types': param_types,
            'layout': local_layout,
            'body': body_statements,
            'local_slots': local_offset,
        }

    return functions


def infer_expression_type_ewvm_phase1(expr, layout, functions=None):
    kind = expr[0]
    if functions is None:
        functions = {}

    if kind == 'number':
        return 'REAL' if isinstance(expr[1], float) else 'INTEGER'

    if kind == 'bool':
        return 'LOGICAL'

    if kind == 'id':
        return get_global_info(layout, expr[1])['type']

    if kind == 'indexed':
        _, name, arg_exprs = expr
        if name in functions:
            function_info = functions[name]
            if len(arg_exprs) != len(function_info['param_types']):
                raise NotImplementedError("Chamada EWVM com número de argumentos incompatível")

            for arg_expr, param_type in zip(arg_exprs, function_info['param_types']):
                arg_type = infer_expression_type_ewvm_phase1(arg_expr, layout, functions)
                if not compatible_ewvm_types(param_type, arg_type):
                    raise NotImplementedError("Chamada EWVM com argumento incompatível")

            return function_info['return_type']

        if len(arg_exprs) != 1:
            raise NotImplementedError("Indexações EWVM só suportam um argumento")

        index_expr = arg_exprs[0]
        info = get_global_info(layout, name)

        if info['kind'] != 'array':
            raise NotImplementedError("Acesso indexado EWVM apenas suporta arrays globais")

        index_type = infer_expression_type_ewvm_phase1(index_expr, layout, functions)
        if index_type != 'INTEGER':
            raise NotImplementedError("Índice de array EWVM deve ser INTEGER")

        return info['type']

    if kind == 'binop':
        _, _, left, right = expr
        left_type = infer_expression_type_ewvm_phase1(left, layout, functions)
        right_type = infer_expression_type_ewvm_phase1(right, layout, functions)

        if left_type == 'REAL' or right_type == 'REAL':
            return 'REAL'
        return 'INTEGER'

    if kind == 'mod':
        _, left, right = expr
        left_type = infer_expression_type_ewvm_phase1(left, layout, functions)
        right_type = infer_expression_type_ewvm_phase1(right, layout, functions)

        if left_type == 'INTEGER' and right_type == 'INTEGER':
            return 'INTEGER'

        raise NotImplementedError("MOD na EWVM só é suportado com operandos INTEGER")

    raise NotImplementedError(f"Expressão não suportada na fase EWVM 1: {kind}")


def emit_global_initialization_ewvm_phase1(code, layout):
    for _, info in iter_layout(layout):
        if info['kind'] == 'array':
            if info['type'] == 'REAL':
                for _ in range(info['size']):
                    code.append("PUSHF 0.0")
            else:
                code.append(f"PUSHN {info['size']}")
        else:
            if info['type'] == 'REAL':
                code.append("PUSHF 0.0")
            else:
                code.append("PUSHI 0")


def emit_label_ewvm_phase1(code, label):
    code.append(f"{label}:")


def emit_global_address_ewvm_phase1(info, code):
    code.append("PUSHGP")
    if info['offset'] != 0:
        code.append(f"PUSHI {info['offset']}")
        code.append("PADD")


def generate_array_index_ewvm_phase1(index_expr, code, layout, functions):
    index_type = generate_expression_ewvm_phase1(index_expr, code, layout, functions)

    if index_type != 'INTEGER':
        raise NotImplementedError("Índice de array EWVM deve ser INTEGER")

    code.append("PUSHI 1")
    code.append("SUB")


def emit_scalar_load_ewvm_phase1(info, code):
    if info.get('storage') == 'global':
        code.append(f"PUSHG {info['offset']}")
        return

    if info.get('storage') == 'param':
        code.append("PUSHFP")
        code.append(f"LOAD {info['offset']}")
        return

    code.append(f"PUSHL {info['offset']}")


def emit_scalar_store_ewvm_phase1(info, code):
    if info.get('storage') == 'global':
        code.append(f"STOREG {info['offset']}")
        return

    code.append(f"STOREL {info['offset']}")


def emit_slot_initialization_ewvm_phase1(info, code):
    if info['type'] == 'REAL':
        code.append("PUSHF 0.0")
    else:
        code.append("PUSHI 0")


def has_explicit_return(statements):
    for stmt in statements:
        kind = stmt[0]
        if kind == 'return':
            return True

        if kind == 'label' and has_explicit_return([stmt[2]]):
            return True

    return False


def generate_expression_ewvm_phase1(expr, code, layout, functions):
    kind = expr[0]

    if kind == 'number':
        value = expr[1]
        if isinstance(value, float):
            code.append(f"PUSHF {value}")
            return 'REAL'

        code.append(f"PUSHI {value}")
        return 'INTEGER'

    if kind == 'bool':
        code.append("PUSHI 1" if expr[1] else "PUSHI 0")
        return 'LOGICAL'

    if kind == 'id':
        info = get_global_info(layout, expr[1])
        emit_scalar_load_ewvm_phase1(info, code)
        return info['type']

    if kind == 'indexed':
        _, name, arg_exprs = expr
        if name in functions:
            function_info = functions[name]
            param_types = function_info['param_types']
            if len(arg_exprs) != len(param_types):
                raise NotImplementedError("Chamada EWVM com número de argumentos incompatível")

            if not arg_exprs:
                code.append("PUSHI 0")

            for arg_expr, param_type in zip(arg_exprs, param_types):
                arg_type = generate_expression_ewvm_phase1(arg_expr, code, layout, functions)
                emit_ewvm_type_conversion(arg_type, param_type, code)

            code.append(f"PUSHA {function_info['label']}")
            code.append("CALL")

            for _ in range(max(0, len(arg_exprs) - 1)):
                code.append("SWAP")
                code.append("POP 1")

            return function_info['return_type']

        if len(arg_exprs) != 1:
            raise NotImplementedError("Indexações EWVM só suportam um argumento")

        index_expr = arg_exprs[0]
        info = get_global_info(layout, name)

        if info['kind'] != 'array':
            raise NotImplementedError("Acesso indexado EWVM apenas suporta arrays globais")

        emit_global_address_ewvm_phase1(info, code)
        generate_array_index_ewvm_phase1(index_expr, code, layout, functions)
        code.append("LOADN")
        return info['type']

    if kind == 'binop':
        _, op, left, right = expr
        left_type = infer_expression_type_ewvm_phase1(left, layout, functions)
        right_type = infer_expression_type_ewvm_phase1(right, layout, functions)
        if left_type == 'LOGICAL' or right_type == 'LOGICAL':
            raise NotImplementedError("Operações aritméticas EWVM não suportam LOGICAL")

        result_type = 'REAL' if left_type == 'REAL' or right_type == 'REAL' else 'INTEGER'

        generate_expression_ewvm_phase1(left, code, layout, functions)
        emit_ewvm_type_conversion(left_type, result_type, code)

        generate_expression_ewvm_phase1(right, code, layout, functions)
        emit_ewvm_type_conversion(right_type, result_type, code)

        int_ops = {'+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV'}
        real_ops = {'+': 'FADD', '-': 'FSUB', '*': 'FMUL', '/': 'FDIV'}
        code.append(real_ops[op] if result_type == 'REAL' else int_ops[op])
        return result_type

    if kind == 'mod':
        _, left, right = expr
        left_type = infer_expression_type_ewvm_phase1(left, layout, functions)
        right_type = infer_expression_type_ewvm_phase1(right, layout, functions)

        if left_type != 'INTEGER' or right_type != 'INTEGER':
            raise NotImplementedError("MOD na EWVM só é suportado com operandos INTEGER")

        generate_expression_ewvm_phase1(left, code, layout, functions)
        generate_expression_ewvm_phase1(right, code, layout, functions)
        code.append("MOD")
        return 'INTEGER'

    raise NotImplementedError(f"Expressão não suportada na fase EWVM 1: {kind}")


def generate_condition_ewvm_phase1(cond, code, layout, functions):
    kind = cond[0]

    if kind == 'logicop':
        _, op, left, right = cond
        generate_condition_ewvm_phase1(left, code, layout, functions)
        generate_condition_ewvm_phase1(right, code, layout, functions)
        code.append("AND" if op == '.AND.' else "OR")
        return

    if kind == 'not':
        generate_condition_ewvm_phase1(cond[1], code, layout, functions)
        code.append("NOT")
        return

    if kind in ('bool', 'id', 'indexed'):
        cond_type = generate_expression_ewvm_phase1(cond, code, layout, functions)
        if cond_type != 'LOGICAL':
            raise NotImplementedError(f"Condição EWVM deve ser LOGICAL, obtido {cond_type}")
        return

    if kind != 'relop':
        raise NotImplementedError(f"Condição não suportada na fase EWVM 1: {kind}")

    _, op, left, right = cond
    left_type = infer_expression_type_ewvm_phase1(left, layout, functions)
    right_type = infer_expression_type_ewvm_phase1(right, layout, functions)
    comparison_type = 'REAL' if left_type == 'REAL' or right_type == 'REAL' else 'INTEGER'

    generate_expression_ewvm_phase1(left, code, layout, functions)
    emit_ewvm_type_conversion(left_type, comparison_type, code)

    generate_expression_ewvm_phase1(right, code, layout, functions)
    emit_ewvm_type_conversion(right_type, comparison_type, code)

    equality_ops = {
        '.EQ.': ['EQUAL'],
        '.NE.': ['EQUAL', 'NOT'],
    }
    int_ops = {
        '.LT.': ['INF'],
        '.LE.': ['INFEQ'],
        '.GT.': ['SUP'],
        '.GE.': ['SUPEQ'],
    }
    real_ops = {
        '.LT.': ['FINF'],
        '.LE.': ['FINFEQ'],
        '.GT.': ['FSUP'],
        '.GE.': ['FSUPEQ'],
    }

    if op in equality_ops:
        code.extend(equality_ops[op])
        return

    ops = real_ops if comparison_type == 'REAL' else int_ops
    code.extend(ops[op])


def generate_statement_ewvm_phase1(stmt, code, layout, functions, label_counter, current_function=None):
    kind = stmt[0]

    if kind == 'declare':
        return

    if kind == 'assign':
        _, target, expr = stmt
        if isinstance(target, tuple) and target[0] == 'array_access':
            _, name, index_expr = target
            info = get_global_info(layout, name)

            if info['kind'] != 'array':
                raise NotImplementedError("Atribuição indexada EWVM apenas suporta arrays globais")

            emit_global_address_ewvm_phase1(info, code)
            generate_array_index_ewvm_phase1(index_expr, code, layout, functions)
            expr_type = generate_expression_ewvm_phase1(expr, code, layout, functions)
            emit_ewvm_type_conversion(expr_type, info['type'], code)

            code.append("STOREN")
            return

        info = get_global_info(layout, target)
        expr_type = generate_expression_ewvm_phase1(expr, code, layout, functions)
        emit_ewvm_type_conversion(expr_type, info['type'], code)

        emit_scalar_store_ewvm_phase1(info, code)
        return

    if kind == 'read':
        _, ids = stmt
        for target in ids:
            if isinstance(target, tuple) and target[0] == 'array_access':
                _, name, index_expr = target
                info = get_global_info(layout, name)

                if info['kind'] != 'array':
                    raise NotImplementedError("READ indexado EWVM apenas suporta arrays globais")

                emit_global_address_ewvm_phase1(info, code)
                generate_array_index_ewvm_phase1(index_expr, code, layout, functions)
                code.append("READ")
                code.append("ATOF" if info['type'] == 'REAL' else "ATOI")
                code.append("STOREN")
                continue

            info = get_global_info(layout, target)
            code.append("READ")
            code.append("ATOF" if info['type'] == 'REAL' else "ATOI")
            emit_scalar_store_ewvm_phase1(info, code)
        return

    if kind == 'print':
        _, items = stmt
        for item in items:
            if isinstance(item, tuple) and item[0] == 'string':
                code.append(f"PUSHS {ewvm_string(item[1])}")
                code.append("WRITES")
                continue

            item_type = generate_expression_ewvm_phase1(item, code, layout, functions)
            code.append("WRITEF" if item_type == 'REAL' else "WRITEI")

        code.append("WRITELN")
        return

    if kind == 'if':
        _, cond, then_statements, else_statements = stmt

        if else_statements is None:
            end_label = new_label(label_counter)

            generate_condition_ewvm_phase1(cond, code, layout, functions)
            code.append(f"JZ {end_label}")

            for inner_stmt in then_statements:
                generate_statement_ewvm_phase1(inner_stmt, code, layout, functions, label_counter, current_function)

            emit_label_ewvm_phase1(code, end_label)
            return

        else_label = new_label(label_counter)
        end_label = new_label(label_counter)

        generate_condition_ewvm_phase1(cond, code, layout, functions)
        code.append(f"JZ {else_label}")

        for inner_stmt in then_statements:
            generate_statement_ewvm_phase1(inner_stmt, code, layout, functions, label_counter, current_function)

        code.append(f"JUMP {end_label}")
        emit_label_ewvm_phase1(code, else_label)

        for inner_stmt in else_statements:
            generate_statement_ewvm_phase1(inner_stmt, code, layout, functions, label_counter, current_function)

        emit_label_ewvm_phase1(code, end_label)
        return

    if kind == 'goto':
        _, label = stmt
        code.append(f"JUMP {user_label(label, current_function)}")
        return

    if kind == 'label':
        _, label, inner_stmt = stmt
        emit_label_ewvm_phase1(code, user_label(label, current_function))
        generate_statement_ewvm_phase1(inner_stmt, code, layout, functions, label_counter, current_function)
        return

    if kind == 'continue':
        return

    if kind == 'do':
        _, label, var, start_expr, end_expr, body_statements = stmt
        start_label = new_label(label_counter)
        end_label = user_label(label, current_function)
        control_info = get_global_info(layout, var)

        start_type = generate_expression_ewvm_phase1(start_expr, code, layout, functions)
        emit_ewvm_type_conversion(start_type, control_info['type'], code)
        emit_scalar_store_ewvm_phase1(control_info, code)

        emit_label_ewvm_phase1(code, start_label)
        generate_condition_ewvm_phase1(
            ('relop', '.LE.', ('id', var), end_expr),
            code,
            layout,
            functions,
        )
        code.append(f"JZ {end_label}")

        for inner_stmt in body_statements:
            generate_statement_ewvm_phase1(inner_stmt, code, layout, functions, label_counter, current_function)

        emit_scalar_load_ewvm_phase1(control_info, code)
        if control_info['type'] == 'REAL':
            code.append("PUSHF 1.0")
            code.append("FADD")
        else:
            code.append("PUSHI 1")
            code.append("ADD")
        emit_scalar_store_ewvm_phase1(control_info, code)
        code.append(f"JUMP {start_label}")
        emit_label_ewvm_phase1(code, end_label)
        return

    if kind == 'return':
        function_info = functions[current_function]
        emit_scalar_load_ewvm_phase1(function_info['layout'][current_function], code)
        code.append("STOREL -1")
        code.append("RETURN")
        return

    raise NotImplementedError(f"Statement não suportado na fase EWVM 1: {kind}")


def generate_function_ewvm_phase1(function_node, function_info, code, functions, label_counter):
    _, _, name, _, body_statements = function_node

    emit_label_ewvm_phase1(code, function_info['label'])

    for local_name, info in sorted(function_info['layout'].items(), key=lambda item: item[1]['offset']):
        if info['storage'] == 'local':
            emit_slot_initialization_ewvm_phase1(info, code)

    for stmt in body_statements:
        generate_statement_ewvm_phase1(
            stmt,
            code,
            function_info['layout'],
            functions,
            label_counter,
            current_function=name,
        )

    if not has_explicit_return(body_statements):
        emit_scalar_load_ewvm_phase1(function_info['layout'][name], code)
        code.append("STOREL -1")
        code.append("RETURN")


def generate_program_ewvm_phase1(ast):
    _, statements, function_nodes = normalize_program(ast)
    layout = build_global_layout(statements)
    functions = collect_functions_ewvm(function_nodes)
    code = []
    label_counter = [0]

    emit_global_initialization_ewvm_phase1(code, layout)
    code.append("START")

    for stmt in statements:
        generate_statement_ewvm_phase1(stmt, code, layout, functions, label_counter)

    code.append("STOP")

    for function_node in function_nodes:
        _, _, name, _, _ = function_node
        generate_function_ewvm_phase1(function_node, functions[name], code, functions, label_counter)

    return code


def generate_program_legacy(ast):
    _, statements, function_nodes = normalize_program(ast)

    code = []
    label_counter = [0]
    functions = collect_functions(function_nodes)

    for stmt in statements:
        generate_statement_legacy(stmt, code, label_counter, functions, None)

    code.append("HALT")

    for function_node in function_nodes:
        generate_function_legacy(function_node, code, label_counter, functions)

    return code


def new_label(label_counter):
    label = f"L{label_counter[0]}"
    label_counter[0] += 1
    return label


def user_label(label, current_function=None):
    if current_function is None:
        return f"LBL{label}"

    return f"{current_function}LBL{label}"


def collect_functions(function_nodes):
    functions = {}

    for function_node in function_nodes:
        kind = function_node[0]

        if kind == 'function':
            _, return_type, name, param_names, body_statements = function_node
        elif kind == 'subroutine':
            _, name, param_names, body_statements = function_node
            return_type = None
        else:
            continue

        functions[name] = {
            'kind': kind,
            'return_type': return_type,
            'param_names': param_names,
            'body': body_statements,
        }

    return functions


def get_decl_info(item):
    if isinstance(item, tuple):
        if item[0] == 'scalar':
            return 'scalar', item[1], None
        if item[0] == 'array':
            return 'array', item[1], item[2]

    return 'scalar', item, None


def generate_function_legacy(function_node, code, label_counter, functions):
    kind = function_node[0]

    if kind == 'function':
        _, return_type, name, param_names, body_statements = function_node
        code.append(f"FUNC {name}")
    else:
        _, name, param_names, body_statements = function_node
        code.append(f"SUBROUTINE {name}")

    for param_name in param_names:
        code.append(f"PARAM {param_name}")

    if kind == 'function':
        code.append(f"DECL {name}")

    for stmt in body_statements:
        generate_statement_legacy(stmt, code, label_counter, functions, name)

    if not has_explicit_return(body_statements):
        if kind == 'function':
            code.append(f"LOAD {name}")
        code.append("RET")

    code.append("ENDFUNC" if kind == 'function' else "ENDSUBROUTINE")


def generate_statement_legacy(stmt, code, label_counter, functions, current_function):
    kind = stmt[0]

    if kind == 'label':
        _, label, inner_stmt = stmt
        code.append(f"LABEL {user_label(label)}")
        generate_statement_legacy(inner_stmt, code, label_counter, functions, current_function)

    elif kind == 'declare':
        _, var_type, ids = stmt
        for item in ids:
            item_kind, name, size = get_decl_info(item)
            if item_kind == 'array':
                code.append(f"DECLARR {name} {size}")
            else:
                code.append(f"DECL {name}")

    elif kind == 'assign':
        _, target, expr = stmt

        if isinstance(target, tuple) and target[0] == 'array_access':
            _, name, index_expr = target
            generate_expression_legacy(index_expr, code, functions)
            generate_expression_legacy(expr, code, functions)
            code.append(f"STOREARR {name}")
        else:
            generate_expression_legacy(expr, code, functions)
            code.append(f"STORE {target}")

    elif kind == 'print':
        _, items = stmt
        for item in items:
            if isinstance(item, tuple) and item[0] == 'string':
                code.append(f'PRINTSTR "{item[1]}"')
            else:
                generate_expression_legacy(item, code, functions)
                code.append("PRINT")

    elif kind == 'read':
        _, ids = stmt
        for target in ids:
            if isinstance(target, tuple) and target[0] == 'array_access':
                _, name, index_expr = target
                generate_expression_legacy(index_expr, code, functions)
                code.append(f"READARR {name}")
            else:
                code.append(f"READ {target}")

    elif kind == 'if':
        _, cond, then_statements, else_statements = stmt

        if else_statements is None:
            end_label = new_label(label_counter)

            generate_condition_legacy(cond, code, functions)
            code.append(f"JZ {end_label}")

            for inner_stmt in then_statements:
                generate_statement_legacy(inner_stmt, code, label_counter, functions, current_function)

            code.append(f"LABEL {end_label}")

        else:
            else_label = new_label(label_counter)
            end_label = new_label(label_counter)

            generate_condition_legacy(cond, code, functions)
            code.append(f"JZ {else_label}")

            for inner_stmt in then_statements:
                generate_statement_legacy(inner_stmt, code, label_counter, functions, current_function)

            code.append(f"JMP {end_label}")
            code.append(f"LABEL {else_label}")

            for inner_stmt in else_statements:
                generate_statement_legacy(inner_stmt, code, label_counter, functions, current_function)

            code.append(f"LABEL {end_label}")

    elif kind == 'do':
        _, label, var, start_expr, end_expr, body_statements = stmt
        start_label = new_label(label_counter)
        end_label = user_label(label)

        generate_expression_legacy(start_expr, code, functions)
        code.append(f"STORE {var}")

        code.append(f"LABEL {start_label}")
        code.append(f"LOAD {var}")
        generate_expression_legacy(end_expr, code, functions)
        code.append("CMPLE")
        code.append(f"JZ {end_label}")

        for inner_stmt in body_statements:
            generate_statement_legacy(inner_stmt, code, label_counter, functions, current_function)

        code.append(f"LOAD {var}")
        code.append("PUSH 1")
        code.append("ADD")
        code.append(f"STORE {var}")
        code.append(f"JMP {start_label}")
        code.append(f"LABEL {end_label}")

    elif kind == 'continue':
        return

    elif kind == 'goto':
        _, label = stmt
        code.append(f"JMP {user_label(label)}")

    elif kind == 'call':
        _, name, arg_exprs = stmt
        for arg_expr in arg_exprs:
            generate_expression_legacy(arg_expr, code, functions)
        code.append(f"CALL {name}")

    elif kind == 'return':
        if functions[current_function]['kind'] == 'function':
            code.append(f"LOAD {current_function}")
        code.append("RET")


def generate_expression_legacy(expr, code, functions):
    kind = expr[0]

    if kind == 'number':
        code.append(f"PUSH {expr[1]}")

    elif kind == 'bool':
        value = 1 if expr[1] else 0
        code.append(f"PUSH {value}")

    elif kind == 'id':
        code.append(f"LOAD {expr[1]}")

    elif kind == 'indexed':
        _, name, args = expr

        if name in functions:
            if functions[name]['kind'] != 'function':
                raise NotImplementedError("Subrotina não pode ser usada como expressão")
            for arg_expr in args:
                generate_expression_legacy(arg_expr, code, functions)
            code.append(f"CALL {name}")
        else:
            if len(args) != 1:
                raise NotImplementedError("Arrays legacy só suportam um índice")

            generate_expression_legacy(args[0], code, functions)
            code.append(f"LOADARR {name}")

    elif kind == 'binop':
        _, op, left, right = expr
        generate_expression_legacy(left, code, functions)
        generate_expression_legacy(right, code, functions)

        if op == '+':
            code.append("ADD")
        elif op == '-':
            code.append("SUB")
        elif op == '*':
            code.append("MUL")
        elif op == '/':
            code.append("DIV")

    elif kind == 'mod':
        _, left, right = expr
        generate_expression_legacy(left, code, functions)
        generate_expression_legacy(right, code, functions)
        code.append("MOD")


def generate_condition_legacy(cond, code, functions):
    kind = cond[0]

    if kind in ('number', 'bool', 'id', 'indexed', 'binop'):
        generate_expression_legacy(cond, code, functions)

    elif kind == 'relop':
        _, op, left, right = cond
        generate_expression_legacy(left, code, functions)
        generate_expression_legacy(right, code, functions)

        if op == '.EQ.':
            code.append("CMPEQ")
        elif op == '.NE.':
            code.append("CMPNE")
        elif op == '.LT.':
            code.append("CMPLT")
        elif op == '.LE.':
            code.append("CMPLE")
        elif op == '.GT.':
            code.append("CMPGT")
        elif op == '.GE.':
            code.append("CMPGE")

    elif kind == 'logicop':
        _, op, left, right = cond
        generate_condition_legacy(left, code, functions)
        generate_condition_legacy(right, code, functions)

        if op == '.AND.':
            code.append("AND")
        elif op == '.OR.':
            code.append("OR")

    elif kind == 'not':
        generate_condition_legacy(cond[1], code, functions)
        code.append("NOT")
