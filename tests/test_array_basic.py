from src.parser import parser
from src.semantic import check_program
from src.codegen import generate_program

code = """
PROGRAM TEST
INTEGER NUMS(5)
INTEGER I, SOMA
SOMA = 0
DO 10 I = 1, 5
READ *, NUMS(I)
NUMS(I) = NUMS(I) + 1
SOMA = SOMA + NUMS(I)
10 CONTINUE
PRINT *, SOMA
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
