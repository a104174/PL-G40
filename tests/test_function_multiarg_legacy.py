import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class FunctionMultiargLegacyTest(unittest.TestCase):
    def test_function_multiarg_with_labeled_if_uses_legacy_backend(self):
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
            "DECL N",
            "DECL BASE",
            "DECL RESULT",
            "PUSH 4",
            "STORE N",
            "PUSH 2",
            "STORE BASE",
            "LOAD N",
            "LOAD BASE",
            "CALL CONVRT",
            "STORE RESULT",
            "LOAD RESULT",
            "PRINT",
            "HALT",
            "FUNC CONVRT",
            "PARAM N",
            "PARAM B",
            "DECL CONVRT",
            "DECL N",
            "DECL B",
            "DECL ACC",
            "PUSH 0",
            "STORE ACC",
            "LABEL LBL_20",
            "LOAD N",
            "PUSH 0",
            "CMPGT",
            "JZ L0",
            "LOAD ACC",
            "LOAD B",
            "ADD",
            "STORE ACC",
            "LOAD N",
            "PUSH 1",
            "SUB",
            "STORE N",
            "JMP LBL_20",
            "LABEL L0",
            "LOAD ACC",
            "STORE CONVRT",
            "LOAD CONVRT",
            "RET",
            "ENDFUNC",
        ])
