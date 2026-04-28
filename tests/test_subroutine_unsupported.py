import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class SubroutineUnsupportedTest(unittest.TestCase):
    def test_subroutine_call_is_rejected_without_ewvm_backend(self):
        code = """
PROGRAM TEST
INTEGER N
N = 1
CALL INC(N)
PRINT *, N
END

SUBROUTINE INC(X)
INTEGER X
X = X + 1
RETURN
END
"""

        ast = parser.parse(code)
        symbols, errors = check_program(ast)

        self.assertEqual(errors, [])

        with self.assertRaisesRegex(NotImplementedError, "Geração EWVM não suportada"):
            generate_program(ast)
