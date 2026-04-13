import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class EwvmModIfTest(unittest.TestCase):
    def test_ewvm_mod_if(self):
        code = """
PROGRAM TEST
INTEGER N, I
N = 9
I = 2
IF (MOD(N, I) .EQ. 1) THEN
PRINT *, N
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
            "PUSHI 0",
            "START",
            "PUSHI 9",
            "STOREG 0",
            "PUSHI 2",
            "STOREG 1",
            "PUSHG 0",
            "PUSHG 1",
            "MOD",
            "PUSHI 1",
            "EQUAL",
            "JZ L0",
            "PUSHG 0",
            "WRITEI",
            "WRITELN",
            "L0:",
            "STOP",
        ])
