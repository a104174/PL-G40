import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class EwvmLabeledIfTest(unittest.TestCase):
    def test_ewvm_labeled_if(self):
        code = """
PROGRAM TEST
INTEGER N
N = 0
20 IF (N .LT. 3) THEN
N = N + 1
GOTO 20
ENDIF
PRINT *, N
END
"""

        ast = parser.parse(code)
        symbols, errors = check_program(ast)

        self.assertEqual(errors, [])

        vm_code = generate_program(ast)

        self.assertEqual(vm_code, [
            "PUSHI 0",
            "START",
            "PUSHI 0",
            "STOREG 0",
            "LBL20:",
            "PUSHG 0",
            "PUSHI 3",
            "INF",
            "JZ L0",
            "PUSHG 0",
            "PUSHI 1",
            "ADD",
            "STOREG 0",
            "JUMP LBL20",
            "L0:",
            "PUSHG 0",
            "WRITEI",
            "WRITELN",
            "STOP",
        ])
