import unittest

from src.parser import parser
from src.semantic import check_program


class ArrayIndexTypeInvalidTest(unittest.TestCase):
    def test_array_index_must_be_integer(self):
        code = """
PROGRAM TEST
INTEGER A(5)
REAL I
I = 2.0
PRINT *, A(I)
END
"""

        ast = parser.parse(code)
        symbols, errors = check_program(ast)

        self.assertIn("Indice do array 'A' deve ser INTEGER", [error.replace('Í', 'I') for error in errors])
