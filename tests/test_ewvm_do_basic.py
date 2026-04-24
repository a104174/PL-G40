import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class EwvmDoBasicTest(unittest.TestCase):
    def test_ewvm_do_basic(self):
        code = """
PROGRAM TEST
INTEGER I, N
N = 3
DO 10 I = 1, N
PRINT *, I
10 CONTINUE
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
            "PUSHI 3",
            "STOREG 1",
            "PUSHI 1",
            "STOREG 0",
            "L0:",
            "PUSHG 0",
            "PUSHG 1",
            "INFEQ",
            "JZ LBL10",
            "PUSHG 0",
            "WRITEI",
            "WRITELN",
            "PUSHG 0",
            "PUSHI 1",
            "ADD",
            "STOREG 0",
            "JUMP L0",
            "LBL10:",
            "STOP",
        ])
