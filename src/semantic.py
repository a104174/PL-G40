"""Análise semântica da AST.

Esta fase valida propriedades que a gramática não consegue garantir sozinha:
declaração de variáveis, compatibilidade de tipos, uso correto de arrays,
existência de labels, coerência de chamadas a funções/subrotinas e validade de
`RETURN`.

As funções deste módulo acumulam erros em vez de parar no primeiro problema.
Isso permite devolver ao utilizador uma lista mais útil de correções a fazer.
"""


def check_program(ast):
    """Valida semanticamente um programa completo.

    Recebe a AST produzida pelo parser, recolhe labels e subprogramas, valida
    funções/subrotinas e por fim percorre o corpo principal. Devolve a tabela de
    símbolos globais e a lista de erros encontrados.
    """
    if ast[0] != 'program':
        raise Exception("AST inválida")

    if len(ast) == 4:
        _, program_name, statements, function_nodes = ast
    else:
        _, program_name, statements = ast
        function_nodes = []

    symbols = {}
    errors = []
    reported = set()
    labels = collect_labels(statements, errors=errors, reported=reported)
    functions = collect_functions(function_nodes, errors, reported)

    for function_node in function_nodes:
        check_function(function_node, functions, errors, reported)

    for stmt in statements:
        check_statement(stmt, symbols, functions, errors, reported, labels, None)

    return symbols, errors


def add_error(msg, errors, reported):
    """Adiciona um erro apenas uma vez.

    A mesma inconsistência pode ser descoberta por mais de uma verificação
    recursiva. O conjunto `reported` evita mensagens duplicadas.
    """
    if msg not in reported:
        errors.append(msg)
        reported.add(msg)


def get_symbol_info(name, symbols):
    """Obtém informação normalizada de um símbolo.

    Versões antigas da tabela podiam guardar apenas a string do tipo. Esta
    função uniformiza o acesso, devolvendo sempre um dicionário com `kind` e
    `type` quando o símbolo existe.
    """
    info = symbols.get(name)

    if info is None:
        return None

    if isinstance(info, str):
        return {'kind': 'scalar', 'type': info}

    return info


def get_decl_info(item, var_type):
    """Converte um item de declaração num par `(nome, info)`.

    O parser representa escalares e arrays de forma diferente. A análise
    semântica usa esta função para obter uma entrada pronta a colocar na tabela
    de símbolos.
    """
    if isinstance(item, tuple):
        if item[0] == 'scalar':
            return item[1], {'kind': 'scalar', 'type': var_type}
        if item[0] == 'array':
            return item[1], {'kind': 'array', 'type': var_type, 'size': item[2]}

    return item, {'kind': 'scalar', 'type': var_type}


def collect_functions(function_nodes, errors, reported):
    """Recolhe assinaturas de funções e subrotinas.

    Nesta primeira passagem só são registados nome, espécie, parâmetros e corpo.
    Os tipos dos parâmetros são preenchidos depois, quando as declarações locais
    do subprograma forem analisadas.
    """
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

        if name in functions:
            add_error(f"Subprograma '{name}' declarado mais do que uma vez", errors, reported)
            continue

        functions[name] = {
            'kind': kind,
            'return_type': return_type,
            'param_names': param_names,
            'param_types': [None] * len(param_names),
            'body': body_statements,
        }

    return functions


def find_parameter_types(function_name, param_names, body_statements, errors, reported):
    """Determina os tipos dos parâmetros formais de um subprograma.

    No subconjunto suportado, os parâmetros aparecem na lista da função e os seus
    tipos são declarados no corpo. Esta função cruza essas duas fontes e reporta
    parâmetros não declarados ou declarados como arrays.
    """
    param_types = {param_name: None for param_name in param_names}

    for stmt in body_statements:
        if stmt[0] == 'label':
            stmt = stmt[2]

        if stmt[0] != 'declare':
            continue

        _, var_type, items = stmt
        for item in items:
            name, info = get_decl_info(item, var_type)
            if name not in param_types:
                continue

            if info['kind'] != 'scalar':
                add_error(
                    f"Parâmetro '{name}' da função '{function_name}' deve ser escalar",
                    errors,
                    reported
                )
                param_types[name] = None
                continue

            if param_types[name] is None:
                param_types[name] = info['type']

    for param_name in param_names:
        if param_types[param_name] is None:
            add_error(
                f"Parâmetro '{param_name}' da função '{function_name}' deve ser declarado",
                errors,
                reported
            )

    return [param_types[param_name] for param_name in param_names]


