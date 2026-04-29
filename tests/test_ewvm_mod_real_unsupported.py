import unittest

from src.parser import parser
from src.semantic import check_program


class EwvmModRealUnsupportedTest(unittest.TestCase):
    def test_mod_real_is_rejected_semantically(self):
        code = """
PROGRAM TEST
REAL A, X
INTEGER B
A = 10.0
B = 3
X = MOD(A, B)
PRINT *, X
END
"""

        ast = parser.parse(code)
        _, errors = check_program(ast)

        self.assertEqual(errors, ["Operação MOD inválida com tipos REAL e INTEGER"])
