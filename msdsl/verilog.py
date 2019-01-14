import datetime
from msdsl.generator import CodeGenerator

class VerilogGenerator(CodeGenerator):
    def __init__(self, filename, tab_string='    ', line_ending='\n'):
        self.filename = filename
        self.tab_string = tab_string
        self.line_ending = line_ending

        # initialize variables
        self.tab_level = 0
        self.tmp_counter = 0
        self.variable_names = set()

        # initialize model file
        self.init_file()

    #######################################################
    # implementation of abstract CodeGenerator interface

    def section(self, label):
        self.comment(label)

    def mul_const_real(self, coeff, var, out=None):
        if out is None:
            out = self.tmpvar()

        self.macro_call('MUL_CONST_REAL', self.real2str(coeff), var, out)

        return out

    def make_const_real(self, value, out=None):
        if out is None:
            out = self.tmpvar()

        self.macro_call('MAKE_CONST_REAL', self.real2str(value), out)

        return out

    def add_real(self, a, b, out=None):
        if out is None:
            out = self.tmpvar()

        self.macro_call('ADD_REAL', a, b, out)

        return out

    def mem_into_real(self, next, curr):
        self.macro_call('MEM_INTO_REAL', next, curr)

    #######################################################

    def init_file(self):
        """
        Initializes the output file with a timescale and
        """

        # clear model file
        self.clear()

        # print header
        self.header()
        self.println()

        # set timescale
        self.timescale()
        self.println()

        # include real number library
        self.include('real.sv')
        self.println()

        # clear default nettype to make debugging easier
        self.default_nettype('none')
        self.println()

    def tmpvar(self, prefix='tmp'):
        """
        Returns a new variable name that doesn't conflict with any currently defined variables.
        """

        name = f'{prefix}{self.tmp_counter}'
        self.tmp_counter += 1

        while name in self.variable_names:
            name = f'{prefix}{self.tmp_counter}'
            self.tmp_counter += 1

        return name

    def header(self):
        self.comment(f'Model generated on {datetime.datetime.now()}')

    def timescale(self, unit='1ns', precision='1ps'):
        self.println(f'`timescale {unit}/{precision}')

    def include(self, file):
        self.println(f'`include "{file}"')

    def default_nettype(self, type):
        self.println(f'`default_nettype {type}')

    def macro_call(self, macro_name, *args):
        self.println(f"`{macro_name}({', '.join(args)});")

    def comment(self, content=''):
        self.println(f'// {content}')

    def comma_separated_lines(self, lines):
        if len(lines) == 0:
            pass
        else:
            self.println(lines[0] + (',' if len(lines) > 1 else ''))
            self.comma_separated_lines(lines[1:])

    def indent(self):
        self.tab_level += 1

    def dedent(self):
        self.tab_level -= 1
        assert self.tab_level >= 0

    def start_module(self, name, inputs, outputs):
        # set defaults
        if inputs is None:
            inputs = []
        if outputs is None:
            outputs = []

        # module name
        self.println(f'module {name} #(')

        # parameters
        self.indent()
        parameters = [self.decl_real(name) for name in inputs+outputs]
        self.comma_separated_lines(parameters)
        self.dedent()
        self.println(') (')

        # IO
        self.indent()
        ios = ['input wire logic clk', 'input wire logic rst']
        ios += [self.input_real(name) for name in inputs]
        ios += [self.output_real(name) for name in outputs]
        self.comma_separated_lines(ios)
        self.dedent()
        self.println(');')

        # set indentation level
        self.indent()

    def end_module(self):
        self.dedent()
        self.println('endmodule')
        self.println()
        self.default_nettype('wire')

    # file I/O operations

    def write(self, string='', mode='a'):
        with open(self.filename, mode) as f:
            f.write(string)

    def println(self, line=''):
        self.write(self.tab_level*self.tab_string + line + self.line_ending)

    def clear(self):
        self.write(mode='w')

    # formatting

    @staticmethod
    def real2str(value):
        return '{:0.10f}'.format(value)

    @staticmethod
    def decl_real(name):
        return f'`DECL_REAL({name})'

    @staticmethod
    def input_real(name):
        return f'`INPUT_REAL({name})'

    @staticmethod
    def output_real(name):
        return f'`OUTPUT_REAL({name})'