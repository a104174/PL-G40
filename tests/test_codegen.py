import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class CodegenTest(unittest.TestCase):
    def test_ewvm_codegen_for_logical_program(self):
        code = """
PROGRAM TEST
INTEGER N
REAL R
LOGICAL X

N = 5
R = N + 2
X = .TRUE.
PRINT *, 'Valor de N = ', N
PRINT *, R
PRINT *, X
END
"""

        ast = parser.parse(code)
        symbols, errors = check_program(ast)

        self.assertEqual(errors, [])
        self.assertEqual(
            generate_program(ast),
            [
                "PUSHI 0",
                "PUSHF 0.0",
                "PUSHI 0",
                "START",
                "PUSHI 5",
                "STOREG 0",
                "PUSHG 0",
                "PUSHI 2",
                "ADD",
                "ITOF",
                "STOREG 1",
                "PUSHI 1",
                "STOREG 2",
                'PUSHS "Valor de N = "',
                "WRITES",
                "PUSHG 0",
                "WRITEI",
                "WRITELN",
                "PUSHG 1",
                "WRITEF",
                "WRITELN",
                "PUSHG 2",
                "WRITEI",
                "WRITELN",
                "STOP",
            ],
        )
