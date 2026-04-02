def check_program(ast):
    if ast[0] != 'program':
        raise Exception("AST inválida")

    _, program_name, statements = ast
    symbols = {}
    errors = []
    reported = set()

    for stmt in statements:
        check_statement(stmt, symbols, errors, reported)

    return symbols, errors


def add_error(msg, errors, reported):
    if msg not in reported:
        errors.append(msg)
        reported.add(msg)


def check_statement(stmt, symbols, errors, reported):
    kind = stmt[0]

    if kind == 'declare':
        _, var_type, ids = stmt
        for var in ids:
            if var in symbols:
                add_error(f"Variável '{var}' declarada mais do que uma vez", errors, reported)
            else:
                symbols[var] = var_type

    elif kind == 'assign':
        _, var, expr = stmt

        if var not in symbols:
            add_error(f"Variável '{var}' usada sem declaração", errors, reported)
            check_expression(expr, symbols, errors, reported)
            return

        expr_type = infer_type(expr, symbols, errors, reported)
        var_type = symbols[var]

        if expr_type is not None and not compatible_types(var_type, expr_type):
            add_error(
                f"Incompatibilidade de tipos na atribuição a '{var}': {var_type} <- {expr_type}",
                errors,
                reported
            )

    elif kind == 'print':
        _, items = stmt
        for item in items:
            if isinstance(item, tuple) and item[0] != 'string':
                check_expression(item, symbols, errors, reported)


def check_expression(expr, symbols, errors, reported):
    kind = expr[0]

    if kind in ('number', 'bool'):
        return

    if kind == 'id':
        var = expr[1]
        if var not in symbols:
            add_error(f"Variável '{var}' usada sem declaração", errors, reported)

    elif kind == 'binop':
        _, op, left, right = expr
        check_expression(left, symbols, errors, reported)
        check_expression(right, symbols, errors, reported)


def infer_type(expr, symbols, errors, reported):
    kind = expr[0]

    if kind == 'number':
        value = expr[1]
        if isinstance(value, int):
            return 'INTEGER'
        elif isinstance(value, float):
            return 'REAL'

    if kind == 'bool':
        return 'LOGICAL'

    if kind == 'id':
        var = expr[1]
        if var not in symbols:
            add_error(f"Variável '{var}' usada sem declaração", errors, reported)
            return None
        return symbols[var]

    if kind == 'binop':
        _, op, left, right = expr

        left_type = infer_type(left, symbols, errors, reported)
        right_type = infer_type(right, symbols, errors, reported)

        if left_type is None or right_type is None:
            return None

        if left_type == 'LOGICAL' or right_type == 'LOGICAL':
            add_error(
                f"Operação aritmética inválida com tipos {left_type} e {right_type}",
                errors,
                reported
            )
            return None

        if left_type == 'REAL' or right_type == 'REAL':
            return 'REAL'
        return 'INTEGER'

    return None


def compatible_types(var_type, expr_type):
    if var_type == expr_type:
        return True

    # REAL pode receber INTEGER
    if var_type == 'REAL' and expr_type == 'INTEGER':
        return True

    return False