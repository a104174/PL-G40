import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class EwvmBasicRealTest(unittest.TestCase):
    def test_ewvm_basic_real(self):
        code = """
PROGRAM TEST
REAL A, B
A = 3.5
B = A * 2.0
PRINT *, B
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
            "PUSHF 0.0",
            "PUSHF 0.0",
            "START",
            "PUSHF 3.5",
            "STOREG 0",
            "PUSHG 0",
            "PUSHF 2.0",
            "FMUL",
            "STOREG 1",
            "PUSHG 1",
            "WRITEF",
            "WRITELN",
            "STOP",
        ])
