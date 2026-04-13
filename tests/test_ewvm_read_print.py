import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class EwvmReadPrintTest(unittest.TestCase):
    def test_ewvm_read_print(self):
        code = """
PROGRAM TEST
INTEGER N
READ *, N
PRINT *, 'N = ', N
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
            "READ",
            "ATOI",
            "STOREG 0",
            'PUSHS "N = "',
            "WRITES",
            "PUSHG 0",
            "WRITEI",
            "WRITELN",
            "STOP",
        ])
