from src.parser import parser
from src.semantic import check_program

code = """
PROGRAM TEST
INTEGER N
REAL R
LOGICAL X

N = 5
R = 3.14
X = .TRUE.
N = X
R = N + 2
PRINT *, N, R, X
END
"""

ast = parser.parse(code)
print("AST:")
print(ast)

symbols, errors = check_program(ast)

print("\nTabela de símbolos:")
print(symbols)

print("\nErros:")
for e in errors:
    print("-", e)
