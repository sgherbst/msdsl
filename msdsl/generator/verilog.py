from typing import List, Union
from numbers import Number, Integral
from math import ceil, log2
import datetime

from msdsl.generator.generator import CodeGenerator
from msdsl.expr.expr import ModelExpr, wrap_constant, ModelOperator, Constant, ArithmeticOperator, ComparisonOperator, \
    BitwiseOperator, Concatenate, Array, TypeConversion, SIntToReal, UIntToSInt, BitwiseInv, ArithmeticShift, \
    BitwiseAccess, RealToSInt, SIntToUInt, BitwiseAnd, BitwiseOr, BitwiseXor, ArithmeticRightShift, \
    ArithmeticLeftShift, LessThan, LessThanOrEquals, GreaterThan, GreaterThanOrEquals, EqualTo, NotEqualTo, \
    Sum, Product, Min, Max
from msdsl.expr.table import Table, RealTable, UIntTable, SIntTable
from msdsl.expr.format import UIntFormat, SIntFormat, RealFormat, IntFormat
from msdsl.expr.signals import Signal, AnalogSignal, DigitalSignal, AnalogInput, AnalogOutput, DigitalOutput, \
    DigitalInput, DigitalParameter, RealParameter
from msdsl.generator.tree_op import tree_op
from msdsl.generator.svreal import compile_range_expr, compile_width_expr, compile_exponent_expr
from msdsl.expr.analyze import signal_names, signal_name
from msdsl.generator.case_statement import case_statment

BITWISE_OP = {
    BitwiseAnd: '&',
    BitwiseOr: '|',
    BitwiseXor: '^'
}

SHIFT_OP = {
    ArithmeticLeftShift: '<<<',
    ArithmeticRightShift: '>>>'
}

INT_COMP_OP = {
    LessThan: '<',
    LessThanOrEquals: '<=',
    GreaterThan: '>',
    GreaterThanOrEquals: '>=',
    EqualTo: '==',
    NotEqualTo: '!='
}

REAL_COMP_OP = {
    LessThan: 'LT_REAL',
    LessThanOrEquals: 'LE_REAL',
    GreaterThan: 'GT_REAL',
    GreaterThanOrEquals: 'GE_REAL',
    EqualTo: 'EQ_REAL',
    NotEqualTo: 'NE_REAL'
}

REAL_ARITH_OP = {
    Sum: 'ADD_REAL',
    Product: 'MUL_REAL',
    Min: 'MIN_REAL',
    Max: 'MAX_REAL'
}

INT_ARITH_OP = {
    Sum:     lambda a, b: f'({a}+{b})',
    Product: lambda a, b: f'({a}*{b})',
    Min:     lambda a, b: f'(({a} < {b}) ? {a} : {b})',
    Max:     lambda a, b: f'(({a} > {b}) ? {a} : {b})'
}

