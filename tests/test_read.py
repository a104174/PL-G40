import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class ReadTest(unittest.TestCase):
    def test_read_and_print_codegen(self):
        code = """
PROGRAM TEST
INTEGER N, X
READ *, N, X
PRINT *, 'Valores: ', N, X
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
                "READ",
                "ATOI",
                "STOREG 0",
                "READ",
                "ATOI",
                "STOREG 1",
                'PUSHS "Valores: "',
                "WRITES",
                "PUSHG 0",
                "WRITEI",
                "PUSHG 1",
                "WRITEI",
                "WRITELN",
                "STOP",
            ],
        )
