import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class IfValidTest(unittest.TestCase):
    def test_logical_if_falls_back_to_legacy(self):
        code = """
PROGRAM TEST
INTEGER N
LOGICAL OK
N = 2
OK = .TRUE.
IF (OK .AND. (N .GT. 0)) THEN
PRINT *, 'VALIDO'
ENDIF
END
"""

        ast = parser.parse(code)
        symbols, errors = check_program(ast)

        self.assertEqual(errors, [])
        self.assertEqual(
            generate_program(ast),
            [
                "DECL N",
                "DECL OK",
                "PUSH 2",
                "STORE N",
                "PUSH 1",
                "STORE OK",
                "LOAD OK",
                "LOAD N",
                "PUSH 0",
                "CMPGT",
                "AND",
                "JZ L0",
                'PRINTSTR "VALIDO"',
                "LABEL L0",
                "HALT",
            ],
        )
