import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class ModBasicTest(unittest.TestCase):
    def test_mod_codegen(self):
        code = """
PROGRAM TEST
INTEGER A, B, X, N, I
A = 10
B = 3
X = MOD(A, B)
N = 9
I = 2
IF (MOD(N, I) .EQ. 1) THEN
PRINT *, MOD(X, 2)
ENDIF
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
                "PUSHI 9",
                "STOREG 3",
                "PUSHI 2",
                "STOREG 4",
                "PUSHG 3",
                "PUSHG 4",
                "MOD",
                "PUSHI 1",
                "EQUAL",
                "JZ L0",
                "PUSHG 2",
                "PUSHI 2",
                "MOD",
                "WRITEI",
                "WRITELN",
                "L0:",
                "STOP",
            ],
        )
