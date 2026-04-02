from parser import parser
from semantic import check_program
from codegen import generate_program

code = """
PROGRAM TEST
INTEGER NUMS(5), X
LOGICAL IDX
IDX = .TRUE.
X = NUMS(IDX)
PRINT *, NUMS
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
