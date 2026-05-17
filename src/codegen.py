"""Geração de código EWVM a partir da AST validada.

O backend percorre a AST e emite uma lista de instruções EWVM. Antes de gerar
código, confirma se o programa pertence ao subconjunto implementado para a
EWVM; construções fora desse subconjunto são rejeitadas explicitamente.

O sufixo `phase1` ficou do desenvolvimento incremental do backend. Atualmente
estas funções constituem o backend principal do compilador.
"""

SUPPORTED_EWVM_PHASE1_TYPES = {'INTEGER', 'REAL', 'LOGICAL'}


def normalize_program(ast):
    """Extrai `(nome, statements, subprogramas)` de uma AST de programa."""
    if ast[0] != 'program':
        raise Exception("AST inválida")

    if len(ast) == 4:
        _, program_name, statements, function_nodes = ast
    else:
        _, program_name, statements = ast
        function_nodes = []

    return program_name, statements, function_nodes


def generate_program(ast):
    """Gera código EWVM para um programa suportado.

    Esta é a entrada pública do backend. O teste de suporte é feito antes da
    geração para evitar produzir código parcial ou instruções que a EWVM não
    conhece.
    """
    if not supports_ewvm_phase1(ast):
        raise NotImplementedError("Geração EWVM não suportada para este programa")

    return generate_program_ewvm_phase1(ast)


def build_global_layout(statements):
    """Constrói o layout de memória global.

    Cada variável global recebe um offset fixo. Escalares ocupam uma posição;
    arrays ocupam um bloco contíguo com o tamanho declarado.
    """
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
    """Itera símbolos pela ordem do offset de memória."""
    return sorted(layout.items(), key=lambda item: item[1]['offset'])


def supports_ewvm_phase1(ast):
    """Verifica se todo o programa é gerável pelo backend EWVM atual."""
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
    """Verifica se um statement é suportado no layout dado.

    Esta função é conservadora: se houver dúvida sobre uma construção, devolve
    `False` para que o compilador rejeite o programa em vez de gerar EWVM
    inválida.
    """
    kind = stmt[0]

    if kind == 'label':
        if not isinstance(stmt[1], int):
            return False
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
        return isinstance(stmt[1], int)

    if kind == 'call':
        return False

    if kind == 'continue':
        return True

    if kind == 'do':
        _, _, var, start_expr, end_expr, body_statements = stmt
        if not isinstance(stmt[1], int):
            return False

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
    """Verifica se uma expressão pode ser traduzida para EWVM."""
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

    if kind == 'uminus':
        return (
            expression_supported_ewvm_phase1(expr[1], layout, functions)
            and infer_expression_type_ewvm_phase1(expr[1], layout, functions) != 'LOGICAL'
        )

    return False


def array_access_supported_ewvm_phase1(expr, layout, functions):
    """Confirma se um acesso indexado representa um array global suportado."""
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
    """Confirma se uma expressão `NOME(...)` é uma chamada de função suportada."""
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
    """Verifica se uma condição pode ser emitida como valor lógico EWVM."""
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
    """Indica se o backend consegue converter `expr_type` para `target_type`."""
    if target_type == expr_type:
        return True

    if target_type == 'REAL' and expr_type == 'INTEGER':
        return True

    return False


def emit_ewvm_type_conversion(source_type, target_type, code):
    """Emite conversão implícita entre tipos EWVM, quando existe.

    O backend só implementa `INTEGER -> REAL`, traduzido pela instrução `ITOF`.
    Qualquer outra conversão deve ter sido rejeitada antes pela semântica ou
    pelo teste de suporte.
    """
    if source_type == target_type:
        return

    if target_type == 'REAL' and source_type == 'INTEGER':
        code.append("ITOF")
        return

    raise NotImplementedError(f"Conversão EWVM não suportada: {source_type} -> {target_type}")


def ewvm_string(value):
    """Escapa uma string para o formato aceite pela instrução `PUSHS`."""
    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"'


def get_global_info(layout, name):
    """Obtém informação de um símbolo no layout atual ou falha explicitamente."""
    info = layout.get(name)
    if info is None:
        raise Exception(f"Símbolo '{name}' não encontrado no layout EWVM")

    return info


