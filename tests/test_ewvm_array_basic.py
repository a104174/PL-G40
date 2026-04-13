import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class EwvmArrayBasicTest(unittest.TestCase):
    def test_ewvm_array_basic(self):
        code = """
PROGRAM TEST
INTEGER NUMS(3), I
I = 1
NUMS(I) = 7
PRINT *, NUMS(I)
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
            "PUSHN 3",
            "PUSHI 0",
            "START",
            "PUSHI 1",
            "STOREG 3",
            "PUSHGP",
            "PUSHG 3",
            "PUSHI 1",
            "SUB",
            "PUSHI 7",
            "STOREN",
            "PUSHGP",
            "PUSHG 3",
            "PUSHI 1",
            "SUB",
            "LOADN",
            "WRITEI",
            "WRITELN",
            "STOP",
        ])