def check_function(function_node, functions, errors, reported):
    """Valida o corpo de uma função ou subrotina.

    Cria uma tabela de símbolos local, acrescenta o símbolo de retorno quando o
    subprograma é uma função e valida todos os statements no contexto local.
    """
    kind = function_node[0]

    if kind == 'function':
        _, return_type, name, param_names, body_statements = function_node
    else:
        _, name, param_names, body_statements = function_node
        return_type = None

    if name not in functions:
        return

    if functions[name]['body'] is not body_statements:
        return

    seen_params = set()
    for param_name in param_names:
        if param_name == name:
            add_error(
                f"Parâmetro '{param_name}' da função '{name}' não pode ter o mesmo nome da função",
                errors,
                reported
            )

        if param_name in seen_params:
            add_error(
                f"Parâmetro '{param_name}' da função '{name}' declarado mais do que uma vez",
                errors,
                reported
            )
            continue

        seen_params.add(param_name)

    param_types = find_parameter_types(name, param_names, body_statements, errors, reported)
    functions[name]['param_types'] = param_types

    local_symbols = {}
    if kind == 'function':
        local_symbols[name] = {'kind': 'scalar', 'type': return_type}
    local_labels = collect_labels(body_statements, errors=errors, reported=reported)

    for stmt in body_statements:
        check_statement(stmt, local_symbols, functions, errors, reported, local_labels, name)


def format_label(label):
    """Converte labels para texto em mensagens de erro."""
    return str(label)


def is_integer_label(label):
    """Indica se um valor é uma label inteira válida."""
    return isinstance(label, int) and not isinstance(label, bool)


def add_label(label, labels, errors, reported, context):
    """Regista uma label, validando tipo e duplicação."""
    if not is_integer_label(label):
        if errors is not None:
            add_error(f"Label '{format_label(label)}' em {context} deve ser inteiro", errors, reported)
        return

    if label in labels:
        if errors is not None:
            add_error(f"Label '{format_label(label)}' declarado mais do que uma vez", errors, reported)
        return

    labels.add(label)


def collect_labels(statements, labels=None, errors=None, reported=None):
    """Recolhe todas as labels visíveis numa lista de statements.

    A recolha é recursiva porque labels podem aparecer dentro de `IF` e `DO`.
    Também são registadas as labels finais de ciclos `DO`, usadas por `GOTO` e
    pela geração de código.
    """
    if labels is None:
        labels = set()

    for stmt in statements:
        kind = stmt[0]

        if kind == 'label':
            inner_context = 'CONTINUE' if stmt[2][0] == 'continue' else 'statement'
            add_label(stmt[1], labels, errors, reported, inner_context)
            collect_labels([stmt[2]], labels, errors, reported)

        elif kind == 'do':
            add_label(stmt[1], labels, errors, reported, 'DO')
            collect_labels(stmt[5], labels, errors, reported)

        elif kind == 'if':
            collect_labels(stmt[2], labels, errors, reported)
            if stmt[3] is not None:
                collect_labels(stmt[3], labels, errors, reported)

    return labels


def check_call(name, arg_exprs, symbols, functions, errors, reported):
    """Valida uma chamada de função usada como expressão.

    Confirma que o nome existe, que representa uma função e que o número e tipos
    dos argumentos são compatíveis com a assinatura recolhida.
    """
    function_info = functions.get(name)

    if function_info is None:
        add_error(f"Função '{name}' usada sem declaração", errors, reported)
        for arg_expr in arg_exprs:
            infer_type(arg_expr, symbols, functions, errors, reported)
        return None

    if function_info.get('kind') != 'function':
        add_error(f"Subrotina '{name}' não pode ser usada numa expressão", errors, reported)
        for arg_expr in arg_exprs:
            infer_type(arg_expr, symbols, functions, errors, reported)
        return None

    param_names = function_info.get('param_names', [])
    param_types = function_info.get('param_types', [])

    if len(arg_exprs) != len(param_names):
        add_error(
            f"Função '{name}' chamada com {len(arg_exprs)} argumentos, esperado {len(param_names)}",
            errors,
            reported
        )

    arg_types = [infer_type(arg_expr, symbols, functions, errors, reported) for arg_expr in arg_exprs]

    for param_type, arg_type in zip(param_types, arg_types):
        if param_type is not None and arg_type is not None and not compatible_types(param_type, arg_type):
            add_error(
                f"Incompatibilidade de tipos na chamada a '{name}': {param_type} <- {arg_type}",
                errors,
                reported
            )

    return function_info['return_type']


