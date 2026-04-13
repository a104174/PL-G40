import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class IfTest(unittest.TestCase):
    def test_if_else_codegen(self):
        code = """
PROGRAM TEST
INTEGER N
READ *, N
IF (N .GT. 0) THEN
PRINT *, 'POSITIVO'
ELSE
PRINT *, 'NAO POSITIVO'
ENDIF
END
"""

        ast = parser.parse(code)
        symbols, errors = check_program(ast)

        self.assertEqual(symbols, {'N': {'kind': 'scalar', 'type': 'INTEGER'}})
        self.assertEqual(errors, [])
        self.assertEqual(
            generate_program(ast),
            [
                "PUSHI 0",
                "START",
                "READ",
                "ATOI",
                "STOREG 0",
                "PUSHG 0",
                "PUSHI 0",
                "SUP",
                "JZ L0",
                'PUSHS "POSITIVO"',
                "WRITES",
                "WRITELN",
                "JUMP L1",
                "L0:",
                'PUSHS "NAO POSITIVO"',
                "WRITES",
                "WRITELN",
                "L1:",
                "STOP",
            ],
        )
