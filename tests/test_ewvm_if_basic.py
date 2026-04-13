import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class EwvmIfBasicTest(unittest.TestCase):
    def test_ewvm_if_basic(self):
        code = """
PROGRAM TEST
INTEGER N
N = 5
IF (N .GT. 0) THEN
PRINT *, 'OK'
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
            "PUSHI 5",
            "STOREG 0",
            "PUSHG 0",
            "PUSHI 0",
            "SUP",
            "JZ L0",
            'PUSHS "OK"',
            "WRITES",
            "WRITELN",
            "L0:",
            "STOP",
        ])
