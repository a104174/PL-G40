from src.lexer import lexer

code = """
PROGRAM HELLO
INTEGER N
N = 5
PRINT *, N
END
"""

lexer.input(code)

for tok in lexer:
    print(tok)
