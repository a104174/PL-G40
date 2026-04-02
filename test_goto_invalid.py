from parser import parser
from semantic import check_program
from codegen import generate_program

code = """
PROGRAM TEST
INTEGER N
N = 0
GOTO 99
PRINT *, N
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
