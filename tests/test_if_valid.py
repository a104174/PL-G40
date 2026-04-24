import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class IfValidTest(unittest.TestCase):
    def test_logical_if_uses_ewvm(self):
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
                "PUSHI 0",
                "PUSHI 0",
                "START",
                "PUSHI 2",
                "STOREG 0",
                "PUSHI 1",
                "STOREG 1",
                "PUSHG 1",
                "PUSHG 0",
                "PUSHI 0",
                "SUP",
                "AND",
                "JZ L0",
                'PUSHS "VALIDO"',
                "WRITES",
                "WRITELN",
                "L0:",
                "STOP",
            ],
        )