def check_subroutine_call(name, arg_exprs, symbols, functions, errors, reported):
    """Valida uma chamada feita através de `CALL`.

    `CALL` só pode invocar subrotinas. Funções chamadas com `CALL` e subrotinas
    usadas como expressões são erros semânticos distintos.
    """
    function_info = functions.get(name)

    if function_info is None:
        add_error(f"Subrotina '{name}' usada sem declaração", errors, reported)
        for arg_expr in arg_exprs:
            infer_type(arg_expr, symbols, functions, errors, reported)
        return

    if function_info.get('kind') != 'subroutine':
        add_error(f"Função '{name}' não pode ser usada com CALL", errors, reported)
        for arg_expr in arg_exprs:
            infer_type(arg_expr, symbols, functions, errors, reported)
        return

    param_names = function_info.get('param_names', [])
    param_types = function_info.get('param_types', [])

    if len(arg_exprs) != len(param_names):
        add_error(
            f"Subrotina '{name}' chamada com {len(arg_exprs)} argumentos, esperado {len(param_names)}",
            errors,
            reported
        )

    arg_types = [infer_type(arg_expr, symbols, functions, errors, reported) for arg_expr in arg_exprs]

    for param_type, arg_type in zip(param_types, arg_types):
        if param_type is not None and arg_type is not None and not compatible_types(param_type, arg_type):
            add_error(
                f"Incompatibilidade de tipos na chamada a '{name}': {param_type} <- {arg_type}",
                errors,
                reported
            )


def check_array_access(expr, symbols, functions, errors, reported):
    """Valida o acesso a uma posição de array e devolve o tipo do elemento."""
    _, name, index_expr = expr
    info = get_symbol_info(name, symbols)

    if info is None:
        add_error(f"Variável '{name}' usada sem declaração", errors, reported)
        infer_type(index_expr, symbols, functions, errors, reported)
        return None

    if info['kind'] != 'array':
        add_error(f"Variável escalar '{name}' não pode ser indexada", errors, reported)
        infer_type(index_expr, symbols, functions, errors, reported)
        return None

    index_type = infer_type(index_expr, symbols, functions, errors, reported)
    if index_type is not None and index_type != 'INTEGER':
        add_error(f"Índice do array '{name}' deve ser INTEGER", errors, reported)

    return info['type']


def infer_indexed_type(expr, symbols, functions, errors, reported):
    """Resolve expressões da forma `NOME(...)`.

    A mesma sintaxe pode significar chamada de função ou acesso a array. A
    decisão é feita consultando primeiro a tabela de subprogramas e depois a
    tabela de símbolos locais/globais.
    """
    _, name, arg_exprs = expr

    if name in functions:
        return check_call(name, arg_exprs, symbols, functions, errors, reported)

    if len(arg_exprs) != 1:
        if get_symbol_info(name, symbols) is None:
            add_error(f"Função '{name}' usada sem declaração", errors, reported)
        else:
            add_error(f"Identificador '{name}' não é uma função com {len(arg_exprs)} argumentos", errors, reported)

        for arg_expr in arg_exprs:
            infer_type(arg_expr, symbols, functions, errors, reported)
        return None

    if get_symbol_info(name, symbols) is None:
        add_error(f"Função '{name}' usada sem declaração", errors, reported)
        infer_type(arg_exprs[0], symbols, functions, errors, reported)
        return None

    return check_array_access(('array_access', name, arg_exprs[0]), symbols, functions, errors, reported)


