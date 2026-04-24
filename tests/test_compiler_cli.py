import unittest

from compiler import compile_source


class CompilerCliTest(unittest.TestCase):
    def test_compile_source_returns_ewvm_code(self):
        code = """
PROGRAM TEST
INTEGER N
N = 5
PRINT *, N
END
"""

        self.assertEqual(
            compile_source(code),
            "\n".join([
                "PUSHI 0",
                "START",
                "PUSHI 5",
                "STOREG 0",
                "PUSHG 0",
                "WRITEI",
                "WRITELN",
                "STOP",
                "",
            ]),
        )

    def test_compile_source_rejects_semantic_errors(self):
        code = """
PROGRAM TEST
N = 5
END
"""

        with self.assertRaisesRegex(ValueError, "Variável 'N' usada sem declaração"):
            compile_source(code)
