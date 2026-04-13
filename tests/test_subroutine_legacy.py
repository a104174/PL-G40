import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class SubroutineLegacyTest(unittest.TestCase):
    def test_subroutine_call_uses_legacy_backend(self):
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

        vm_code = generate_program(ast)

        self.assertEqual(vm_code, [
            "DECL N",
            "PUSH 1",
            "STORE N",
            "LOAD N",
            "CALL INC",
            "LOAD N",
            "PRINT",
            "HALT",
            "SUBROUTINE INC",
            "PARAM X",
            "DECL X",
            "LOAD X",
            "PUSH 1",
            "ADD",
            "STORE X",
            "RET",
            "ENDSUBROUTINE",
        ])
