# PL-G40 - Compilador Fortran 77 para EWVM

Projeto da unidade curricular de Processamento de Linguagens, ano letivo 2025/2026.

## Autores

- A104174 - Hélder Tiago Peixoto da Cruz
- A104434 - João Pedro Rodrigues Veloso
- A104255 - Orlando Daniel Venda da Costa

## Descrição

Este projeto implementa, em Python com PLY, um compilador para um subconjunto de Fortran 77 em formato livre. O compilador faz análise lexical, análise sintática, análise semântica e geração direta de código para a EWVM.

O subset suportado inclui declarações `INTEGER`, `REAL` e `LOGICAL`, expressões aritméticas, relacionais e lógicas, `IF-THEN-ELSE`, ciclos `DO` com labels, `GOTO`, `READ`, `PRINT`, arrays unidimensionais globais, `FUNCTION` e a função intrínseca `MOD` para inteiros.

## Instalação

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Como correr o compilador

Gerar código EWVM para stdout:

```bash
.venv/bin/python compiler.py examples/primo.f
```

Gerar código EWVM para um ficheiro:

```bash
.venv/bin/python compiler.py examples/primo.f -o examples/primo.vm
```

## Testes

```bash
.venv/bin/python -m unittest discover -v tests
```

## Exemplos

Os exemplos principais estão em `examples/`:

- `hello.f`
- `fatorial.f`
- `primo.f`
- `somaarr.f`
- `conversor.f`

Os respetivos ficheiros `.vm` contêm código EWVM gerado para esses programas.

## Limitações conhecidas

- `SUBROUTINE` e `CALL` são reconhecidos sintática e semanticamente, mas não têm backend EWVM.
- O formato fixo clássico de Fortran 77 não é suportado.
- Arrays são apenas unidimensionais; arrays locais em funções não são gerados para EWVM.
- Não há verificação de limites em acessos a arrays.
- `READ` e `PRINT` suportam apenas as formas simplificadas `READ *, ...` e `PRINT *, ...`.
- Ciclos `DO` têm incremento implícito de 1, sem passo explícito.
- Literais reais usam formato simples, sem notação exponencial.
- O código gerado não é otimizado.