def check_statement(stmt, symbols, functions, errors, reported, labels, in_function):
    """Valida semanticamente um statement.

    A função também atualiza a tabela de símbolos quando encontra declarações.
    `in_function` indica se a validação ocorre dentro de um subprograma, o que é
    necessário para decidir se `RETURN` é permitido.
    """
    kind = stmt[0]

    if kind == 'label':
        check_statement(stmt[2], symbols, functions, errors, reported, labels, in_function)

    elif kind == 'declare':
        _, var_type, ids = stmt
        for item in ids:
            name, info = get_decl_info(item, var_type)

            if name in symbols:
                add_error(f"Variável '{name}' declarada mais do que uma vez", errors, reported)
            else:
                symbols[name] = info

            if info['kind'] == 'array':
                size = info['size']
                if not isinstance(size, int) or size <= 0:
                    add_error(f"Tamanho do array '{name}' deve ser inteiro positivo", errors, reported)

    elif kind == 'assign':
        _, target, expr = stmt

        if isinstance(target, tuple) and target[0] == 'array_access':
            target_type = check_array_access(target, symbols, functions, errors, reported)
        else:
            info = get_symbol_info(target, symbols)

            if info is None:
                add_error(f"Variável '{target}' usada sem declaração", errors, reported)
                check_expression(expr, symbols, functions, errors, reported)
                return

            if info['kind'] != 'scalar':
                add_error(f"Array '{target}' usado sem índice na atribuição", errors, reported)
                check_expression(expr, symbols, functions, errors, reported)
                return

            target_type = info['type']

        expr_type = infer_type(expr, symbols, functions, errors, reported)

        if target_type is None:
            check_expression(expr, symbols, functions, errors, reported)
            return

        if expr_type is not None and not compatible_types(target_type, expr_type):
            add_error(
                f"Incompatibilidade de tipos na atribuição: {target_type} <- {expr_type}",
                errors,
                reported
            )

    elif kind == 'print':
        _, items = stmt
        for item in items:
            if isinstance(item, tuple) and item[0] != 'string':
                check_expression(item, symbols, functions, errors, reported)

    elif kind == 'read':
        _, ids = stmt
        for target in ids:
            if isinstance(target, tuple) and target[0] == 'array_access':
                check_array_access(target, symbols, functions, errors, reported)
            else:
                info = get_symbol_info(target, symbols)
                if info is None:
                    add_error(f"Variável '{target}' usada sem declaração", errors, reported)
                elif info['kind'] != 'scalar':
                    add_error(f"Array '{target}' usado sem índice no READ", errors, reported)

    elif kind == 'call':
        _, name, arg_exprs = stmt
        check_subroutine_call(name, arg_exprs, symbols, functions, errors, reported)

    elif kind == 'if':
        _, cond, then_statements, else_statements = stmt

        cond_type = infer_condition_type(cond, symbols, functions, errors, reported)
        if cond_type is not None and cond_type != 'LOGICAL':
            add_error("Condição do IF deve ser do tipo LOGICAL", errors, reported)

        for inner_stmt in then_statements:
            check_statement(inner_stmt, symbols, functions, errors, reported, labels, in_function)

        if else_statements is not None:
            for inner_stmt in else_statements:
                check_statement(inner_stmt, symbols, functions, errors, reported, labels, in_function)

    elif kind == 'do':
        _, label, var, start_expr, end_expr, body_statements = stmt

        info = get_symbol_info(var, symbols)

        if info is None:
            add_error(f"Variável de controlo '{var}' usada sem declaração", errors, reported)
        elif info['kind'] != 'scalar' or info['type'] == 'LOGICAL':
            add_error(f"Variável de controlo '{var}' do DO deve ser escalar numérica", errors, reported)

        start_type = infer_type(start_expr, symbols, functions, errors, reported)
        if start_type == 'LOGICAL':
            add_error("Expressão inicial do DO deve ser numérica", errors, reported)

        end_type = infer_type(end_expr, symbols, functions, errors, reported)
        if end_type == 'LOGICAL':
            add_error("Expressão final do DO deve ser numérica", errors, reported)

        for inner_stmt in body_statements:
            check_statement(inner_stmt, symbols, functions, errors, reported, labels, in_function)

    elif kind == 'continue':
        return

    elif kind == 'goto':
        _, label = stmt
        if not is_integer_label(label):
            add_error(f"Label '{format_label(label)}' em GOTO deve ser inteiro", errors, reported)
        elif label not in labels:
            add_error(f"Label '{label}' usado em GOTO não existe", errors, reported)

    elif kind == 'return':
        if in_function is None:
            add_error("RETURN usado fora de função", errors, reported)


