import unittest

from src.parser import parser
from src.semantic import check_program


class GotoInvalidTest(unittest.TestCase):
    def test_goto_missing_label(self):
        code = """
PROGRAM TEST
INTEGER N
N = 0
GOTO 99
PRINT *, N
END
"""

        ast = parser.parse(code)
        symbols, errors = check_program(ast)

        self.assertEqual(symbols, {'N': {'kind': 'scalar', 'type': 'INTEGER'}})
        self.assertEqual(errors, ["Label '99' usado em GOTO não existe"])
