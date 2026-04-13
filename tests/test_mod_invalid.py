import unittest

from src.parser import parser
from src.semantic import check_program


class ModInvalidTest(unittest.TestCase):
    def test_mod_with_logical_operand(self):
        code = """
PROGRAM TEST
INTEGER X, N
LOGICAL FLAG
N = 5
FLAG = .TRUE.
X = MOD(N, FLAG)
END
"""

        ast = parser.parse(code)
        symbols, errors = check_program(ast)

        self.assertEqual(
            symbols,
            {
                'X': {'kind': 'scalar', 'type': 'INTEGER'},
                'N': {'kind': 'scalar', 'type': 'INTEGER'},
                'FLAG': {'kind': 'scalar', 'type': 'LOGICAL'},
            },
        )
        self.assertEqual(errors, ["Operação MOD inválida com tipos INTEGER e LOGICAL"])
