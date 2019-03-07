from typing import List
from msdsl.generator.generator import CodeGenerator

def case_statment(gen: CodeGenerator, sel, var, values: List, default=None):
    gen.writeln('always @(*) begin')
    gen.indent()

    gen.writeln(f'case ({sel})')
    gen.indent()

    for k, value in enumerate(values):
        gen.writeln(f'{k}: {var} = {value};')

    if default is not None:
        gen.writeln(f'default: {var} = {default};')

    gen.dedent()
    gen.writeln('endcase')

    gen.dedent()
    gen.writeln('end')

def main():
    gen = CodeGenerator()

    case_statment(gen, 'sel', 'var', ['a', 'b', 'c', 'd'], 'e')

    print(gen.text)

if __name__ == '__main__':
    main()