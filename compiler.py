import argparse
import sys

from src.codegen import generate_program, supports_ewvm_phase1
from src.parser import parser
from src.semantic import check_program


def compile_source(source):
    ast = parser.parse(source)
    if ast is None:
        raise ValueError("Erro sintático")

    _, errors = check_program(ast)
    if errors:
        raise ValueError("\n".join(errors))

    if not supports_ewvm_phase1(ast):
        raise ValueError("Geração EWVM não suportada para este programa")

    return "\n".join(generate_program(ast)) + "\n"


def main():
    arg_parser = argparse.ArgumentParser(description="Compilador Fortran 77 para EWVM")
    arg_parser.add_argument("input", help="Ficheiro Fortran de entrada")
    arg_parser.add_argument("-o", "--output", help="Ficheiro EWVM de saída")
    args = arg_parser.parse_args()

    with open(args.input, encoding="utf-8") as source_file:
        source = source_file.read()

    try:
        output = compile_source(source)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, "w", encoding="utf-8") as output_file:
            output_file.write(output)
    else:
        print(output, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
