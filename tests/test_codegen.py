import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class CodegenTest(unittest.TestCase):
    def test_legacy_codegen_for_logical_program(self):
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
                "DECL N",
                "DECL R",
                "DECL X",
                "PUSH 5",
                "STORE N",
                "LOAD N",
                "PUSH 2",
                "ADD",
                "STORE R",
                "PUSH 1",
                "STORE X",
                'PRINTSTR "Valor de N = "',
                "LOAD N",
                "PRINT",
                "LOAD R",
                "PRINT",
                "LOAD X",
                "PRINT",
                "HALT",
            ],
        )
