def generate_program(ast):
    if ast[0] != 'program':
        raise Exception("AST inválida")

    if len(ast) == 4:
        _, program_name, statements, function_nodes = ast
    else:
        _, program_name, statements = ast
        function_nodes = []

    code = []
    label_counter = [0]
    functions = collect_functions(function_nodes)

    for stmt in statements:
        generate_statement(stmt, code, label_counter, functions, None)

    code.append("HALT")

    for function_node in function_nodes:
        generate_function(function_node, code, label_counter, functions)

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


def generate_function(function_node, code, label_counter, functions):
    _, return_type, name, param_name, body_statements = function_node

    code.append(f"FUNC {name}")
    code.append(f"PARAM {param_name}")
    code.append(f"DECL {name}")

    for stmt in body_statements:
        generate_statement(stmt, code, label_counter, functions, name)

    if not any(stmt[0] == 'return' for stmt in body_statements):
        code.append(f"LOAD {name}")
        code.append("RET")

    code.append("ENDFUNC")


def generate_statement(stmt, code, label_counter, functions, current_function):
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
            generate_expression(index_expr, code, functions)
            generate_expression(expr, code, functions)
            code.append(f"STOREARR {name}")
        else:
            generate_expression(expr, code, functions)
            code.append(f"STORE {target}")

    elif kind == 'print':
        _, items = stmt
        for item in items:
            if isinstance(item, tuple) and item[0] == 'string':
                code.append(f'PRINTSTR "{item[1]}"')
            else:
                generate_expression(item, code, functions)
                code.append("PRINT")

    elif kind == 'read':
        _, ids = stmt
        for target in ids:
            if isinstance(target, tuple) and target[0] == 'array_access':
                _, name, index_expr = target
                generate_expression(index_expr, code, functions)
                code.append(f"READARR {name}")
            else:
                code.append(f"READ {target}")

    elif kind == 'if':
        _, cond, then_statements, else_statements = stmt

        if else_statements is None:
            end_label = new_label(label_counter)

            generate_condition(cond, code, functions)
            code.append(f"JZ {end_label}")

            for inner_stmt in then_statements:
                generate_statement(inner_stmt, code, label_counter, functions, current_function)

            code.append(f"LABEL {end_label}")

        else:
            else_label = new_label(label_counter)
            end_label = new_label(label_counter)

            generate_condition(cond, code, functions)
            code.append(f"JZ {else_label}")

            for inner_stmt in then_statements:
                generate_statement(inner_stmt, code, label_counter, functions, current_function)

            code.append(f"JMP {end_label}")
            code.append(f"LABEL {else_label}")

            for inner_stmt in else_statements:
                generate_statement(inner_stmt, code, label_counter, functions, current_function)

            code.append(f"LABEL {end_label}")

    elif kind == 'do':
        _, label, var, start_expr, end_expr, body_statements = stmt
        start_label = new_label(label_counter)
        end_label = user_label(label)

        generate_expression(start_expr, code, functions)
        code.append(f"STORE {var}")

        code.append(f"LABEL {start_label}")
        code.append(f"LOAD {var}")
        generate_expression(end_expr, code, functions)
        code.append("CMPLE")
        code.append(f"JZ {end_label}")

        for inner_stmt in body_statements:
            generate_statement(inner_stmt, code, label_counter, functions, current_function)

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


def generate_expression(expr, code, functions):
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
        generate_expression(index_expr, code, functions)

        if name in functions:
            code.append(f"CALL {name}")
        else:
            code.append(f"LOADARR {name}")

    elif kind == 'binop':
        _, op, left, right = expr
        generate_expression(left, code, functions)
        generate_expression(right, code, functions)

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
        generate_expression(left, code, functions)
        generate_expression(right, code, functions)
        code.append("MOD")


def generate_condition(cond, code, functions):
    kind = cond[0]

    if kind in ('number', 'bool', 'id', 'array_access', 'binop'):
        generate_expression(cond, code, functions)

    elif kind == 'relop':
        _, op, left, right = cond
        generate_expression(left, code, functions)
        generate_expression(right, code, functions)

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
        generate_condition(left, code, functions)
        generate_condition(right, code, functions)

        if op == '.AND.':
            code.append("AND")
        elif op == '.OR.':
            code.append("OR")

    elif kind == 'not':
        generate_condition(cond[1], code, functions)
        code.append("NOT")