def is_scalar_symbol(layout, name):
    """Indica se o nome existe no layout e representa um escalar."""
    info = layout.get(name)
    return info is not None and info['kind'] == 'scalar'


def is_array_symbol(layout, name):
    """Indica se o nome existe no layout e representa um array."""
    info = layout.get(name)
    return info is not None and info['kind'] == 'array'


def collect_functions_ewvm(function_nodes):
    """Constrói metadados necessários para gerar funções EWVM.

    Apenas `FUNCTION` é suportado. Subrotinas fazem a função devolver `None`,
    sinalizando ao chamador que o programa deve ser rejeitado. Para cada função
    é criado um layout local com símbolo de retorno, variáveis locais e
    parâmetros.
    """
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

        # Devolve um dicionário com uma entrada por função, no formato:
        functions[name] = {
            'label': f"FUNC{name}",         # FUNC[nome função]
            'return_type': return_type,     # 'INTEGER', 'REAL' ou 'LOGICAL'
            'param_names': param_names,     # nomes dos parâmetros formais, por ordem
            'param_types': param_types,     # tipos correspondentes
            'layout': local_layout,         # símbolo -> info (offset, storage, type)
            'body': body_statements,        # statements do AST
            'local_slots': local_offset,    # número de slots locais reservados
        }
        # Devolve 'None' se algum subprograma não for suportado.
    return functions


def infer_expression_type_ewvm_phase1(expr, layout, functions=None):
    """Infere o tipo EWVM de uma expressão já validada semanticamente.
    
    Ao contrário de 'generate_expression_ewvm_phase_1', esta função não emite
    instruções, apenas calcula o tipo que a expressão produziria. É usada
    antes da 'generate' para decidir se é necessário emitir `ITOF` e para
    escolher entre instruções inteiras e reais (por exemplo, `ADD` vs `FADD`).
    """
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


    if kind == 'uminus':
        return infer_expression_type_ewvm_phase1(expr[1], layout, functions)


    raise NotImplementedError(f"Expressão não suportada na fase EWVM 1: {kind}")


def emit_global_initialization_ewvm_phase1(code, layout):
    """Reserva e inicializa a memória global antes de `START`.

    A EWVM usa os valores empilhados antes de `START` como espaço global. Arrays
    de inteiros/lógicos podem usar `PUSHN`; arrays reais são inicializados
    posição a posição para garantir o tipo correto.
    """
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
    """Emite uma label EWVM."""
    code.append(f"{label}:")


def emit_global_address_ewvm_phase1(info, code):
    """Emite o endereço base de um símbolo global.

    Arrays são manipulados por endereço com `PUSHGP`, offset e operações
    indiretas como `LOADN` e `STOREN`.
    """
    code.append("PUSHGP")
    if info['offset'] != 0:
        code.append(f"PUSHI {info['offset']}")
        code.append("PADD")


def generate_array_index_ewvm_phase1(index_expr, code, layout, functions):
    """Gera o índice usado para acesso a array.

    O Fortran usado nos exemplos indexa arrays a partir de 1. A EWVM usa offsets
    a partir de 0, por isso o gerador subtrai 1 ao índice calculado.
    """
    index_type = generate_expression_ewvm_phase1(index_expr, code, layout, functions)

    if index_type != 'INTEGER':
        raise NotImplementedError("Índice de array EWVM deve ser INTEGER")

    code.append("PUSHI 1")
    code.append("SUB")


def emit_scalar_load_ewvm_phase1(info, code):
    """Emite código para carregar um escalar para a stack de operandos."""
    if info.get('storage') == 'global':
        code.append(f"PUSHG {info['offset']}")
        return

    if info.get('storage') == 'param':
        code.append("PUSHFP")
        code.append(f"LOAD {info['offset']}")
        return

    code.append(f"PUSHL {info['offset']}")


def emit_scalar_store_ewvm_phase1(info, code):
    """Emite código para guardar o topo da stack num escalar."""
    if info.get('storage') == 'global':
        code.append(f"STOREG {info['offset']}")
        return

    code.append(f"STOREL {info['offset']}")


