import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class ArrayBasicTest(unittest.TestCase):
    def test_array_read_increment_and_sum(self):
        code = """
PROGRAM TEST
INTEGER NUMS(5)
INTEGER I, SOMA
SOMA = 0
DO 10 I = 1, 5
READ *, NUMS(I)
NUMS(I) = NUMS(I) + 1
SOMA = SOMA + NUMS(I)
10 CONTINUE
PRINT *, SOMA
END
"""

        ast = parser.parse(code)
        symbols, errors = check_program(ast)

        self.assertEqual(
            symbols,
            {
                'NUMS': {'kind': 'array', 'type': 'INTEGER', 'size': 5},
                'I': {'kind': 'scalar', 'type': 'INTEGER'},
                'SOMA': {'kind': 'scalar', 'type': 'INTEGER'},
            },
        )
        self.assertEqual(errors, [])
        self.assertEqual(
            generate_program(ast),
            [
                "PUSHN 5",
                "PUSHI 0",
                "PUSHI 0",
                "START",
                "PUSHI 0",
                "STOREG 6",
                "PUSHI 1",
                "STOREG 5",
                "L0:",
                "PUSHG 5",
                "PUSHI 5",
                "INFEQ",
                "JZ LBL_10",
                "PUSHGP",
                "PUSHG 5",
                "PUSHI 1",
                "SUB",
                "READ",
                "ATOI",
                "STOREN",
                "PUSHGP",
                "PUSHG 5",
                "PUSHI 1",
                "SUB",
                "PUSHGP",
                "PUSHG 5",
                "PUSHI 1",
                "SUB",
                "LOADN",
                "PUSHI 1",
                "ADD",
                "STOREN",
                "PUSHG 6",
                "PUSHGP",
                "PUSHG 5",
                "PUSHI 1",
                "SUB",
                "LOADN",
                "ADD",
                "STOREG 6",
                "PUSHG 5",
                "PUSHI 1",
                "ADD",
                "STOREG 5",
                "JUMP L0",
                "LBL_10:",
                "PUSHG 6",
                "WRITEI",
                "WRITELN",
                "STOP",
            ],
        )
