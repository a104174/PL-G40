import unittest

from src.lexer import lexer


class LexerTest(unittest.TestCase):
    def test_basic_tokens(self):
        code = """
PROGRAM HELLO
INTEGER N
N = 5
PRINT *, N
END
"""

        lexer.input(code)
        tokens = [(tok.type, tok.value) for tok in lexer]

        self.assertEqual(
            tokens,
            [
                ('PROGRAM', 'PROGRAM'),
                ('ID', 'HELLO'),
                ('INTEGER', 'INTEGER'),
                ('ID', 'N'),
                ('ID', 'N'),
                ('ASSIGN', '='),
                ('NUMBER', 5),
                ('PRINT', 'PRINT'),
                ('TIMES', '*'),
                ('COMMA', ','),
                ('ID', 'N'),
                ('END', 'END'),
            ],
        )
