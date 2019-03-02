from typing import List, Union
from numbers import Number
import datetime

from msdsl.generator.generator import CodeGenerator
from msdsl.expr.expr import ModelExpr, wrap_constant, ModelOperator, Constant, ArithmeticOperator, ComparisonOperator, \
    BitwiseOperator, Concatenate, Array, TypeConversion, SIntToReal, UIntToSInt, BitwiseInv
from msdsl.expr.format import UIntFormat, SIntFormat, RealFormat, IntFormat
from msdsl.expr.signals import Signal, AnalogSignal, DigitalSignal, AnalogInput, AnalogOutput, DigitalOutput, \
    DigitalInput
from msdsl.generator.tree_op import tree_op
from msdsl.generator.svreal import compile_range_expr, compile_width_expr, compile_exponent_expr
from msdsl.expr.analyze import signal_names, signal_name

BITWISE_OP = {
    'BitwiseInv': '~',
    'BitwiseAnd': '&',
    'BitwiseOr': '|',
    'BitwiseXor': '^'
}

INT_COMP_OP = {
    'LessThan': '<',
    'LessThanOrEquals': '<=',
    'GreaterThan': '>',
    'GreaterThanOrEquals': '>=',
    'EqualTo': '==',
    'NotEqualTo': '!='
}

REAL_COMP_OP = {
    'LessThan': 'LT_REAL',
    'LessThanOrEquals': 'LE_REAL',
    'GreaterThan': 'GT_REAL',
    'GreaterThanOrEquals': 'GE_REAL',
    'EqualTo': 'EQ_REAL',
    'NotEqualTo': 'NE_REAL'
}

REAL_ARITH_OP = {
    'Sum': 'ADD_REAL',
    'Product': 'MUL_REAL',
    'Min': 'MIN_REAL',
    'Max': 'MAX_REAL'
}

INT_ARITH_OP = {
    'Sum':     lambda a, b: f'({a}+{b})',
    'Product': lambda a, b: f'({a}*{b})',
    'Min':     lambda a, b: f'(({a} < {b}) ? {a} : {b})',
    'Max':     lambda a, b: f'(({a} > {b}) ? {a} : {b})'
}

