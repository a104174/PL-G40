from src.parser import parser

code = """
PROGRAM HELLO
INTEGER N
N = 5
PRINT *, N
END
"""

result = parser.parse(code)
print(result)
