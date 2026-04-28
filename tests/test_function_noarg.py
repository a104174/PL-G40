import unittest
from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program

class FunctionNoArgTest(unittest.TestCase):
    def test_function_no_arguments(self):
        code = """
PROGRAM TEST
INTEGER Y
Y = ZERO()
PRINT *, Y
END

INTEGER FUNCTION ZERO()
ZERO = 0
RETURN
END
"""
        ast = parser.parse(code)
        _, errors = check_program(ast)
        self.assertEqual(errors, [])

        vm_code = generate_program(ast)
        self.assertNotIn("PUSHI 0\nPUSHA FUNCZERO", "\n".join(vm_code))
        self.assertIn("PUSHA FUNCZERO", vm_code)
        self.assertIn("CALL", vm_code)