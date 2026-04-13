import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class DoTest(unittest.TestCase):
    def test_do_loop_codegen(self):
        code = """
PROGRAM TEST
INTEGER I, N
N = 5
DO 10 I = 1, N
PRINT *, I
10 CONTINUE
END
"""

        ast = parser.parse(code)
        symbols, errors = check_program(ast)

        self.assertEqual(
            symbols,
            {
                'I': {'kind': 'scalar', 'type': 'INTEGER'},
                'N': {'kind': 'scalar', 'type': 'INTEGER'},
            },
        )
        self.assertEqual(errors, [])
        self.assertEqual(
            generate_program(ast),
            [
                "PUSHI 0",
                "PUSHI 0",
                "START",
                "PUSHI 5",
                "STOREG 1",
                "PUSHI 1",
                "STOREG 0",
                "L0:",
                "PUSHG 0",
                "PUSHG 1",
                "INFEQ",
                "JZ LBL_10",
                "PUSHG 0",
                "WRITEI",
                "WRITELN",
                "PUSHG 0",
                "PUSHI 1",
                "ADD",
                "STOREG 0",
                "JUMP L0",
                "LBL_10:",
                "STOP",
            ],
        )
