from parser import parser
from semantic import check_program
from codegen import generate_program

code = """
PROGRAM TEST
INTEGER N
READ *, N
IF (N .GT. 0) THEN
PRINT *, 'POSITIVO'
ELSE
PRINT *, 'NAO POSITIVO'
ENDIF
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
