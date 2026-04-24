import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class EwvmFunctionBasicTest(unittest.TestCase):
    def test_ewvm_function_basic(self):
        code = """
PROGRAM TEST
INTEGER X, Y
X = 5
Y = DOBRO(X)
PRINT *, Y
END

INTEGER FUNCTION DOBRO(N)
INTEGER N
DOBRO = N * 2
RETURN
END
"""

        ast = parser.parse(code)
        symbols, errors = check_program(ast)

        self.assertEqual(errors, [])

        vm_code = generate_program(ast)

        print("\nCódigo EWVM gerado:")
        for instr in vm_code:
            print(instr)

        self.assertEqual(vm_code, [
            "PUSHI 0",
            "PUSHI 0",
            "START",
            "PUSHI 5",
            "STOREG 0",
            "PUSHG 0",
            "PUSHA FUNCDOBRO",
            "CALL",
            "STOREG 1",
            "PUSHG 1",
            "WRITEI",
            "WRITELN",
            "STOP",
            "FUNCDOBRO:",
            "PUSHI 0",
            "PUSHFP",
            "LOAD -1",
            "PUSHI 2",
            "MUL",
            "STOREL 0",
            "PUSHL 0",
            "STOREL -1",
            "RETURN",
        ])
