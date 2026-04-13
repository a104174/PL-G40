import unittest

from src.parser import parser
from src.semantic import check_program


class FunctionInvalidTest(unittest.TestCase):
    def test_undeclared_function(self):
        code = """
PROGRAM TEST
INTEGER X, Y
X = 5
Y = FALTA(X)
PRINT *, Y
END
"""

        ast = parser.parse(code)
        symbols, errors = check_program(ast)

        self.assertEqual(
            symbols,
            {
                'X': {'kind': 'scalar', 'type': 'INTEGER'},
                'Y': {'kind': 'scalar', 'type': 'INTEGER'},
            },
        )
        self.assertEqual(errors, ["Função 'FALTA' usada sem declaração"])
