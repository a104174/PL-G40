import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class EwvmIfElseTest(unittest.TestCase):
    def test_ewvm_if_else(self):
        code = """
PROGRAM TEST
INTEGER N
N = 0
IF (N .GT. 0) THEN
PRINT *, 'POS'
ELSE
PRINT *, 'NAO POS'
ENDIF
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
            "PUSHI 0",
            "START",
            "PUSHI 0",
            "STOREG 0",
            "PUSHG 0",
            "PUSHI 0",
            "SUP",
            "JZ L0",
            'PUSHS "POS"',
            "WRITES",
            "WRITELN",
            "JUMP L1",
            "L0:",
            'PUSHS "NAO POS"',
            "WRITES",
            "WRITELN",
            "L1:",
            "STOP",
        ])
