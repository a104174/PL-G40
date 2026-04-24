import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class EwvmArrayReadSumTest(unittest.TestCase):
    def test_ewvm_array_read_sum(self):
        code = """
PROGRAM TEST
INTEGER NUMS(3)
INTEGER I, SOMA
SOMA = 0
DO 10 I = 1, 3
READ *, NUMS(I)
SOMA = SOMA + NUMS(I)
10 CONTINUE
PRINT *, SOMA
END
"""

        ast = parser.parse(code)
        symbols, errors = check_program(ast)

        self.assertEqual(errors, [])

        vm_code = generate_program(ast)

        print("\nCódigo EWVM gerado:")
        for instr in vm_code:
            print(instr)

        self.assertEqual(vm_code, [
            "PUSHN 3",
            "PUSHI 0",
            "PUSHI 0",
            "START",
            "PUSHI 0",
            "STOREG 4",
            "PUSHI 1",
            "STOREG 3",
            "L0:",
            "PUSHG 3",
            "PUSHI 3",
            "INFEQ",
            "JZ LBL10",
            "PUSHGP",
            "PUSHG 3",
            "PUSHI 1",
            "SUB",
            "READ",
            "ATOI",
            "STOREN",
            "PUSHG 4",
            "PUSHGP",
            "PUSHG 3",
            "PUSHI 1",
            "SUB",
            "LOADN",
            "ADD",
            "STOREG 4",
            "PUSHG 3",
            "PUSHI 1",
            "ADD",
            "STOREG 3",
            "JUMP L0",
            "LBL10:",
            "PUSHG 4",
            "WRITEI",
            "WRITELN",
            "STOP",
        ])
