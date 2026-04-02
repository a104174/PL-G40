from parser import parser
from semantic import check_program
from codegen import generate_program

code = """
PROGRAM TEST
INTEGER N
REAL R
LOGICAL X

N = 5
R = N + 2
X = .TRUE.
PRINT *, 'Valor de N = ', N
PRINT *, R
PRINT *, X
END
"""

ast = parser.parse(code)

symbols, errors = check_program(ast)

if errors:
    print("Erros semânticos:")
    for e in errors:
        print("-", e)
else:
    vm_code = generate_program(ast)
    print("Código gerado:")
    for instr in vm_code:
        print(instr)