import unittest

from src.parser import parser
from src.semantic import check_program


class SemanticTypesTest(unittest.TestCase):
    def test_assignment_type_mismatch(self):
        code = """
PROGRAM TEST
INTEGER N
LOGICAL X
X = .TRUE.
N = X
END
"""

        ast = parser.parse(code)
        symbols, errors = check_program(ast)

        self.assertEqual(
            symbols,
            {
                'N': {'kind': 'scalar', 'type': 'INTEGER'},
                'X': {'kind': 'scalar', 'type': 'LOGICAL'},
            },
        )
        self.assertEqual(errors, ["Incompatibilidade de tipos na atribuição: INTEGER <- LOGICAL"])
