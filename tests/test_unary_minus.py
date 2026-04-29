import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class UnaryMinusTest(unittest.TestCase):
    def test_unary_minus_integer_codegen(self):
        code = """
PROGRAM TEST
INTEGER X, Y
X = 5
Y = -X
PRINT *, Y
END
"""

        ast = parser.parse(code)
        _, errors = check_program(ast)

        self.assertEqual(errors, [])
        self.assertEqual(
            generate_program(ast),
            [
                "PUSHI 0",
                "PUSHI 0",
                "START",
                "PUSHI 5",
                "STOREG 0",
                "PUSHG 0",
                "PUSHI -1",
                "MUL",
                "STOREG 1",
                "PUSHG 1",
                "WRITEI",
                "WRITELN",
                "STOP",
            ],
        )

    def test_unary_minus_real_codegen(self):
        code = """
PROGRAM TEST
REAL X, Y
X = 2.5
Y = -X
PRINT *, Y
END
"""

        ast = parser.parse(code)
        _, errors = check_program(ast)

        self.assertEqual(errors, [])
        self.assertEqual(
            generate_program(ast),
            [
                "PUSHF 0.0",
                "PUSHF 0.0",
                "START",
                "PUSHF 2.5",
                "STOREG 0",
                "PUSHG 0",
                "PUSHF -1.0",
                "FMUL",
                "STOREG 1",
                "PUSHG 1",
                "WRITEF",
                "WRITELN",
                "STOP",
            ],
        )

    def test_unary_minus_logical_is_invalid(self):
        code = """
PROGRAM TEST
LOGICAL L
L = .TRUE.
L = -L
END
"""

        ast = parser.parse(code)
        _, errors = check_program(ast)

        self.assertEqual(errors, ["Operador unário '-' inválido sobre tipo LOGICAL"])
