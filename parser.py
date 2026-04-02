import ply.yacc as yacc
from lexer import tokens

# Programa completo
def p_program(p):
    'program : PROGRAM ID statements END'
    p[0] = ('program', p[2], p[3])

# Lista de statements
def p_statements_multiple(p):
    'statements : statements statement'
    p[0] = p[1] + [p[2]]

def p_statements_single(p):
    'statements : statement'
    p[0] = [p[1]]

# Tipos de statement
def p_statement_decl(p):
    'statement : declaration'
    p[0] = p[1]

def p_statement_assign(p):
    'statement : assignment'
    p[0] = p[1]

def p_statement_print(p):
    'statement : print_stmt'
    p[0] = p[1]

# Declarações
def p_declaration_integer(p):
    'declaration : INTEGER id_list'
    p[0] = ('declare', 'INTEGER', p[2])

def p_declaration_real(p):
    'declaration : REAL id_list'
    p[0] = ('declare', 'REAL', p[2])

def p_declaration_logical(p):
    'declaration : LOGICAL id_list'
    p[0] = ('declare', 'LOGICAL', p[2])

# Lista de identificadores
def p_id_list_multiple(p):
    'id_list : id_list COMMA ID'
    p[0] = p[1] + [p[3]]

def p_id_list_single(p):
    'id_list : ID'
    p[0] = [p[1]]

# Atribuição
def p_assignment(p):
    'assignment : ID ASSIGN expression'
    p[0] = ('assign', p[1], p[3])

# PRINT *, ...
def p_print_stmt(p):
    'print_stmt : PRINT TIMES COMMA print_list'
    p[0] = ('print', p[4])

# Lista de coisas a imprimir
def p_print_list_multiple(p):
    'print_list : print_list COMMA printable'
    p[0] = p[1] + [p[3]]

def p_print_list_single(p):
    'print_list : printable'
    p[0] = [p[1]]

def p_printable_expr(p):
    'printable : expression'
    p[0] = p[1]

def p_printable_string(p):
    'printable : STRING'
    p[0] = ('string', p[1])

# Expressões
def p_expression_binop(p):
    '''
    expression : expression PLUS expression
               | expression MINUS expression
               | expression TIMES expression
               | expression DIVIDE expression
    '''
    p[0] = ('binop', p[2], p[1], p[3])

def p_expression_group(p):
    'expression : LPAREN expression RPAREN'
    p[0] = p[2]

def p_expression_number(p):
    'expression : NUMBER'
    p[0] = ('number', p[1])

def p_expression_id(p):
    'expression : ID'
    p[0] = ('id', p[1])

def p_expression_true(p):
    'expression : DOT_TRUE'
    p[0] = ('bool', True)

def p_expression_false(p):
    'expression : DOT_FALSE'
    p[0] = ('bool', False)

# Precedência dos operadores
precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
)

def p_error(p):
    if p:
        print(f"Erro sintático no token {p.type} com valor {p.value}")
    else:
        print("Erro sintático no fim do ficheiro")

parser = yacc.yacc()