from typing import List
from numbers import Number
import datetime

from msdsl.generator import CodeGenerator
from msdsl.expr import (AnalogInput, AnalogOutput, DigitalInput, DigitalOutput, Signal, DigitalSignal, AnalogSignal,
                        Plus, Times, Constant, AnalogArray, BinaryOp, ListOp, LessThan, LessThanOrEquals, GreaterThan,
                        GreaterThanOrEquals, Concatenate, EqualTo, NotEqualTo, Min, Max)
from msdsl.util import tree_op

class VerilogGenerator(CodeGenerator):
    def __init__(self, filename, tab_string='    ', line_ending='\n'):
        super().__init__(filename=filename, tab_string=tab_string, line_ending=line_ending)

        # initialize model file
        self.init_file()

    #######################################################
    # implementation of abstract CodeGenerator interface

    def make_section(self, label):
        self.comment(label)

    def compile_expr(self, expr):
        if isinstance(expr, Number):
            return self.make_analog_const(expr)
        elif isinstance(expr, Signal):
            return expr
        elif isinstance(expr, Constant):
            return self.make_analog_const(expr.value)
        elif isinstance(expr, AnalogArray):
            # compile terms and address
            gen_terms = [self.compile_expr(term) for term in expr.terms]
            gen_addr = self.compile_expr(expr.addr)

            # implement the lookup table
            return self.make_analog_array(gen_terms, gen_addr)
        elif isinstance(expr, ListOp):
            # compile each term
            gen_terms = [self.compile_expr(term) for term in expr.terms]

            # determine the elementwise operations
            if isinstance(expr, Plus):
                op = lambda a, b: self.make_plus(a, b)
                default = lambda: self.make_analog_const(0)
            elif isinstance(expr, Times):
                op = lambda a, b: self.make_times(a, b)
                default = lambda: self.make_analog_const(1)
            elif isinstance(expr, Min):
                op = lambda a, b: self.make_min(a, b)
                default = lambda: self.make_analog_const(0)
            elif isinstance(expr, Max):
                op = lambda a, b: self.make_max(a, b)
                default = lambda: self.make_analog_const(0)
            else:
                raise Exception('Invalid ListOp type.')

            # implement operations in a tree
            return tree_op(gen_terms, op=op, default=default)
        elif isinstance(expr, BinaryOp):
            gen_lhs = self.compile_expr(expr.lhs)
            gen_rhs = self.compile_expr(expr.rhs)

            if isinstance(expr, LessThan):
                return self.make_less_than(gen_lhs, gen_rhs)
            elif isinstance(expr, LessThanOrEquals):
                return self.make_less_than_or_equals(gen_lhs, gen_rhs)
            elif isinstance(expr, GreaterThan):
                return self.make_greater_than(gen_lhs, gen_rhs)
            elif isinstance(expr, GreaterThanOrEquals):
                return self.make_greater_than_or_equals(gen_lhs, gen_rhs)
            elif isinstance(expr, EqualTo):
                return self.make_equal_to(gen_lhs, gen_rhs)
            elif isinstance(expr, NotEqualTo):
                return self.make_not_equal_to(gen_lhs, gen_rhs)
            else:
                raise Exception('Invalid BinaryOp type.')
        elif isinstance(expr, Concatenate):
            gen_terms = [self.compile_expr(term) for term in expr.terms]
            return self.make_concatenate(gen_terms)
        else:
            raise Exception('Invalid expression type.')

    def make_signal(self, s: Signal):
        if isinstance(s, AnalogSignal):
            if s.range is not None:
                self.macro_call('MAKE_REAL', s.name, self.real2str(s.range))
            elif s.copy_format_from is not None:
                self.macro_call('COPY_FORMAT_REAL', s.copy_format_from.name, s.name)
            else:
                raise Exception('Range not specified for signal.')
        elif isinstance(s, DigitalSignal):
            self.println(f'{VerilogGenerator.digital_type_string(s)} {s.name};')
        else:
            raise Exception('Invalid signal type.')

    def make_assign(self, input_: Signal, output: Signal):
        if isinstance(input_, AnalogSignal) and isinstance(output, AnalogSignal):
            self.macro_call('ASSIGN_REAL', input_.name, output.name)
        elif isinstance(input_, DigitalSignal) and isinstance(output, DigitalSignal):
            self.println(f'assign {input_.name} = {output.name};')
        else:
            raise Exception('Invalid signal type.')

    def make_mem(self, next: Signal, curr: Signal):
        if isinstance(next, AnalogSignal) and isinstance(curr, AnalogSignal):
            self.macro_call('MEM_INTO_ANALOG', next.name, curr.name, "1'b1", '0')
        elif isinstance(next, DigitalSignal) and isinstance(curr, DigitalSignal):
            assert next.width == curr.width
            self.macro_call('MEM_INTO_DIGITAL', next.name, curr.name, "1'b1", '0')
        else:
            raise Exception('Invalid signal type.')

    def start_module(self, name: str, ios: List[Signal]):
        # clear default nettype to make debugging easier
        self.default_nettype('none')
        self.println()

        # module name
        self.write(f'module {name}')

        # parameters
        parameters = [self.param_string(io) for io in ios if isinstance(io, (AnalogInput, AnalogOutput))]
        if len(parameters) > 0:
            self.write(' #')
            self.comma_separated_lines(parameters)

        # ports
        ports = [self.port_string(io) for io in ios]
        if len(ports) > 0:
            self.write(' ')
            self.comma_separated_lines(ports)

        # end module definition and indent
        self.write(';' + self.line_ending)
        self.indent()

    def end_module(self):
        self.dedent()
        self.println('endmodule')
        self.println()
        self.default_nettype('wire')

    #######################################################

    def make_bin_op(self, macro_name: str, a: Signal, b: Signal):
        name = self.tmp_name()

        if isinstance(a, AnalogSignal) and isinstance(b, AnalogSignal):
            self.macro_call(macro_name, a.name, b.name, name)
            return AnalogSignal(name)
        else:
            raise Exception('Invalid signal type.')

    def make_times(self, a: Signal, b: Signal):
        return self.make_bin_op('MUL_REAL', a, b)

    def make_plus(self, a: Signal, b: Signal):
        return self.make_bin_op('ADD_REAL', a, b)

    def make_min(self, a: Signal, b: Signal):
        return self.make_bin_op('MIN_REAL', a, b)

    def make_max(self, a: Signal, b: Signal):
        return self.make_bin_op('MAX_REAL', a, b)

    def make_analog_const(self, value: Number):
        name = self.tmp_name()
        self.macro_call('MAKE_CONST_REAL', self.real2str(value), name)
        return AnalogSignal(name)

    def make_less_than(self, lhs, rhs):
        return self.make_comp('LT_REAL', lhs, rhs)

    def make_less_than_or_equals(self, lhs, rhs):
        return self.make_comp('LE_REAL', lhs, rhs)

    def make_greater_than(self, lhs, rhs):
        return self.make_comp('GT_REAL', lhs, rhs)

    def make_greater_than_or_equals(self, lhs, rhs):
        return self.make_comp('GE_REAL', lhs, rhs)

    def make_equal_to(self, lhs, rhs):
        return self.make_comp('EQ_REAL', lhs, rhs)

    def make_not_equal_to(self, lhs, rhs):
        return self.make_comp('NE_REAL', lhs, rhs)

    def make_concatenate(self, terms: List[DigitalSignal]):
        # create the output signal
        width = sum(term.width for term in terms)
        out = DigitalSignal(self.tmp_name(), width=width)
        self.make_signal(out)

        # assign the output signal
        concat_string = '{' + ', '.join(term.name for term in terms) + '}'
        self.println(f'assign {out.name} = {concat_string};')

        return out

    def make_analog_array(self, values: List[AnalogSignal], addr: DigitalSignal):
        if len(values) == 0:
            raise Exception('Invalid table size.')
        elif len(values) == 1:
            return values[0]
        else:
            # declare the variable that will hold the result
            out = AnalogSignal(name=self.tmp_name())
            self.macro_call('MAKE_REAL', out.name, self.max_analog_range(values))

            # assign values to each entry in the table
            entries = []
            for k, value in enumerate(values):
                entry = out.copy_format_to(f'{out.name}_{k}')
                entries.append(entry)

                self.make_signal(entry)
                self.make_assign(value, entry)

            # create string entries for each case
            case_entries = [(k, f'{out.name} = {entry.name}') for k, entry in enumerate(entries)]
            self.always_begin('*')
            self.case_statement(addr.name, case_entries, default = f'{out.name} = 0')
            self.end()

            # return the variable
            return out

    def init_file(self):
        # clear model file
        self.clear()

        # print header
        self.comment(f'Model generated on {datetime.datetime.now()}')
        self.println()

        # set timescale
        self.println(f'`timescale 1ns/1ps')
        self.println()

        # include required libraries
        self.include('real.sv')
        self.include('math.sv')
        self.include('msdsl.sv')
        self.println()

    def make_comp(self, macro_name, lhs, rhs):
        name = self.tmp_name()
        self.macro_call(macro_name, lhs.name, rhs.name, name)
        return DigitalSignal(name)

    def include(self, file):
        self.println(f'`include "{file}"')

    def default_nettype(self, type):
        self.println(f'`default_nettype {type}')

    def macro_call(self, macro_name, *args):
        self.println(f"`{macro_name}({', '.join(args)});")

    def comment(self, content=''):
        self.println(f'// {content}')

    def comma_separated_lines(self, lines):
        self.write('(' + self.line_ending)
        self.write((',' + self.line_ending).join([self.tab_string + line for line in lines]))
        self.write(self.line_ending)
        self.write(')')

    @staticmethod
    def param_string(io):
        return f'`DECL_REAL({io.name})'

    @staticmethod
    def port_string(io):
        if isinstance(io, AnalogInput):
            return f'`INPUT_REAL({io.name})'
        elif isinstance(io, AnalogOutput):
            return f'`OUTPUT_REAL({io.name})'
        elif isinstance(io, DigitalInput):
            type_string = VerilogGenerator.digital_type_string(io)
            return f'input wire {type_string} {io.name}'
        elif isinstance(io, DigitalOutput):
            type_string = VerilogGenerator.digital_type_string(io)
            return f'output wire {type_string} {io.name}'
        else:
            raise Exception('Invalid type.')

    @staticmethod
    def digital_type_string(s: DigitalSignal):
        retval = 'logic'
        retval += ' signed' if s.signed else ''
        retval += f' [{s.width-1}:0]'

        return retval

    def always_begin(self, sensitivity):
        self.println(f'always @({sensitivity}) begin')
        self.indent()

    def case_statement(self, input_, case_entries, default=None):
        self.println(f'case ({input_})')
        self.indent()
        for k, action in case_entries:
            self.println(f'{k}: {action};')
        if default is not None:
            self.println(f'default: {default};')
        self.dedent()
        self.println('endcase')

    def end(self):
        self.dedent()
        self.println('end')

    @staticmethod
    def real2str(value):
        return '{:0.10f}'.format(value)

    @staticmethod
    def max_analog_range(values: List[AnalogSignal]):
        if len(values) == 0:
            return '0'
        elif len(values) == 1:
            return f'`RANGE_PARAM_REAL({values[0].name})'
        else:
            return f'`MAX_MATH(`RANGE_PARAM_REAL({values[0].name}), {VerilogGenerator.max_analog_range(values[1:])})'
