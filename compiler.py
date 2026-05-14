"""Interface de linha de comandos do compilador.

Este módulo não contém regras de linguagem nem geração de código. A sua função é
ligar as fases principais do compilador: leitura do ficheiro Fortran, construção
da AST, validação semântica e emissão de código EWVM.
"""

import argparse
import sys

from src.codegen import generate_program, supports_ewvm_phase1
from src.parser import parser
from src.semantic import check_program


def compile_source(source):
    """Compila uma string com código Fortran e devolve código EWVM.

    A função é deliberadamente pequena para refletir o pipeline do compilador.
    Primeiro constrói a AST, depois executa a análise semântica e, finalmente,
    chama o backend EWVM. Erros sintáticos, semânticos ou de suporte são
    convertidos para `ValueError`, que a CLI apresenta ao utilizador.
    """
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
    """Ponto de entrada da CLI.

    Recebe um ficheiro de entrada obrigatório e, opcionalmente, um ficheiro de
    saída. Sem `-o/--output`, o código EWVM é escrito no stdout, o que facilita
    testes rápidos e redirecionamento pela shell.
    """
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
