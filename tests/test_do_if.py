import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class DoIfTest(unittest.TestCase):
    def test_do_with_if_codegen(self):
        code = """
PROGRAM TEST
INTEGER I, N
N = 3
DO 10 I = 1, N
IF (I .LT. N) THEN
PRINT *, I
ENDIF
10 CONTINUE
END
"""

        ast = parser.parse(code)
        symbols, errors = check_program(ast)

        self.assertEqual(errors, [])
        self.assertEqual(
            generate_program(ast),
            [
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
                "JZ LBL_10",
                "PUSHG 0",
                "PUSHG 1",
                "INF",
                "JZ L1",
                "PUSHG 0",
                "WRITEI",
                "WRITELN",
                "L1:",
                "PUSHG 0",
                "PUSHI 1",
                "ADD",
                "STOREG 0",
                "JUMP L0",
                "LBL_10:",
                "STOP",
            ],
        )
