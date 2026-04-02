from src.parser import parser
from src.semantic import check_program
from src.codegen import generate_program

code = """
PROGRAM TEST
INTEGER N
LOGICAL OK
N = 2
OK = .TRUE.
IF (OK .AND. (N .GT. 0)) THEN
PRINT *, 'VALIDO'
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
