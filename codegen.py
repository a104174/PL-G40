def generate_program(ast):
    if ast[0] != 'program':
        raise Exception("AST inválida")

    _, program_name, statements = ast
    code = []
    label_counter = [0]

    for stmt in statements:
        generate_statement(stmt, code, label_counter)

    code.append("HALT")
    return code


def new_label(label_counter):
    label = f"L{label_counter[0]}"
    label_counter[0] += 1
    return label


def generate_statement(stmt, code, label_counter):
    kind = stmt[0]

    if kind == 'declare':
        _, var_type, ids = stmt
        for var in ids:
            code.append(f"DECL {var}")

    elif kind == 'assign':
        _, var, expr = stmt
        generate_expression(expr, code)
        code.append(f"STORE {var}")

    elif kind == 'print':
        _, items = stmt
        for item in items:
            if isinstance(item, tuple) and item[0] == 'string':
                code.append(f'PRINTSTR "{item[1]}"')
            else:
                generate_expression(item, code)
                code.append("PRINT")

    elif kind == 'read':
        _, ids = stmt
        for var in ids:
            code.append(f"READ {var}")

    elif kind == 'if':
        _, cond, then_statements, else_statements = stmt

        if else_statements is None:
            end_label = new_label(label_counter)

            generate_condition(cond, code)
            code.append(f"JZ {end_label}")

            for inner_stmt in then_statements:
                generate_statement(inner_stmt, code, label_counter)

            code.append(f"LABEL {end_label}")

        else:
            else_label = new_label(label_counter)
            end_label = new_label(label_counter)

            generate_condition(cond, code)
            code.append(f"JZ {else_label}")

            for inner_stmt in then_statements:
                generate_statement(inner_stmt, code, label_counter)

            code.append(f"JMP {end_label}")
            code.append(f"LABEL {else_label}")

            for inner_stmt in else_statements:
                generate_statement(inner_stmt, code, label_counter)

            code.append(f"LABEL {end_label}")

    elif kind == 'do':
        _, label, var, start_expr, end_expr, body_statements = stmt
        start_label = new_label(label_counter)
        end_label = new_label(label_counter)

        generate_expression(start_expr, code)
        code.append(f"STORE {var}")

        code.append(f"LABEL {start_label}")
        code.append(f"LOAD {var}")
        generate_expression(end_expr, code)
        code.append("CMPLE")
        code.append(f"JZ {end_label}")

        for inner_stmt in body_statements:
            generate_statement(inner_stmt, code, label_counter)

        code.append(f"LOAD {var}")
        code.append("PUSH 1")
        code.append("ADD")
        code.append(f"STORE {var}")
        code.append(f"JMP {start_label}")
        code.append(f"LABEL {end_label}")

    elif kind == 'continue':
        _, label = stmt
        code.append(f"LABEL {label}")

def generate_expression(expr, code):
    kind = expr[0]

    if kind == 'number':
        code.append(f"PUSH {expr[1]}")

    elif kind == 'bool':
        value = 1 if expr[1] else 0
        code.append(f"PUSH {value}")

    elif kind == 'id':
        code.append(f"LOAD {expr[1]}")

    elif kind == 'binop':
        _, op, left, right = expr
        generate_expression(left, code)
        generate_expression(right, code)

        if op == '+':
            code.append("ADD")
        elif op == '-':
            code.append("SUB")
        elif op == '*':
            code.append("MUL")
        elif op == '/':
            code.append("DIV")


def generate_condition(cond, code):
    kind = cond[0]

    if kind in ('number', 'bool', 'id', 'binop'):
        generate_expression(cond, code)

    elif kind == 'relop':
        _, op, left, right = cond
        generate_expression(left, code)
        generate_expression(right, code)

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
        generate_condition(left, code)
        generate_condition(right, code)

        if op == '.AND.':
            code.append("AND")
        elif op == '.OR.':
            code.append("OR")

    elif kind == 'not':
        generate_condition(cond[1], code)
        code.append("NOT")
