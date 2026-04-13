import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class EwvmModBasicTest(unittest.TestCase):
    def test_ewvm_mod_basic(self):
        code = """
PROGRAM TEST
INTEGER A, B, X
A = 10
B = 3
X = MOD(A, B)
PRINT *, X
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
            "PUSHI 0",
            "START",
            "PUSHI 10",
            "STOREG 0",
            "PUSHI 3",
            "STOREG 1",
            "PUSHG 0",
            "PUSHG 1",
            "MOD",
            "STOREG 2",
            "PUSHG 2",
            "WRITEI",
            "WRITELN",
            "STOP",
        ])