class VerilogGenerator(CodeGenerator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_file()

    def make_section(self, label):
        self.comment(label)

    def expr_to_signal(self, expr: ModelExpr):
        # before starting, make sure that the expression is wrapped in case it is a number
        expr = wrap_constant(expr)

        if isinstance(expr, Signal):
            return expr
        elif isinstance(expr, Constant):
            return self.make_constant(expr)
        elif isinstance(expr, ArithmeticOperator):
            return self.make_arithmetic_operator(expr)
        elif isinstance(expr, BitwiseInv):
            return self.make_bitwise_inv(expr)
        elif isinstance(expr, BitwiseOperator):
            return self.make_bitwise_operator(expr)
        elif isinstance(expr, ComparisonOperator):
            return self.make_comparison_operator(expr)
        elif isinstance(expr, Concatenate):
            return self.make_concatenation(expr)
        elif isinstance(expr, Array):
            return self.make_array(expr)
        elif isinstance(expr, ArithmeticShift):
            return self.make_arithmetic_shift(expr)
        elif isinstance(expr, BitwiseAccess):
            return self.make_bitwise_access(expr)
        elif isinstance(expr, TypeConversion):
            return self.make_type_conversion(expr)
        else:
            raise Exception(f'Unknown expression type: {expr.__class__.__name__}')

    def make_signal(self, signal: Signal):
        if isinstance(signal.format_, RealFormat):
            # compile the range, width, and exponent expressions
            range = compile_range_expr(signal.format_.range_)
            width = compile_width_expr(signal.format_.width)
            exponent = compile_exponent_expr(signal.format_.exponent)

            # call the appropriate macro
            if width is None:
                self.macro_call('MAKE_REAL', signal.name, range)
            elif exponent is None:
                self.macro_call('MAKE_GENERIC_REAL', signal.name, range, width)
            else:
                self.macro_call('MAKE_FORMAT_REAL', signal.name, range, width, exponent)
        elif isinstance(signal.format_, IntFormat):
            self.writeln(f'{self.int_type_str(signal.format_)} {signal.name};')
        else:
            raise Exception('Invalid signal type.')

    def make_probe(self, s: Signal):
        if isinstance(s, Signal) and isinstance(s.format_, RealFormat):
            self.macro_call('PROBE_ANALOG', s.name)
        elif isinstance(s, Signal) and isinstance(s.format_, IntFormat):
            self.macro_call('PROBE_DIGITAL', s.name, str(s.format_.width))
        else:
            raise Exception('Invalid signal type.')

    def make_assign(self, input_: Signal, output: Signal):
        if isinstance(input_.format_, RealFormat) and isinstance(output.format_, RealFormat):
            self.macro_call('ASSIGN_REAL', input_.name, output.name)
        elif (isinstance(input_.format_, SIntFormat) and isinstance(output.format_, SIntFormat)) or \
             (isinstance(input_.format_, UIntFormat) and isinstance(output.format_, UIntFormat)):
            self.digital_assignment(signal=output, value=input_.name)
        else:
            raise Exception(f'Input and output formats do not match: {input_.name} with {input_.format_} vs. {output.name} with {output.format_}')

    def make_mem(self, next_: Signal, curr: Signal, init: Union[Number, DigitalParameter, RealParameter]=0,
                 clk: Signal=None, rst: Signal=None, ce: Signal = None):
        # set defaults
        clk_name = clk.name if clk is not None else '`CLK_MSDSL'

        # determine name of reset signal
        if rst is None:
            rst_name = '`RST_MSDSL'
        elif isinstance(rst, str):
            rst_name = rst
        else:
            rst_name = rst.name

        ce_name = ce.name if ce is not None else "1'b1"

        # create memory for real number
        if isinstance(next_.format_, RealFormat) and isinstance(curr.format_, RealFormat):
            # determine string expression for the initial value
            if isinstance(init, Number):
                init_str = str(init)
            elif isinstance(init, RealParameter):
                init_str = init.param_name
            elif isinstance(init, str):
                init_str = init
            else:
                raise Exception(f'Could not determine string representation for initial value {init}')

            # call the macro to create the memory
            self.macro_call('DFF_INTO_REAL', next_.name, curr.name, rst_name, clk_name, ce_name, init_str)
        # create memory for integer
        elif (isinstance(next_.format_, SIntFormat) and isinstance(curr.format_, SIntFormat)) or \
             (isinstance(next_.format_, UIntFormat) and isinstance(curr.format_, UIntFormat)):
            # check that initial value is valid, if it's number. range checking for DigitalParameters is not
            # yet implemented
            if isinstance(init, Number):
                assert (curr.format_.min_val <= init <= curr.format_.max_val), \
                    f'Initial value {init} does not fit in the range [{curr.format_.min_val}, {curr.format_.max_val}] of signal {curr.name}.'
            else:
                print(f'Warning: could not validate range of init value {init}')

            # check that the widths of next_ and curr match
            assert next_.format_.width == curr.format_.width, f'The widths of {next_.name} ({next_.format_.width}) does not match the width of {curr.name} ({curr.format_.width}).'

            # determine string expression for the initial value
            if isinstance(init, Number):
                init_str = str(init)
            elif isinstance(init, DigitalParameter):
                init_str = init.name
            elif isinstance(init, str):
                init_str = init
            else:
                raise Exception(f'Could not determine string representation for initial value {init}')

            # call the macro to create the memory
            self.macro_call('MEM_INTO_DIGITAL', next_.name, curr.name, ce_name, clk_name, rst_name, init_str,
                            str(next_.format_.width))
        else:
            raise Exception(f'Next and current formats do not match: {next_.name} with {next_.format_} vs. {curr.name} with {curr.format_}')

    def make_sync_rom(self, signal: Signal, table: Table, addr: Signal,
                      clk: Signal=None, ce: Signal=None):
        # set defaults
        clk_name = clk.name if clk is not None else "`CLK_MSDSL"
        ce_name = ce.name if ce is not None else "1'b1"

        if isinstance(table, RealTable):
            self.macro_call('SYNC_ROM_INTO_REAL', addr.name, signal.name, clk_name,
                            ce_name, table.addr_bits, table.width, f'"{table.path}"',
                            table.exp)
        elif isinstance(table, SIntTable):
            self.macro_call('SYNC_ROM_INTO_SINT', addr.name, signal.name, clk_name,
                            ce_name, table.addr_bits, table.width, f'"{table.path}"')
        elif isinstance(table, UIntTable):
            self.macro_call('SYNC_ROM_INTO_UINT', addr.name, signal.name, clk_name,
                            ce_name, table.addr_bits, table.width, f'"{table.path}"')
        else:
            raise Exception(f'Unknown table type: {type(table)}')

    def make_sync_ram(self, signal: AnalogSignal, format_: RealFormat, addr: DigitalSignal,
                      clk: DigitalSignal=None, ce: DigitalSignal=None, we: DigitalSignal=None,
                      din: DigitalSignal=None):
        # set defaults
        din_name = din.name if din is not None else "'0"
        clk_name = clk.name if clk is not None else "`CLK_MSDSL"
        ce_name = ce.name if ce is not None else "1'b1"
        we_name = we.name if we is not None else "1'b0"

        # call the SVREAL macro
        self.macro_call('SYNC_RAM_INTO_REAL', addr.name, din_name, signal.name,
                        clk_name, ce_name, we_name, addr.format_.width, format_.width,
                        format_.exponent)

    def start_module(self, name: str, ios: List[Signal], real_params: List, digital_params: List=None):
        # set defaults
        if digital_params is None:
            digital_params = []

        # clear default nettype to make debugging easier
        self.default_nettype('none')
        self.writeln()

        # module name
        self.write(f'module {name}')

        # parameters
        parameters = []
        parameters += [f'parameter real {real_param.param_name}={real_param.default}' for real_param in real_params]
        for dig_param in digital_params:
            dig_param_str = 'parameter '
            if dig_param.signed:
                dig_param_str += 'signed '
            if dig_param.width > 1:
                dig_param_str += f'[{dig_param.width-1}:0] '
            dig_param_str += f'{dig_param.name}={dig_param.default}'
            parameters += [dig_param_str]
        parameters += [self.real_param_str(io) for io in ios if isinstance(io.format_, RealFormat)]
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

        # assign parameters to constants
        if len(real_params) > 0:
            self.comment('Assign real parameters to constant wires')
        for real_param in real_params:
            self.macro_call('MAKE_CONST_REAL', real_param.param_name, real_param.signal_name)

    def end_module(self):
        self.dedent()
        self.writeln('endmodule')
        self.writeln()
        self.default_nettype('wire')

    def make_constant(self, expr: Constant):
        output = Signal(name=next(self.namer), format_=expr.format_)

        if isinstance(expr.format_, RealFormat):
            # compile the range, width, and exponent expressions.
            if isinstance(expr.value, Integral):
                # avoid a synthesis corner-case:
                # https://forums.xilinx.com/t5/Synthesis/Possible-synthesis-bug-casting-integer-to-real-in-a-function/td-p/1140910
                const = str(float(expr.value))
            else:
                const = str(expr.value)
            range = compile_range_expr(expr.format_.range_)
            width = compile_width_expr(expr.format_.width)
            exponent = compile_exponent_expr(expr.format_.exponent)

            # call the appropriate macro
            if width is None:
                self.macro_call('MAKE_CONST_REAL', const, output.name)
            elif exponent is None:
                self.macro_call('MAKE_GENERIC_CONST_REAL', const, output.name, width)
            else:
                self.macro_call('MAKE_FORMAT_REAL', output.name, range, width, exponent)
                self.macro_call('ASSIGN_CONST_REAL', const, output.name)
        elif isinstance(expr.format_, IntFormat):
            self.make_signal(output)
            self.digital_assignment(output, expr.value)
        else:
            raise ValueError(f'Unknown expression format type: ' + expr.format_.__class__.__name__)

        return output

    def make_arithmetic_operator(self, expr: ArithmeticOperator):
        # first check for some special cases involving multiplication.  this is an attempt to get most multiplications
        # to consume only one DSP
        if isinstance(expr, Product) and (len(expr.operands) == 2) and isinstance(expr.format_, RealFormat):
            if isinstance(expr.operands[0], Constant) or isinstance(expr.operands[1], Constant):
                return self.make_constant_mul_signal(expr=expr)
            elif (isinstance(expr.operands[0], Array) and expr.operands[0].all_constants) or \
                 (isinstance(expr.operands[1], Array) and expr.operands[1].all_constants):
                return self.make_constant_array_mul_signal(expr=expr)

        # compile the inputs to signals
        inputs_ = [self.expr_to_signal(operand) for operand in expr.operands]

        # define the operator used to build up the expression.  it takes two signals as arguments and returns
        # a signal bound to the result
        def operator(a, b):
            # determine the parameters of the output signal
            name = next(self.namer)
            format_ = expr.function(a.format_, b.format_)

            # create the output signal
            c = Signal(name=name, format_=format_)

            # assign the result
            if isinstance(expr.format_, RealFormat):
                self.macro_call(REAL_ARITH_OP[type(expr)], a.name, b.name, c.name)
            elif isinstance(expr.format_, IntFormat):
                self.make_signal(c)
                value = INT_ARITH_OP[type(expr)](a.name, b.name)
                self.digital_assignment(signal=c, value=value)
            else:
                raise Exception(f'Unknown expression format type: {expr.format_.__class__.__name__}')

            # return the output signal
            return c

        # apply the operator in a tree-wise fashion
        output = tree_op(operands=inputs_, operator=operator)

        # return the resulting signal
        return output

    def make_constant_mul_signal(self, expr: Product):
        # figure out which operand is the constant and which is the signal (note: if both are constants, that is
        # not handled in a special fashion.  although that shouldn't usually occur due to the way that expressions
        # are built up.)
        if isinstance(expr.operands[0], Constant):
            constant = expr.operands[0]
            signal = self.expr_to_signal(expr.operands[1])
        elif isinstance(expr.operands[1], Constant):
            constant = expr.operands[1]
            signal = self.expr_to_signal(expr.operands[0])
        else:
            raise Exception(f'This expression does not represent a constant times a signal: {expr}.')

        # create the output signal
        output = Signal(name=next(self.namer), format_=expr.format_)

        # call the special multiplication macro, avoiding a synthesis corner-case:
        # https://forums.xilinx.com/t5/Synthesis/Possible-synthesis-bug-casting-integer-to-real-in-a-function/td-p/1140910
        if isinstance(constant.value, Integral):
            # avoid a synthesis corner-case:
            # https://forums.xilinx.com/t5/Synthesis/Possible-synthesis-bug-casting-integer-to-real-in-a-function/td-p/1140910
            const_as_str = str(float(constant.value))
        else:
            const_as_str = str(constant.value)
        self.macro_call('MUL_CONST_REAL', const_as_str, signal.name, output.name)

        # return the output signal
        return output

    def make_constant_array_mul_signal(self, expr: Product):
        # figure out which operand is the constant array and which is the signal (note: if both are constant arrays,
        # that is not handled in a special fashion.  although that shouldn't usually occur due to the way that
        # expressions are built up.)
        if isinstance(expr.operands[0], Array) and expr.operands[0].all_constants:
            constant_array = expr.operands[0]
            signal = self.expr_to_signal(expr.operands[1])
        elif isinstance(expr.operands[1], Array) and expr.operands[1].all_constants:
            constant_array = expr.operands[1]
            signal = self.expr_to_signal(expr.operands[0])
        else:
            raise Exception(f'This expression does not represent a constant array times a signal: {expr}.')

        # create the output signal
        output = Signal(name=next(self.namer), format_=expr.format_)

        # create a short real variable to be assigned the selected value from the array
        array_name = next(self.namer)
        self.macro_call('MAKE_SHORT_REAL', array_name, compile_range_expr(constant_array.format_.range_))

        # perform the multiplication
        self.macro_call('MUL_REAL', array_name, signal.name, output.name)

        # compile the array address to a signal
        address = self.expr_to_signal(constant_array.address)

        # compute the valuess to go in the array
        values = [f'`FROM_REAL({element.value}, {array_name})' for element in constant_array.elements]

        # create the array itself
        case_statment(gen=self, sel=address.name, var=array_name, values=values, default=0)

        # return the output signal
        return output

    def make_array(self, expr: Array):
        # make the output signal that will hold the results
        output = Signal(name=next(self.namer), format_=expr.format_)
        self.make_signal(output)

        # compile the array elements and address to signals
        elements = [self.expr_to_signal(element) for element in expr.elements]
        address  = self.expr_to_signal(expr.address)

        # extra step for analog signals -- they must be aligned to the output format
        if isinstance(expr.format_, RealFormat):
            # rename the elements list to indicate these values are not aligned to the output format
            non_aligned_elements = elements

            # created an "aligned" version of each signal
            elements = [Signal(name=next(self.namer), format_=expr.format_) for _ in range(len(expr))]
            for element, non_aligned_element in zip(elements, non_aligned_elements):
                self.make_signal(element)
                self.make_assign(input_=non_aligned_element, output=element)

        # now create the array
        case_statment(gen=self, sel=address.name, var=output.name, values=signal_names(elements), default=0)

        # and last return the output signal
        return output

    def make_bitwise_inv(self, expr: BitwiseInv):
        output = Signal(name=next(self.namer), format_=expr.format_)
        self.make_signal(output)

        input_ = self.expr_to_signal(expr.operand)
        value = f'~{input_.name}'
        self.digital_assignment(signal=output, value=value)

        return output

    def make_bitwise_operator(self, expr: BitwiseOperator):
        output = Signal(name=next(self.namer), format_=expr.format_)
        self.make_signal(output)

        inputs = [self.expr_to_signal(operand) for operand in expr.operands]
        value = BITWISE_OP[type(expr)].join(signal_names(inputs))
        self.digital_assignment(signal=output, value=value)

        return output

    def make_comparison_operator(self, expr: ComparisonOperator):
        output = Signal(name=next(self.namer), format_=expr.format_)

        lhs = self.expr_to_signal(expr.lhs)
        rhs = self.expr_to_signal(expr.rhs)

        if isinstance(lhs.format_, RealFormat) and isinstance(rhs.format_, RealFormat):
            self.macro_call(REAL_COMP_OP[type(expr)], lhs.name, rhs.name, output.name)
        elif isinstance(lhs.format_, IntFormat) and isinstance(rhs.format_, IntFormat):
            # make the output signal
            self.make_signal(output)

            # assign the output signal
            value = f"({lhs} {INT_COMP_OP[type(expr)]} {rhs}) ? 1'b1 : 1'b0"
            self.digital_assignment(signal=output, value=value)
        else:
            raise ValueError(f'Unknown format type combination for LHS and RHS: {lhs.format_.__class__.__name__} and {rhs.format_.__class__.__name__}.')

        return output

    def make_concatenation(self, expr: Concatenate):
        output = Signal(name=next(self.namer), format_=expr.format_)
        self.make_signal(output)

        inputs_ = [self.expr_to_signal(operand) for operand in expr.operands]
        value = '{' + ', '.join(signal_names(inputs_)) + '}'
        self.digital_assignment(signal=output, value=value)

        return output

    def make_arithmetic_shift(self, expr: ArithmeticShift):
        output = Signal(name=next(self.namer), format_=expr.format_)
        self.make_signal(output)

        input_ = self.expr_to_signal(expr.operand)
        value = f'{input_.name} {SHIFT_OP[type(expr)]} {expr.shift}'
        self.digital_assignment(signal=output, value=value)

        return output

    def make_bitwise_access(self, expr: BitwiseAccess):
        output = Signal(name=next(self.namer), format_=expr.format_)
        self.make_signal(output)

        input_ = self.expr_to_signal(expr.operand)
        value = f'{input_.name}[{expr.msb}:{expr.lsb}]'
        self.digital_assignment(signal=output, value=value)

        return output

    def make_type_conversion(self, expr: TypeConversion):
        # make the output signal
        output = Signal(name=next(self.namer), format_=expr.format_)

        # compile the input expression to a signal
        input_ = self.expr_to_signal(expr.operand)

        # handle the various cases
        if isinstance(expr, SIntToReal):
            self.macro_call('INT_TO_REAL', input_.name, str(input_.format_.width), output.name)
        elif isinstance(expr, RealToSInt):
            self.macro_call('REAL_TO_INT', input_.name, str(output.format_.width), output.name)
        elif isinstance(expr, UIntToSInt):
            # sanity check
            assert output.format_.width >= input_.format_.width+1, \
                f'Output SInt width ({output.format_.width}) is not at least one greater than the input UInt width ({input_.format_.width}).'

            # make the output signal
            self.make_signal(output)

            # construct string representation of new SInt
            num_zeros = output.format_.width - input_.format_.width
            value = f'{{{self.zero_const(num_zeros)}, {input_.name}}}'

            # make the assignment
            self.digital_assignment(signal=output, value=value, comment='UInt -> SInt')
        elif isinstance(expr, SIntToUInt):
            # sanity check
            assert output.format_.width >= input_.format_.width-1, \
                f'Output UInt width ({output.format_.width}) is not at least one less than the input SInt width ({input_.format_.width}).'

            # make the output signal
            self.make_signal(output)

            # then trim off the sign bit
            value = f'{input_.name}[{input_.format_.width-2}:0]'

            # pad with zeros if necessary
            num_zeros = output.format_.width - (input_.format_.width - 1)
            if num_zeros > 0:
                value = f'{{{self.zero_const(num_zeros)}, {value}}}'

            # make the assignment
            self.digital_assignment(signal=output, value=value, comment='SInt -> UInt')
        else:
            raise ValueError(f'Unknown type conversion: {expr.__class__.__name__}')

        return output

    def init_file(self):
        # print header
        self.comment(f'Model generated on {datetime.datetime.now()}')
        self.writeln()

        # set timescale
        self.writeln(f'`timescale 1ns/1ps')
        self.writeln()

        # include required libraries
        self.include('svreal.sv')
        self.include('msdsl.sv')
        self.writeln()

    def include(self, file):
        self.writeln(f'`include "{file}"')

    def default_nettype(self, type):
        self.writeln(f'`default_nettype {type}')

    def macro_call(self, macro_name, *args, comment=None):
        # format the basic macro call
        line = f"`{macro_name}({', '.join(str(arg) for arg in args)});"

        # add a comment if desired
        if comment is not None:
            line += f' // {comment}'

        # write the full line
        self.writeln(line)

    def digital_assignment(self, signal, value, comment=None):
        # format the basic assignment
        line = f'assign {signal.name} = {value};'

        # add a comment if desired
        if comment is not None:
            line += f' // {comment}'

        # write the full line
        self.writeln(line)

    def comment(self, content=''):
        self.writeln(f'// {content}')

    def comma_separated_lines(self, lines):
        self.write('(' + self.line_ending)
        self.write((',' + self.line_ending).join([self.tab_string + line for line in lines]))
        self.write(self.line_ending)
        self.write(')')

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
            return f'input wire {cls.int_type_str(io.format_)} {io.name}'
        elif isinstance(io, DigitalOutput):
            return f'output wire {cls.int_type_str(io.format_)} {io.name}'
        else:
            raise Exception('Invalid type.')

    @classmethod
    def zero_const(cls, num_zeros):
        return str(num_zeros) + "'b" + '0'*num_zeros

    @classmethod
    def int_type_str(cls, format_: Union[SIntFormat, UIntFormat]):
        retval = 'logic'

        if isinstance(format_, UIntFormat):
            pass
        elif isinstance(format_, SIntFormat):
            retval += ' signed'
        else:
            raise Exception('Cannot determine if format is signed or unsigned.')

        if format_.width > 1:
            retval += f' [{format_.width-1}:0]'

        return retval