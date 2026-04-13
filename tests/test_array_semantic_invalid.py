import unittest

from src.parser import parser
from src.semantic import check_program


class ArraySemanticInvalidTest(unittest.TestCase):
    def test_array_invalid_index_and_scalar_use(self):
        code = """
PROGRAM TEST
INTEGER NUMS(5), X
LOGICAL IDX
IDX = .TRUE.
X = NUMS(IDX)
PRINT *, NUMS
END
"""

        ast = parser.parse(code)
        symbols, errors = check_program(ast)

        self.assertEqual(
            symbols,
            {
                'NUMS': {'kind': 'array', 'type': 'INTEGER', 'size': 5},
                'X': {'kind': 'scalar', 'type': 'INTEGER'},
                'IDX': {'kind': 'scalar', 'type': 'LOGICAL'},
            },
        )
        self.assertEqual(
            errors,
            [
                "Índice do array 'NUMS' deve ser INTEGER",
                "Array 'NUMS' usado sem índice em expressão",
            ],
        )
