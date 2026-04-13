import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class EwvmBasicIntTest(unittest.TestCase):
    def test_ewvm_basic_int(self):
        code = """
PROGRAM TEST
INTEGER X, Y
X = 5
Y = X + 2
PRINT *, Y
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
            "PUSHI 2",
            "ADD",
            "STOREG 1",
            "PUSHG 1",
            "WRITEI",
            "WRITELN",
            "STOP",
        ])
