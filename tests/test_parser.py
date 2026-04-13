import unittest

from src.parser import parser


class ParserTest(unittest.TestCase):
    def test_basic_program_ast(self):
        code = """
PROGRAM HELLO
INTEGER N
N = 5
PRINT *, N
END
"""

        self.assertEqual(
            parser.parse(code),
            (
                'program',
                'HELLO',
                [
                    ('declare', 'INTEGER', [('scalar', 'N')]),
                    ('assign', 'N', ('number', 5)),
                    ('print', [('id', 'N')]),
                ],
                [],
            ),
        )
