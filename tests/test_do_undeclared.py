import unittest

from src.parser import parser
from src.semantic import check_program


class DoUndeclaredTest(unittest.TestCase):
    def test_do_control_variable_must_be_declared(self):
        code = """
PROGRAM TEST
INTEGER N
N = 3
DO 10 I = 1, N
PRINT *, N
10 CONTINUE
END
"""

        ast = parser.parse(code)
        symbols, errors = check_program(ast)

        self.assertEqual(symbols, {'N': {'kind': 'scalar', 'type': 'INTEGER'}})
        self.assertEqual(errors, ["Variável de controlo 'I' usada sem declaração"])
