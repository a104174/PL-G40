from src.parser import parser
from src.semantic import check_program
from src.codegen import generate_program

code = """
PROGRAM TEST
INTEGER N
N = 3
DO 10 I = 1, N
PRINT *, N
10 CONTINUE
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

if not errors:
    print("\nCódigo gerado:")
    vm_code = generate_program(ast)
    for instr in vm_code:
        print(instr)
