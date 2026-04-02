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

def p_statement_read(p):
    'statement : read_stmt'
    p[0] = p[1]

def p_statement_if(p):
    'statement : if_stmt'
    p[0] = p[1]

def p_statement_do(p):
    'statement : do_stmt'
    p[0] = p[1]

def p_statement_labeled_continue(p):
    'statement : labeled_continue'
    p[0] = p[1]

def p_statement_goto(p):
    'statement : goto_stmt'
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

def p_read_stmt(p):
    'read_stmt : READ TIMES COMMA id_list'
    p[0] = ('read', p[4])

def p_if_stmt(p):
    '''
    if_stmt : IF LPAREN condition RPAREN THEN statements ENDIF
            | IF LPAREN condition RPAREN THEN statements ELSE statements ENDIF
    '''
    if len(p) == 8:
        p[0] = ('if', p[3], p[6], None)
    else:
        p[0] = ('if', p[3], p[6], p[8])

def p_do_stmt(p):
    'do_stmt : DO NUMBER ID ASSIGN expression COMMA expression do_body_statements labeled_continue'
    if p[2] != p[9][1]:
        raise SyntaxError(f"Label do DO ({p[2]}) diferente do label do CONTINUE ({p[9][1]})")
    p[0] = ('do', p[2], p[3], p[5], p[7], p[8])

def p_labeled_continue(p):
    'labeled_continue : NUMBER CONTINUE'
    p[0] = ('continue', p[1])

def p_goto_stmt(p):
    'goto_stmt : GOTO NUMBER'
    p[0] = ('goto', p[2])

def p_do_body_statements_multiple(p):
    'do_body_statements : do_body_statements do_body_statement'
    p[0] = p[1] + [p[2]]

def p_do_body_statements_single(p):
    'do_body_statements : do_body_statement'
    p[0] = [p[1]]

def p_do_body_statement(p):
    '''
    do_body_statement : declaration
                      | assignment
                      | print_stmt
                      | read_stmt
                      | if_stmt
                      | do_stmt
                      | goto_stmt
    '''
    p[0] = p[1]

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

# Condições
def p_condition_relop(p):
    '''
    condition : expression DOT_EQ expression
              | expression DOT_NE expression
              | expression DOT_LT expression
              | expression DOT_LE expression
              | expression DOT_GT expression
              | expression DOT_GE expression
    '''
    p[0] = ('relop', p[2], p[1], p[3])

def p_condition_binop(p):
    '''
    condition : condition DOT_AND condition
              | condition DOT_OR condition
    '''
    p[0] = ('logicop', p[2], p[1], p[3])

def p_condition_not(p):
    'condition : DOT_NOT condition %prec DOT_NOT'
    p[0] = ('not', p[2])

def p_condition_group(p):
    'condition : LPAREN condition RPAREN'
    p[0] = p[2]

def p_condition_expression(p):
    'condition : expression %prec COND_EXPR'
    p[0] = p[1]

# Precedência dos operadores
precedence = (
    ('nonassoc', 'COND_EXPR'),
    ('left', 'DOT_OR'),
    ('left', 'DOT_AND'),
    ('right', 'DOT_NOT'),
    ('nonassoc', 'DOT_EQ', 'DOT_NE', 'DOT_LT', 'DOT_LE', 'DOT_GT', 'DOT_GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
)

def p_error(p):
    if p:
        print(f"Erro sintático no token {p.type} com valor {p.value}")
    else:
        print("Erro sintático no fim do ficheiro")

parser = yacc.yacc()
