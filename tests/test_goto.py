import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class GotoTest(unittest.TestCase):
    def test_goto_loop_codegen(self):
        code = """
PROGRAM TEST
INTEGER N
N = 0
10 CONTINUE
N = N + 1
IF (N .LT. 5) THEN
GOTO 10
ENDIF
PRINT *, N
END
"""

        ast = parser.parse(code)
        symbols, errors = check_program(ast)

        self.assertEqual(errors, [])
        self.assertEqual(
            generate_program(ast),
            [
                "PUSHI 0",
                "START",
                "PUSHI 0",
                "STOREG 0",
                "LBL10:",
                "PUSHG 0",
                "PUSHI 1",
                "ADD",
                "STOREG 0",
                "PUSHG 0",
                "PUSHI 5",
                "INF",
                "JZ L0",
                "JUMP LBL10",
                "L0:",
                "PUSHG 0",
                "WRITEI",
                "WRITELN",
                "STOP",
            ],
        )
