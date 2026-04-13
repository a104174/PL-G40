import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class EwvmGotoBasicTest(unittest.TestCase):
    def test_ewvm_goto_basic(self):
        code = """
PROGRAM TEST
INTEGER N
N = 0
10 CONTINUE
N = N + 1
IF (N .LT. 3) THEN
GOTO 10
ENDIF
PRINT *, N
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
            "START",
            "PUSHI 0",
            "STOREG 0",
            "LBL_10:",
            "PUSHG 0",
            "PUSHI 1",
            "ADD",
            "STOREG 0",
            "PUSHG 0",
            "PUSHI 3",
            "INF",
            "JZ L0",
            "JUMP LBL_10",
            "L0:",
            "PUSHG 0",
            "WRITEI",
            "WRITELN",
            "STOP",
        ])