class VerilogGenerator(CodeGenerator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_file()

    #######################################################
    # implementation of abstract CodeGenerator interface

    def make_section(self, label):
        self.comment(label)

    def expr_to_signal(self, expr: ModelExpr):
        # wrap number as constant if needed
        expr = wrap_constant(expr)

        # handle expression
        if isinstance(expr, Signal):
            return expr
        elif isinstance(expr, Constant):
            return self.handle_constant(expr=expr)
        elif isinstance(expr, ArithmeticOperator):
            operands = [self.expr_to_signal(operand) for operand in expr.operands]
            return self.make_arithmetic_operator(expr=expr, operands=operands)
        elif isinstance(expr, BitwiseIv)
        elif isinstance(expr, BitwiseOperator):
            return self.make_bitwise_operator(expr=expr, operands=operands)
        elif isinstance(expr, ComparisonOperator):
            return self.make_comparison_operator(expr=expr, operands=operands)
        elif isinstance(expr, Concatenate):
            return self.make_concatenation(expr=expr, operands=operands)
        elif isinstance(expr, Array):
            return self.make_array(expr=expr, operands=operands)
        elif isinstance(expr, TypeConversion):
            return self.make_type_conversion(expr=expr, operands=operands)
        else:
            raise Exception(f'Unknown expression type: {type(expr)}')

    def make_signal(self, s: Signal):
        if isinstance(s.format, RealFormat):
            # compile the range, width, and exponent expressions
            range = compile_range_expr(s.format.range)
            width = compile_width_expr(s.format.width)
            exponent = compile_exponent_expr(s.format.exponent)

            # call the appropriate macro
            if width is None:
                self.macro_call('MAKE_REAL', s.name, range)
            elif exponent is None:
                self.macro_call('MAKE_GENERIC_REAL', s.name, range, width)
            else:
                self.macro_call('MAKE_FORMAT_REAL', s.name, range, width, exponent)
        elif isinstance(s.format, IntFormat):
            self.writeln(f'{self.int_type_str(s.format)} {s.name};')
        else:
            raise Exception('Invalid signal type.')

    def make_probe(self, s: Signal):
        if isinstance(s, AnalogSignal):
            self.macro_call('PROBE_ANALOG', s.name)
        elif isinstance(s, DigitalSignal):
            self.macro_call('PROBE_DIGITAL', s.name, str(s.format.width))
        else:
            raise Exception('Invalid signal type.')

    def make_assign(self, input_: Signal, output: Signal):
        if isinstance(input_.format, RealFormat) and isinstance(output.format, RealFormat):
            self.macro_call('ASSIGN_REAL', input_.name, output.name)
        elif (isinstance(input_.format, SIntFormat) and isinstance(output.format, SIntFormat)) or \
             (isinstance(input_.format, UIntFormat) and isinstance(output.format, UIntFormat)):
            self.writeln(f'assign {output.name} = {input_.name};')
        else:
            raise Exception(f'Input and output formats do not match: {input_.format} vs. {output.format}')

    def make_mem(self, next_: Signal, curr: Signal, init: Number=0):
        # create memory for real number
        if isinstance(next_.format, RealFormat) and isinstance(curr.format, RealFormat):
            self.macro_call('MEM_INTO_ANALOG', next_.name, curr.name, "1'b1", str(init))
        # create memory for integer
        elif (isinstance(next_.format, SIntFormat) and isinstance(curr.format, SIntFormat)) or \
             (isinstance(next_.format, UIntFormat) and isinstance(curr.format, UIntFormat)):
            # check that initial value is valid
            assert (curr.format.min_val <= init <= curr.format.max_val), \
                f'Initial value {init} does not fit in the range [{curr.format.min_val}, {curr.format.max_val}] of signal {curr.name}.'

            # check that the widths match
            assert next_.format.width == curr.format.width, f'The widths of {next_.name} and {curr.name} do not match.'

            self.macro_call('MEM_INTO_DIGITAL', next_.name, curr.name, "1'b1", str(init), str(next_.format.width))
        else:
            raise Exception(f'Next and current formats do not match: {next_.format} vs. {curr.format}')

    def start_module(self, name: str, ios: List[Signal]):
        # clear default nettype to make debugging easier
        self.default_nettype('none')
        self.writeln()

        # module name
        self.write(f'module {name}')

        # parameters
        parameters = [self.real_param_str(io) for io in ios if isinstance(io.format, RealFormat)]
        if len(parameters) > 0:
            self.write(' #')
            self.comma_separated_lines(parameters)

        # ports
        ports = [self.port_str(io) for io in ios]
        if len(ports) > 0:
            self.write(' ')
            self.comma_separated_lines(ports)

        # end module definition and indent
        self.write(';' + self.line_ending)
        self.indent()

    def end_module(self):
        self.dedent()
        self.writeln('endmodule')
        self.writeln()
        self.default_nettype('wire')

    #######################################################

    def handle_constant(self, expr):
        name = next(self.namer)

        if isinstance(expr.format, RealFormat):
            # compile the range, width, and exponent expressions
            const = str(expr.value)
            range = compile_range_expr(expr.format.range)
            width = compile_width_expr(expr.format.width)
            exponent = compile_exponent_expr(expr.format.exponent)

            # call the appropriate macro
            if width is None:
                self.macro_call('MAKE_CONST_REAL', const, name)
            elif exponent is None:
                self.macro_call('MAKE_GENERIC_CONST_REAL', const, name, width)
            else:
                self.macro_call('MAKE_FORMAT_REAL', name, range, width, exponent)
                self.macro_call('ASSIGN_CONST_REAL', const, name)
        elif isinstance(expr.format, IntFormat):
            self.decl_digital(fmt=expr.format, name=name)
            self.assign_digital(name=name, value=expr.value)
        else:
            raise ValueError(f'Unknown expression format type: ' + expr.format.__class__.__name__)

        return Signal(name=name, format=expr.format)

    def make_arithmetic_operator(self, expr, operands):
        pass

    def make_bitwise_operator(self, expr, operands):
        op = BITWISE_OP[expr.__class__.__name__]

        if op == '~':
            assert len(operands) == 1, 'Bitwise inversion can only be applied to one operand.'
            value = f'~{signal_name(operands[0])}'
        else:
            value = op.join(signal_names(operands))

        name = next(self.namer)
        self.decl_digital(fmt=expr.format, name=name)
        self.assign_digital(name=name, value=value)

        return Signal(name=name, format=expr.format)

    def make_comparison_operator(self, expr, operands):
        name = next(self.namer)
        self.decl_digital(fmt=expr.format, name=name)

        lhs = operands[0]
        rhs = operands[1]
        assert len(operands) == 2, 'Comparison operation must have exactly two operands.'

        if isinstance(lhs.format, RealFormat):
            op = REAL_COMP_OP[expr.__class__.__name__]
            self.macro_call(op, lhs, rhs, name)
        elif isinstance(lhs.format, IntFormat):
            op = INT_COMP_OP[expr.__class__.__name__]
            self.assign_digital(name, f'{lhs} {op} {rhs}')
        else:
            raise ValueError(f'Unknown LHS format type: ' + lhs.format.__class__.__name__)

        return Signal(name=name, format=expr.format)

    def make_concatenation(self, expr, operands):
        value = '{' + ', '.join(signal_names(operands)) + '}'

        name = next(self.namer)
        self.decl_digital(fmt=expr.format, name=name)
        self.assign_digital(name=name, value=value)

        return Signal(name=name, format=expr.format)

    def make_array(self, expr, operands):
        pass

    def make_type_conversion(self, expr, operands):
        name = next(self.namer)

        operand = operands[0]
        assert len(operands) == 1, 'Type conversion must have exactly one operand.'

        if isinstance(expr, SIntToReal):
            self.macro_call('INT_TO_REAL', operand, operand.format.width, name)
        elif isinstance(expr, UIntToSInt):
            self.decl_digital(fmt=expr.format, name=name)
            self.assign_digital(name=name, value="{1'b0, " + signal_name(operand) + "}")
        else:
            raise ValueError(f'Unknown type conversion: ' + expr.__class__.__name__)

        return Signal(name=name, format=expr.format)

    def init_file(self):
        # print header
        self.comment(f'Model generated on {datetime.datetime.now()}')
        self.writeln()

        # set timescale
        self.writeln(f'`timescale 1ns/1ps')
        self.writeln()

        # include required libraries
        self.include('real.sv')
        self.include('math.sv')
        self.include('msdsl.sv')
        self.writeln()

    def include(self, file):
        self.writeln(f'`include "{file}"')

    def default_nettype(self, type):
        self.writeln(f'`default_nettype {type}')

    def macro_call(self, macro_name, *args):
        self.writeln(f"`{macro_name}({', '.join(args)});")

    def comment(self, content=''):
        self.writeln(f'// {content}')

    def comma_separated_lines(self, lines):
        self.write('(' + self.line_ending)
        self.write((',' + self.line_ending).join([self.tab_string + line for line in lines]))
        self.write(self.line_ending)
        self.write(')')

    def decl_digital(self, fmt: Union[SIntFormat, UIntFormat], name):
        self.writeln(f'{self.int_type_str(fmt)} {name};')

    def assign_digital(self, name, value):
        self.writeln(f'assign {name} = {value};')

    @staticmethod
    def real_param_str(io):
        return f'`DECL_REAL({io.name})'

    @classmethod
    def port_str(cls, io):
        if isinstance(io, AnalogInput):
            return f'`INPUT_REAL({io.name})'
        elif isinstance(io, AnalogOutput):
            return f'`OUTPUT_REAL({io.name})'
        elif isinstance(io, DigitalInput):
            return f'input wire {cls.int_type_str(io)} {io.name}'
        elif isinstance(io, DigitalOutput):
            return f'output wire {cls.int_type_str(io)} {io.name}'
        else:
            raise Exception('Invalid type.')

    @staticmethod
    def int_type_str(fmt: Union[SIntFormat, UIntFormat]):
        retval = 'logic'

        if isinstance(fmt, UIntFormat):
            pass
        elif isinstance(fmt, SIntFormat):
            retval += ' signed'
        else:
            raise Exception('Cannot determine if format is signed or unsigned.')

        retval += f' [{fmt.width-1}:0]'

        return retval

    @staticmethod
    def real2str(value):
        return '{:0.10f}'.format(value)

    # if len(array.terms) == 0:
    #     raise Exception('Invalid table size.')
    # elif len(array.terms) == 1:
    #     return array.terms[0]
    # else:
    #     if isinstance(array, AnalogArray):
    #         out = AnalogSignal(name=self.tmp_name())
    #         range = str(array.analog_range) if array.analog_range is not None else self.max_analog_range(array.terms)
    #         self.macro_call('MAKE_REAL', out.name, range)
    #
    #         # create a signal for each entry in the table that is aligned to the output format
    #         # this is important because the values may have varying binary points
    #         entries = []
    #         for k, value in enumerate(array.terms):
    #             entry = out.copy_format_to(f'{out.name}_{k}')
    #             entries.append(entry)
    #
    #             self.make_signal(entry)
    #             self.make_assign(value, entry)
    #     elif isinstance(array, DigitalArray):
    #         # check term widths
    #         assert all(term.width == array.terms[0].width for term in
    #                    array.terms[1:]), 'All terms in a DigitalArray must have the same width.'
    #
    #         # make output signal
    #         out = DigitalSignal(name=self.tmp_name(), width=array.terms[0].width)
    #         self.make_signal(out)
    #
    #         # for now, all values are assumed to have the same width so realignment is not required
    #         entries = array.terms
    #     else:
    #         raise Exception('Invalid signal type.')
    #
    #     # create string entries for each case
    #     case_entries = [(k, f'{out.name} = {entry.name}') for k, entry in enumerate(entries)]
    #     self.always_begin('*')
    #     self.case_statement(array.addr.name, case_entries, default=f'{out.name} = 0')
    #     self.end()
    #
    #     # return the variable
    #     return out

