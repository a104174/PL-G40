import ply.lex as lex

reserved = {
    'PROGRAM': 'PROGRAM',
    'INTEGER': 'INTEGER',
    'REAL': 'REAL',
    'LOGICAL': 'LOGICAL',
    'IF': 'IF',
    'THEN': 'THEN',
    'ELSE': 'ELSE',
    'ENDIF': 'ENDIF',
    'DO': 'DO',
    'CONTINUE': 'CONTINUE',
    'GOTO': 'GOTO',
    'FUNCTION': 'FUNCTION',
    'RETURN': 'RETURN',
    'READ': 'READ',
    'PRINT': 'PRINT',
    'END': 'END',
}

tokens = [
    'ID',
    'NUMBER',
    'STRING',

    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'ASSIGN',

    'LPAREN',
    'RPAREN',
    'COMMA',

    'DOT_EQ',
    'DOT_NE',
    'DOT_LT',
    'DOT_LE',
    'DOT_GT',
    'DOT_GE',
    'DOT_AND',
    'DOT_OR',
    'DOT_NOT',

    'DOT_TRUE',
    'DOT_FALSE',
] + list(reserved.values())

t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_ASSIGN = r'='

t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COMMA = r','

t_DOT_EQ = r'\.EQ\.'
t_DOT_NE = r'\.NE\.'
t_DOT_LT = r'\.LT\.'
t_DOT_LE = r'\.LE\.'
t_DOT_GT = r'\.GT\.'
t_DOT_GE = r'\.GE\.'
t_DOT_AND = r'\.AND\.'
t_DOT_OR = r'\.OR\.'
t_DOT_NOT = r'\.NOT\.'

t_DOT_TRUE = r'\.TRUE\.'
t_DOT_FALSE = r'\.FALSE\.'

t_ignore = ' \t'




def t_NUMBER(t):
    r'\d+(\.\d+)?'
    if '.' in t.value:
        t.value = float(t.value)
    else:
        t.value = int(t.value)
    return t


def t_STRING(t):
    r"\'([^\\\n]|(\\.))*?\'"
    t.value = t.value[1:-1]
    return t


def t_ID(t):
    r'[A-Za-z][A-Za-z0-9_]*'
    upper_value = t.value.upper()
    t.type = reserved.get(upper_value, 'ID')
    t.value = upper_value
    return t


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


def t_comment(t):
    r'!.*'
    pass


def t_error(t):
    print(f"Carácter ilegal: {t.value[0]!r} na linha {t.lineno}")
    t.lexer.skip(1)


lexer = lex.lex()
