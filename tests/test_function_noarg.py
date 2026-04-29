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
        self.assertEqual(
            vm_code,
            [
                "PUSHI 0",
                "START",
                "PUSHN 1",
                "PUSHA FUNCZERO",
                "CALL",
                "STOREG 0",
                "PUSHG 0",
                "WRITEI",
                "WRITELN",
                "STOP",
                "FUNCZERO:",
                "PUSHI 0",
                "PUSHI 0",
                "STOREL 0",
                "PUSHL 0",
                "STOREL -1",
                "RETURN",
            ],
        )
