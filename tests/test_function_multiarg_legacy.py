import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class FunctionMultiargEwvmTest(unittest.TestCase):
    def test_function_multiarg_with_labeled_if_uses_ewvm_backend(self):
        code = """
PROGRAM TEST
INTEGER N, BASE, RESULT
N = 4
BASE = 2
RESULT = CONVRT(N, BASE)
PRINT *, RESULT
END

INTEGER FUNCTION CONVRT(N, B)
INTEGER N, B, ACC
ACC = 0
20 IF (N .GT. 0) THEN
ACC = ACC + B
N = N - 1
GOTO 20
ENDIF
CONVRT = ACC
RETURN
END
"""

        ast = parser.parse(code)
        symbols, errors = check_program(ast)

        self.assertEqual(errors, [])

        vm_code = generate_program(ast)

        self.assertEqual(vm_code, [
            "PUSHI 0",
            "PUSHI 0",
            "PUSHI 0",
            "START",
            "PUSHI 4",
            "STOREG 0",
            "PUSHI 2",
            "STOREG 1",
            "PUSHG 0",
            "PUSHG 1",
            "PUSHA FUNCCONVRT",
            "CALL",
            "SWAP",
            "POP 1",
            "STOREG 2",
            "PUSHG 2",
            "WRITEI",
            "WRITELN",
            "STOP",
            "FUNCCONVRT:",
            "PUSHI 0",
            "PUSHI 0",
            "PUSHI 0",
            "STOREL 1",
            "CONVRTLBL20:",
            "PUSHFP",
            "LOAD -2",
            "PUSHI 0",
            "SUP",
            "JZ L0",
            "PUSHL 1",
            "PUSHFP",
            "LOAD -1",
            "ADD",
            "STOREL 1",
            "PUSHFP",
            "LOAD -2",
            "PUSHI 1",
            "SUB",
            "STOREL -2",
            "JUMP CONVRTLBL20",
            "L0:",
            "PUSHL 1",
            "STOREL 0",
            "PUSHL 0",
            "STOREL -1",
            "RETURN",
        ])
