import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


LEGACY_ONLY_PREFIXES = {
    "CMPGT",
    "CMPGE",
    "CMPLT",
    "CMPLE",
    "CMPEQ",
    "CMPNE",
    "DECL",
    "DECLARR",
    "ENDFUNC",
    "ENDSUBROUTINE",
    "FUNC",
    "HALT",
    "JMP",
    "LABEL",
    "PARAM",
    "PRINT",
    "PRINTSTR",
    "READARR",
    "RET",
    "SUBROUTINE",
}


def compile_code(code):
    ast = parser.parse(code)
    _, errors = check_program(ast)
    if errors:
        raise AssertionError(errors)

    return generate_program(ast)


def assert_no_legacy_code(testcase, vm_code):
    testcase.assertIn("START", vm_code)
    testcase.assertIn("STOP", vm_code)

    for instruction in vm_code:
        opcode = instruction.split()[0].rstrip(":")
        testcase.assertNotIn(opcode, LEGACY_ONLY_PREFIXES)
        testcase.assertFalse(instruction.startswith("CALL "))


class EnunciadoEwvmExamplesTest(unittest.TestCase):
    def test_primo_example_uses_ewvm_logical_codegen(self):
        code = """
PROGRAM PRIMO
INTEGER NUM, I
LOGICAL ISPRIM
PRINT *, 'Introduza um numero inteiro positivo:'
READ *, NUM
ISPRIM = .TRUE.
I = 2
20 IF (I .LE. (NUM/2) .AND. ISPRIM) THEN
IF (MOD(NUM, I) .EQ. 0) THEN
ISPRIM = .FALSE.
ENDIF
I = I + 1
GOTO 20
ENDIF
IF (ISPRIM) THEN
PRINT *, NUM, ' e um numero primo'
ELSE
PRINT *, NUM, ' nao e um numero primo'
ENDIF
END
"""

        vm_code = compile_code(code)

        assert_no_legacy_code(self, vm_code)
        self.assertIn("AND", vm_code)

    def test_conversor_example_uses_ewvm_multiarg_function_codegen(self):
        code = """
PROGRAM CONVERSOR
INTEGER NUM, BASE, RESULT, CONVRT
PRINT *, 'INTRODUZA UM NUMERO DECIMAL INTEIRO:'
READ *, NUM
DO 10 BASE = 2, 9
RESULT = CONVRT(NUM, BASE)
PRINT *, 'BASE ', BASE, ': ', RESULT
10 CONTINUE
END
INTEGER FUNCTION CONVRT(N, B)
INTEGER N, B, QUOT, REM, POT, VAL
VAL = 0
POT = 1
QUOT = N
20 IF (QUOT .GT. 0) THEN
REM = MOD(QUOT, B)
VAL = VAL + (REM * POT)
QUOT = QUOT / B
POT = POT * 10
GOTO 20
ENDIF
CONVRT = VAL
RETURN
END
"""

        vm_code = compile_code(code)

        assert_no_legacy_code(self, vm_code)
        self.assertIn("PUSHA FUNCCONVRT", vm_code)
        self.assertIn("SWAP", vm_code)
        self.assertIn("POP 1", vm_code)
        self.assertIn("CONVRTLBL20:", vm_code)