def check_expression(expr, symbols, functions, errors, reported):
    """Percorre uma expressão apenas para provocar validações internas.

    Quando o tipo final não é necessário, esta função ainda garante que nomes,
    chamadas, acessos a arrays e subexpressões são verificados.
    """
    kind = expr[0]

    if kind in ('number', 'bool'):
        return

    if kind == 'id':
        infer_type(expr, symbols, functions, errors, reported)

    elif kind == 'indexed':
        infer_indexed_type(expr, symbols, functions, errors, reported)

    elif kind == 'binop':
        _, op, left, right = expr
        check_expression(left, symbols, functions, errors, reported)
        check_expression(right, symbols, functions, errors, reported)

    elif kind == 'mod':
        _, left, right = expr
        check_expression(left, symbols, functions, errors, reported)
        check_expression(right, symbols, functions, errors, reported)

    elif kind == 'uminus':
        infer_type(expr, symbols, functions, errors, reported)


def infer_type(expr, symbols, functions, errors, reported):
    """Infere o tipo de uma expressão.

    Devolve `INTEGER`, `REAL`, `LOGICAL` ou `None` quando algum erro impede a
    inferência. Durante a inferência também são reportados erros de uso de
    variáveis, arrays e operadores.
    """
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
        info = get_symbol_info(var, symbols)

        if info is None:
            add_error(f"Variável '{var}' usada sem declaração", errors, reported)
            return None

        if info['kind'] != 'scalar':
            add_error(f"Array '{var}' usado sem índice em expressão", errors, reported)
            return None

        return info['type']

    if kind == 'indexed':
        return infer_indexed_type(expr, symbols, functions, errors, reported)

    if kind == 'binop':
        _, op, left, right = expr

        left_type = infer_type(left, symbols, functions, errors, reported)
        right_type = infer_type(right, symbols, functions, errors, reported)

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

    if kind == 'mod':
        _, left, right = expr

        left_type = infer_type(left, symbols, functions, errors, reported)
        right_type = infer_type(right, symbols, functions, errors, reported)

        if left_type is None or right_type is None:
            return None

        if left_type != 'INTEGER' or right_type != 'INTEGER':
            add_error(
                f"Operação MOD inválida com tipos {left_type} e {right_type}",
                errors,
                reported
            )
            return None

        return 'INTEGER'

    if kind == 'uminus':
        operand_type = infer_type(expr[1], symbols, functions, errors, reported)

        if operand_type is None:
            return None

        if operand_type == 'LOGICAL':
            add_error("Operador unário '-' inválido sobre tipo LOGICAL", errors, reported)
            return None

        return operand_type

    return None


def infer_condition_type(cond, symbols, functions, errors, reported):
    """Infere e valida o tipo de uma condição.

    Relações e operadores lógicos devem resultar em `LOGICAL`. Expressões
    simples podem aparecer como condição, mas a validação do `IF` exige que o
    resultado final seja lógico.
    """
    kind = cond[0]

    if kind in ('number', 'bool', 'id', 'indexed', 'binop', 'uminus'):
        return infer_type(cond, symbols, functions, errors, reported)

    if kind == 'relop':
        _, op, left, right = cond

        left_type = infer_type(left, symbols, functions, errors, reported)
        right_type = infer_type(right, symbols, functions, errors, reported)

        if left_type is None or right_type is None:
            return None

        if left_type == 'LOGICAL' or right_type == 'LOGICAL':
            add_error(
                f"Comparação inválida com tipos {left_type} e {right_type}",
                errors,
                reported
            )
            return None

        return 'LOGICAL'

    if kind == 'logicop':
        _, op, left, right = cond

        left_type = infer_condition_type(left, symbols, functions, errors, reported)
        right_type = infer_condition_type(right, symbols, functions, errors, reported)

        if left_type != 'LOGICAL' or right_type != 'LOGICAL':
            add_error(
                f"Operação lógica inválida com tipos {left_type} e {right_type}",
                errors,
                reported
            )
            return None

        return 'LOGICAL'

    if kind == 'not':
        operand_type = infer_condition_type(cond[1], symbols, functions, errors, reported)

        if operand_type != 'LOGICAL':
            add_error(
                f"Operação lógica inválida: NOT sobre tipo {operand_type}",
                errors,
                reported
            )
            return None

        return 'LOGICAL'

    return None


def compatible_types(var_type, expr_type):
    """Indica se uma expressão pode ser atribuída a um destino.

    A única conversão implícita permitida é `INTEGER` para `REAL`, que preserva
    informação suficiente para este subconjunto.
    """
    if var_type == expr_type:
        return True

    if var_type == 'REAL' and expr_type == 'INTEGER':
        return True

    return False
