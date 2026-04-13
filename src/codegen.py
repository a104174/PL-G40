SUPPORTED_EWVM_PHASE1_TYPES = {'INTEGER', 'REAL'}


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
            if item_kind != 'scalar':
                continue

            if name in layout:
                continue

            layout[name] = {
                'scope': 'global',
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

    if function_nodes:
        return False

    return all(statement_supported_ewvm_phase1(stmt) for stmt in statements)


def statement_supported_ewvm_phase1(stmt):
    kind = stmt[0]

    if kind == 'declare':
        _, var_type, ids = stmt
        if var_type not in SUPPORTED_EWVM_PHASE1_TYPES:
            return False

        for item in ids:
            item_kind, _, _ = get_decl_info(item)
            if item_kind != 'scalar':
                return False

        return True

    if kind == 'assign':
        _, target, expr = stmt
        return isinstance(target, str) and expression_supported_ewvm_phase1(expr)

    if kind == 'print':
        _, items = stmt
        return all(
            isinstance(item, tuple) and item[0] == 'string' or expression_supported_ewvm_phase1(item)
            for item in items
        )

    if kind == 'read':
        _, ids = stmt
        return all(isinstance(target, str) for target in ids)

    return False


def expression_supported_ewvm_phase1(expr):
    kind = expr[0]

    if kind in ('number', 'id'):
        return True

    if kind == 'binop':
        _, op, left, right = expr
        return op in ('+', '-', '*', '/') and (
            expression_supported_ewvm_phase1(left)
            and expression_supported_ewvm_phase1(right)
        )

    return False


def ewvm_string(value):
    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"'


def get_global_info(layout, name):
    info = layout.get(name)
    if info is None:
        raise Exception(f"Variável global '{name}' não encontrada no layout EWVM")

    return info


def infer_expression_type_ewvm_phase1(expr, layout):
    kind = expr[0]

    if kind == 'number':
        return 'REAL' if isinstance(expr[1], float) else 'INTEGER'

    if kind == 'id':
        return get_global_info(layout, expr[1])['type']

    if kind == 'binop':
        _, _, left, right = expr
        left_type = infer_expression_type_ewvm_phase1(left, layout)
        right_type = infer_expression_type_ewvm_phase1(right, layout)

        if left_type == 'REAL' or right_type == 'REAL':
            return 'REAL'
        return 'INTEGER'

    raise NotImplementedError(f"Expressão não suportada na fase EWVM 1: {kind}")


def emit_global_initialization_ewvm_phase1(code, layout):
    for _, info in iter_layout(layout):
        if info['type'] == 'REAL':
            code.append("PUSHF 0.0")
        else:
            code.append("PUSHI 0")


def generate_expression_ewvm_phase1(expr, code, layout):
    kind = expr[0]

    if kind == 'number':
        value = expr[1]
        if isinstance(value, float):
            code.append(f"PUSHF {value}")
            return 'REAL'

        code.append(f"PUSHI {value}")
        return 'INTEGER'

    if kind == 'id':
        info = get_global_info(layout, expr[1])
        code.append(f"PUSHG {info['offset']}")
        return info['type']

    if kind == 'binop':
        _, op, left, right = expr
        left_type = infer_expression_type_ewvm_phase1(left, layout)
        right_type = infer_expression_type_ewvm_phase1(right, layout)
        result_type = 'REAL' if left_type == 'REAL' or right_type == 'REAL' else 'INTEGER'

        generate_expression_ewvm_phase1(left, code, layout)
        if result_type == 'REAL' and left_type == 'INTEGER':
            code.append("ITOF")

        generate_expression_ewvm_phase1(right, code, layout)
        if result_type == 'REAL' and right_type == 'INTEGER':
            code.append("ITOF")

        int_ops = {'+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV'}
        real_ops = {'+': 'FADD', '-': 'FSUB', '*': 'FMUL', '/': 'FDIV'}
        code.append(real_ops[op] if result_type == 'REAL' else int_ops[op])
        return result_type

    raise NotImplementedError(f"Expressão não suportada na fase EWVM 1: {kind}")


def generate_statement_ewvm_phase1(stmt, code, layout):
    kind = stmt[0]

    if kind == 'declare':
        return

    if kind == 'assign':
        _, target, expr = stmt
        info = get_global_info(layout, target)
        expr_type = generate_expression_ewvm_phase1(expr, code, layout)

        if info['type'] == 'REAL' and expr_type == 'INTEGER':
            code.append("ITOF")

        code.append(f"STOREG {info['offset']}")
        return

    if kind == 'read':
        _, ids = stmt
        for target in ids:
            info = get_global_info(layout, target)
            code.append("READ")
            code.append("ATOF" if info['type'] == 'REAL' else "ATOI")
            code.append(f"STOREG {info['offset']}")
        return

    if kind == 'print':
        _, items = stmt
        for item in items:
            if isinstance(item, tuple) and item[0] == 'string':
                code.append(f"PUSHS {ewvm_string(item[1])}")
                code.append("WRITES")
                continue

            item_type = generate_expression_ewvm_phase1(item, code, layout)
            code.append("WRITEF" if item_type == 'REAL' else "WRITEI")

        code.append("WRITELN")
        return

    raise NotImplementedError(f"Statement não suportado na fase EWVM 1: {kind}")


def generate_program_ewvm_phase1(ast):
    _, statements, _ = normalize_program(ast)
    layout = build_global_layout(statements)
    code = []

    emit_global_initialization_ewvm_phase1(code, layout)
    code.append("START")

    for stmt in statements:
        generate_statement_ewvm_phase1(stmt, code, layout)

    code.append("STOP")
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


def user_label(label):
    return f"LBL_{label}"


def collect_functions(function_nodes):
    functions = {}

    for function_node in function_nodes:
        _, return_type, name, param_name, body_statements = function_node
        functions[name] = {
            'return_type': return_type,
            'param_name': param_name,
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
    _, return_type, name, param_name, body_statements = function_node

    code.append(f"FUNC {name}")
    code.append(f"PARAM {param_name}")
    code.append(f"DECL {name}")

    for stmt in body_statements:
        generate_statement_legacy(stmt, code, label_counter, functions, name)

    if not any(stmt[0] == 'return' for stmt in body_statements):
        code.append(f"LOAD {name}")
        code.append("RET")

    code.append("ENDFUNC")


def generate_statement_legacy(stmt, code, label_counter, functions, current_function):
    kind = stmt[0]

    if kind == 'declare':
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
        _, label = stmt
        code.append(f"LABEL {user_label(label)}")

    elif kind == 'goto':
        _, label = stmt
        code.append(f"JMP {user_label(label)}")

    elif kind == 'return':
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

    elif kind == 'array_access':
        _, name, index_expr = expr
        generate_expression_legacy(index_expr, code, functions)

        if name in functions:
            code.append(f"CALL {name}")
        else:
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

    if kind in ('number', 'bool', 'id', 'array_access', 'binop'):
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
