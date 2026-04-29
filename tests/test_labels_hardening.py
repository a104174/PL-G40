import unittest

from src.codegen import generate_program
from src.parser import parser
from src.semantic import check_program


class LabelsHardeningTest(unittest.TestCase):
    def test_real_labels_are_invalid(self):
        code = """
PROGRAM TEST
INTEGER I
10.5 CONTINUE
GOTO 10.5
DO 20.5 I = 1, 1
PRINT *, I
20.5 CONTINUE
END
"""

        ast = parser.parse(code)
        _, errors = check_program(ast)

        self.assertEqual(
            errors,
            [
                "Label '10.5' em CONTINUE deve ser inteiro",
                "Label '20.5' em DO deve ser inteiro",
                "Label '10.5' em GOTO deve ser inteiro",
            ],
        )

    def test_duplicate_label_is_invalid(self):
        code = """
PROGRAM TEST
INTEGER X
10 CONTINUE
10 CONTINUE
END
"""

        ast = parser.parse(code)
        _, errors = check_program(ast)

        self.assertEqual(errors, ["Label '10' declarado mais do que uma vez"])

    def test_valid_goto_label_still_codegen(self):
        code = """
PROGRAM TEST
INTEGER X
X = 0
10 CONTINUE
GOTO 10
END
"""

        ast = parser.parse(code)
        _, errors = check_program(ast)

        self.assertEqual(errors, [])
        self.assertEqual(
            generate_program(ast),
            [
                "PUSHI 0",
                "START",
                "PUSHI 0",
                "STOREG 0",
                "LBL10:",
                "JUMP LBL10",
                "STOP",
            ],
        )
