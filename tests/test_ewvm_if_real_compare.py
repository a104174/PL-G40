import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class EwvmIfRealCompareTest(unittest.TestCase):
    def test_ewvm_if_real_compare(self):
        code = """
PROGRAM TEST
REAL A
INTEGER N
A = 2.5
N = 2
IF (A .GE. N) THEN
PRINT *, 'OK'
ENDIF
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
            "PUSHI 0",
            "START",
            "PUSHF 2.5",
            "STOREG 0",
            "PUSHI 2",
            "STOREG 1",
            "PUSHG 0",
            "PUSHG 1",
            "ITOF",
            "FSUPEQ",
            "JZ L0",
            'PUSHS "OK"',
            "WRITES",
            "WRITELN",
            "L0:",
            "STOP",
        ])