def emit_slot_initialization_ewvm_phase1(info, code):
    """Emite o valor inicial de uma variável local."""
    if info['type'] == 'REAL':
        code.append("PUSHF 0.0")
    else:
        code.append("PUSHI 0")


def has_explicit_return(statements):
    """Indica se uma função contém pelo menos um `RETURN` explícito."""
    for stmt in statements:
        kind = stmt[0]
        if kind == 'return':
            return True

        if kind == 'label' and has_explicit_return([stmt[2]]):
            return True

    return False


def generate_expression_ewvm_phase1(expr, code, layout, functions):
    """Gera EWVM para uma expressão e devolve o seu tipo.

    A função deixa o valor calculado no topo da stack de operandos. Chamadas de
    função, acessos a arrays e conversões implícitas são tratados aqui porque
    todos aparecem no nível de expressão.
    """
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

            # A EWVM espera que uma chamada deixe espaço para o valor de retorno.
            # Funções sem argumentos precisam desse espaço criado explicitamente.
            if len(arg_exprs) == 0:
                code.append("PUSHN 1")

            for arg_expr, param_type in zip(arg_exprs, param_types):
                arg_type = generate_expression_ewvm_phase1(arg_expr, code, layout, functions)
                emit_ewvm_type_conversion(arg_type, param_type, code)

            code.append(f"PUSHA {function_info['label']}")
            code.append("CALL")

            # Após o CALL, a stack contém: [ret] [arg1] [arg2] ... [argN]
            # O valor de retorno fica na posição mais funda; os argumentos ficam
            # por cima. Para cada argumento extra (a partir do segundo), faz-se
            # SWAP + POP 1 para o descartar sem perder o valor de retorno.
            # Com 0 ou 1 argumento não há nada a remover.
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
        result_type = infer_expression_type_ewvm_phase1(expr, layout, functions)

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
        result_type = infer_expression_type_ewvm_phase1(expr, layout, functions)

        generate_expression_ewvm_phase1(left, code, layout, functions)
        generate_expression_ewvm_phase1(right, code, layout, functions)
        code.append("MOD")
        return result_type

    if kind == 'uminus':
        expr_type = generate_expression_ewvm_phase1(expr[1], code, layout, functions)
        if expr_type == 'REAL':
            code.append("PUSHF -1.0")
            code.append("FMUL")
        else:
            code.append("PUSHI -1")
            code.append("MUL")
        return expr_type

    raise NotImplementedError(f"Expressão não suportada na fase EWVM 1: {kind}")


def generate_condition_ewvm_phase1(cond, code, layout, functions):
    """Gera EWVM para uma condição.

    O resultado fica na stack como valor lógico inteiro (`0` para falso, `1`
    para verdadeiro), que pode ser consumido por `JZ` ou por operadores lógicos.
    """
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
    """Gera EWVM para um statement.

    `layout` representa o espaço de símbolos visível no contexto atual. No
    programa principal é o layout global; dentro de funções é o layout local da
    função. `current_function` permite qualificar labels e tratar `RETURN`.
    """
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
    """Emite o corpo EWVM de uma função.

    Funções são colocadas depois do `STOP` do programa principal. As variáveis
    locais são inicializadas no início da função. Se o corpo não tiver `RETURN`,
    o valor da variável com o mesmo nome da função é devolvido no fim.
    """
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
    """Gera a lista completa de instruções EWVM para um programa."""
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


def new_label(label_counter):
    """Cria uma label interna única do tipo `L0`, `L1`, ..."""
    label = f"L{label_counter[0]}"
    label_counter[0] += 1
    return label


def user_label(label, current_function=None):
    """Converte uma label Fortran para uma label EWVM válida.

    Labels dentro de funções recebem o nome da função como prefixo para evitar
    colisões com labels iguais no programa principal.
    """
    if current_function is None:
        return f"LBL{label}"

    return f"{current_function}LBL{label}"


def get_decl_info(item):
    """Normaliza um item de declaração do parser para uso no codegen."""
    if isinstance(item, tuple):
        if item[0] == 'scalar':
            return 'scalar', item[1], None
        if item[0] == 'array':
            return 'array', item[1], item[2]

    return 'scalar', item, None
