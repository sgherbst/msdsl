from typing import List
from numbers import Number
import datetime

from msdsl.generator.generator import CodeGenerator
from msdsl.expr.expr import (AnalogInput, AnalogOutput, DigitalInput, DigitalOutput, Signal, DigitalSignal, AnalogSignal,
                   Plus, Times, AnalogConstant, AnalogArray, BinaryOp, ListOp, LessThan, LessThanOrEquals, GreaterThan,
                   GreaterThanOrEquals, Concatenate, EqualTo, NotEqualTo, Min, Max, DigitalArray, ArrayOp,
                   BitwiseAnd, BitwiseInv, BitwiseOr, BitwiseXor, UnaryOp, DigitalConstant, DigitalCases,
                   CaseExpr, AnalogCases)
from msdsl.util import tree_op

class VerilogGenerator(CodeGenerator):
    def __init__(self, filename=None, tab_string='    ', line_ending='\n'):
        super().__init__(filename=filename, tab_string=tab_string, line_ending=line_ending)

        # initialize model file
        self.init_file()

    #######################################################
    # implementation of abstract CodeGenerator interface

    def make_section(self, label):
        self.comment(label)

    def compile_expr(self, expr, type_hint='analog'):
        if isinstance(expr, Number):
            return self.make_analog_const(expr)
        elif isinstance(expr, Signal):
            return expr
        elif isinstance(expr, AnalogConstant):
            return self.make_analog_const(expr.value)
        elif isinstance(expr, DigitalConstant):
            return self.make_digital_const(expr)
        elif isinstance(expr, CaseExpr):
            addr_bits = [self.compile_expr(case[0]) for case in expr.cases]
            unique_values = [self.compile_expr(case[1]) for case in expr.cases]

            terms = ...

            # check the array type
            if isinstance(expr, DigitalCases):
                array_cls = DigitalArray
            elif isinstance(expr, AnalogCases):
                array_cls = AnalogArray
            else:
                raise Exception(f'Invalid ArrayOp: {type(expr)}')

            return self.compile_expr(array_cls(terms=terms, addr=Concatenate(addr_bits)))
        elif isinstance(expr, ArrayOp):
            # compile address
            gen_addr = self.compile_expr(expr.addr) if expr.addr is not None else None

            # compile terms
            gen_terms = [self.compile_expr(term) for term in expr.terms]

            # update expression properties
            expr.addr = gen_addr
            expr.terms = gen_terms

            # implement the lookup table
            return self.make_array(expr)
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
        elif isinstance(expr, UnaryOp):
            gen_term = self.compile_expr(expr.term)

            if isinstance(expr, BitwiseInv):
                return self.make_bitwise_op('~', [gen_term])
            else:
                raise Exception('Invalid UnaryOp type.')
        elif isinstance(expr, BinaryOp):
            gen_lhs = self.compile_expr(expr.lhs)
            gen_rhs = self.compile_expr(expr.rhs)

            if isinstance(expr, BitwiseAnd):
                return self.make_bitwise_op('&', [gen_lhs, gen_rhs])
            elif isinstance(expr, BitwiseOr):
                return self.make_bitwise_op('|', [gen_lhs, gen_rhs])
            elif isinstance(expr, BitwiseXor):
                return self.make_bitwise_op('^', [gen_lhs, gen_rhs])
            elif isinstance(expr, LessThan):
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
            raise Exception(f'Invalid expression type: {type(expr)}')

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

    def make_probe(self, s: Signal):
        if isinstance(s, AnalogSignal):
            self.macro_call('PROBE_ANALOG', s.name)
        elif isinstance(s, DigitalSignal):
            self.macro_call('PROBE_DIGITAL', s.name, str(s.width))
        else:
            raise Exception('Invalid signal type.')

    def make_assign(self, input_: Signal, output: Signal):
        if isinstance(input_, AnalogSignal) and isinstance(output, AnalogSignal):
            self.macro_call('ASSIGN_REAL', input_.name, output.name)
        elif isinstance(input_, DigitalSignal) and isinstance(output, DigitalSignal):
            self.println(f'assign {output.name} = {input_.name};')
        else:
            raise Exception('Invalid signal type.')

    def make_mem(self, next: Signal, curr: Signal):
        if isinstance(next, AnalogSignal) and isinstance(curr, AnalogSignal):
            self.macro_call('MEM_INTO_ANALOG', next.name, curr.name, "1'b1", '0')
        elif isinstance(next, DigitalSignal) and isinstance(curr, DigitalSignal):
            assert next.width == curr.width
            self.macro_call('MEM_INTO_DIGITAL', next.name, curr.name, "1'b1", '0', str(next.width))
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

    def make_digital_const(self, digital_constant):
        name = self.tmp_name()
        self.println(f'{self.digital_type_string(digital_constant)} {name};')
        self.println(f'assign {name} = {str(digital_constant)};')
        return DigitalSignal(name, width=digital_constant.width)

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

    def make_array(self, array):
        if len(array.terms) == 0:
            raise Exception('Invalid table size.')
        elif len(array.terms) == 1:
            return array.terms[0]
        else:
            if isinstance(array, AnalogArray):
                out = AnalogSignal(name=self.tmp_name())
                range = str(array.analog_range) if array.analog_range is not None else self.max_analog_range(array.terms)
                self.macro_call('MAKE_REAL', out.name, range)

                # create a signal for each entry in the table that is aligned to the output format
                # this is important because the values may have varying binary points
                entries = []
                for k, value in enumerate(array.terms):
                    entry = out.copy_format_to(f'{out.name}_{k}')
                    entries.append(entry)

                    self.make_signal(entry)
                    self.make_assign(value, entry)
            elif isinstance(array, DigitalArray):
                # check term widths
                assert all(term.width == array.terms[0].width for term in array.terms[1:]), 'All terms in a DigitalArray must have the same width.'

                # make output signal
                out = DigitalSignal(name=self.tmp_name(), width=array.terms[0].width)
                self.make_signal(out)

                # for now, all values are assumed to have the same width so realignment is not required
                entries = array.terms
            else:
                raise Exception('Invalid signal type.')

            # create string entries for each case
            case_entries = [(k, f'{out.name} = {entry.name}') for k, entry in enumerate(entries)]
            self.always_begin('*')
            self.case_statement(array.addr.name, case_entries, default = f'{out.name} = 0')
            self.end()

            # return the variable
            return out

    def init_file(self):
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

    def make_bitwise_op(self, op, terms):
        # construct the expression
        if len(terms) == 1:
            value_str = f'{op}{terms[0]}'
        elif len(terms) == 2:
            value_str = f'{terms[0]}{op}{terms[1]}'
        else:
            raise Exception(f'Invalid number of terms for bitwise op: {len(terms)}')

        # declare output signal and assign its value
        result = DigitalSignal(self.tmp_name(), width=max(term.width for term in terms))
        self.println(f'{self.digital_type_string(result)} {result.name};')
        self.println(f'assign {result.name} = {value_str};')

        # return resulting signal
        return result

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

# sign = '-' if self.value < 0 else ''
# is_signed = 's' if self.signed else ''
# return f"{sign}{self.width}'{is_signed}d{abs(self.value)}"