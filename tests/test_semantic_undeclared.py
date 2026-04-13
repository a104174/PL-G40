import unittest

from src.parser import parser
from src.semantic import check_program


class SemanticUndeclaredTest(unittest.TestCase):
    def test_assignment_to_undeclared_variable(self):
        code = """
PROGRAM TEST
INTEGER N
N = 1
X = N + 1
END
"""

        ast = parser.parse(code)
        symbols, errors = check_program(ast)

        self.assertEqual(symbols, {'N': {'kind': 'scalar', 'type': 'INTEGER'}})
        self.assertEqual(errors, ["Variável 'X' usada sem declaração"])
