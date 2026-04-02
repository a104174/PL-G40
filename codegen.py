def generate_program(ast):
    if ast[0] != 'program':
        raise Exception("AST inválida")

    _, program_name, statements = ast
    code = []

    for stmt in statements:
        generate_statement(stmt, code)

    code.append("HALT")
    return code


def generate_statement(stmt, code):
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