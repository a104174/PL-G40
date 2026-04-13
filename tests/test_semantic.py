import unittest

from src.parser import parser
from src.semantic import check_program


class SemanticTest(unittest.TestCase):
    def test_semantic_type_error_in_program(self):
        code = """
PROGRAM TEST
INTEGER N
REAL R
LOGICAL X

N = 5
R = 3.14
X = .TRUE.
N = X
R = N + 2
PRINT *, N, R, X
END
"""

        ast = parser.parse(code)
        symbols, errors = check_program(ast)

        self.assertEqual(
            symbols,
            {
                'N': {'kind': 'scalar', 'type': 'INTEGER'},
                'R': {'kind': 'scalar', 'type': 'REAL'},
                'X': {'kind': 'scalar', 'type': 'LOGICAL'},
            },
        )
        self.assertEqual(errors, ["Incompatibilidade de tipos na atribuição: INTEGER <- LOGICAL"])
