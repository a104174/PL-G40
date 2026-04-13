import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class EwvmModRealFallbackTest(unittest.TestCase):
    def test_ewvm_mod_real_fallback(self):
        code = """
PROGRAM TEST
REAL A, X
INTEGER B
A = 10.0
B = 3
X = MOD(A, B)
PRINT *, X
END
"""

        ast = parser.parse(code)
        symbols, errors = check_program(ast)

        self.assertEqual(errors, [])

        vm_code = generate_program(ast)

        print("\nCódigo gerado com fallback:")
        for instr in vm_code:
            print(instr)

        self.assertEqual(vm_code, [
            "DECL A",
            "DECL X",
            "DECL B",
            "PUSH 10.0",
            "STORE A",
            "PUSH 3",
            "STORE B",
            "LOAD A",
            "LOAD B",
            "MOD",
            "STORE X",
            "LOAD X",
            "PRINT",
            "HALT",
        ])
