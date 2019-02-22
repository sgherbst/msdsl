from functools import reduce
from typing import List, Tuple
from numbers import Number, Integral, Real

from msdsl.expr.format import RealFormat, IntegerFormat, Format, is_real_fmt, is_sint_fmt, is_uint_fmt
from msdsl.expr.range import make_range_min, make_range_max, make_range_product, make_range_sum

# constant wrapping

def wrap_if_necessary(expr: List):
    if isinstance(expr, Integral):
        return IntegerConstant(expr)
    elif isinstance(expr, Real):
        return RealConstant(expr)
    else:
        return expr

# type promotion

def promote(operands):
    # determine promoted format
    if any(is_real_fmt(operand.format) for operand in operands):
        promoted_format = RealFormat()
    elif any(is_sint_fmt(operand.format) for operand in operands):
        promoted_format = IntegerFormat(signed=True)
    else:
        promoted_format = IntegerFormat(signed=False)

    # apply promotion where needed
    promoted_operands = []
    for operand in operands:
        if is_uint_fmt(operand.format) and is_sint_fmt(operand.format):
            promoted_operand = uint_to_sint(operand)
        elif is_uint_fmt(operand.format) and is_real_fmt(operand.format):
            promoted_operand = sint_to_real(uint_to_sint(operand))
        elif is_sint_fmt(operand.format) and is_real_fmt(operand.format):
            promoted_operand = sint_to_real(operand)
        else:
            promoted_operand = operand

        promoted_operands.append(promoted_operand)

    # return promoted operands
    return promoted_operands, promoted_format

class ModelExpr:
    def __init__(self, format: Format):
        self.format = format

    # arithmetic operations

    def __add__(self, other):
        return make_sum([self, other])

    def __mul__(self, other):
        return make_product([self, other])

    def __sub__(self, other):
        return self.__add__(-other)

    def __truediv__(self, other):
        if isinstance(other, Number):
            return (1.0/other)*self
        else:
            raise NotImplementedError

    def __radd__(self, other):
        return self.__add__(other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __rsub__(self, other):
        return (-self).__add__(other)

    def __neg__(self):
        return -1.0*self

    def __pos__(self):
        return self

    # bitwise operations

    def __invert__(self):
        return BitwiseInv(self)

    def __and__(self, other):
        return BitwiseAnd([self, other])

    def __or__(self, other):
        return BitwiseOr([self, other])

    def __xor__(self, other):
        return BitwiseXor([self, other])

    # comparisons

    def __le__(self, other):
        return LessThanOrEquals(self, other)

    def __lt__(self, other):
        return LessThan(self, other)

    def __ge__(self, other):
        return GreaterThanOrEquals(self, other)

    def __gt__(self, other):
        return GreaterThan(self, other)

    def __eq__(self, other):
        return EqualTo(self, other)

    def __ne__(self, other):
        return NotEqualTo(self, other)

# general operator types -- not intended to be instantiated directly

class ModelOperator(ModelExpr):
    def __init__(self, operands: List, format: Format):
        # call the super constructor
        super().__init__(format=format)

        # save the operand list
        self.operands = [wrap_if_necessary(operand) for operand in operands]

class UnaryOperator(ModelOperator):
    def __init__(self, operand, format: Format):
        super().__init__(operands=[operand], format=format)

    @property
    def operand(self):
        return self.operands[0]

class BinaryOperator(ModelOperator):
    def __init__(self, lhs, rhs, format: Format):
        super().__init__(operands=[lhs, rhs], format=format)

    @property
    def lhs(self):
        return self.operands[0]

    @property
    def rhs(self):
        return self.operands[1]

class ComparisonOperator(BinaryOperator):
    def __init__(self, lhs, rhs):
        operands, format = promote([wrap_if_necessary(lhs), wrap_if_necessary(rhs)])
        super().__init__(lhs=operands[0], rhs=operands[1], format=IntegerFormat(width=1, signed=False))

class ArithmeticOperator(ModelOperator):
    initial = None

    @classmethod
    def function(cls, a, b):
        raise NotImplementedError

    @classmethod
    def range_function(cls, a, b):
        raise NotImplementedError

    @classmethod
    def merge_with_same_operator(cls, operands):
        # merge operators of the same type
        new_operands = []
        for operand in operands:
            if isinstance(operand, cls):
                new_operands.extend(operand.operands)
            else:
                new_operands.append(operand)

        # set operands of the expression and return it
        return new_operands

    @classmethod
    def merge_constants(cls, operands, format):
        # extract and process constants
        new_operands = []
        const_term = cls.initial
        for operand in operands:
            if isinstance(operand, Constant):
                const_term = cls.function(const_term, operand.value)
            else:
                new_operands.append(operand)

        # add the const_term as a new operand if necessary
        if const_term != cls.initial:
            new_operands.append(Constant(value=const_term, format=format))

        return new_operands

    @classmethod
    def flatten(cls, operands, format):
        if len(operands) == 0:
            return Constant(value=cls.initial, format=format)
        elif len(operands) == 1:
            return operands[0]
        else:
            return cls(operands, format=format)

class BitwiseOperator(ModelOperator):
    def __init__(self, operands):
        # wrap constants as needed
        operands = [wrap_if_necessary(operand) for operand in operands]

        # Make sure that all operands are unsigned
        assert all(is_uint_fmt(operand.format) for operand in operands), 'Bitwise operations only currently support unsigned operands.'

        # Compute the width of the output
        width = max(operand.format.width for operand in operands)

        # Call the super constructor
        super().__init__(operands=operands, format=IntegerFormat(width=width, signed=False))

# Sum

def make_sum(operands):
    operands, format = promote([wrap_if_necessary(operand) for operand in operands])

    # perform optimizations
    operands = Sum.merge_with_same_operator(operands)
    operands = Sum.merge_constants(operands, format)

    # generate output
    return Sum.flatten(operands, format)

class Sum(ArithmeticOperator):
    initial = 0

    @classmethod
    def function(cls, a, b):
        return a + b

    def __init__(self, operands, format):
        if is_real_fmt(format):
            if format.range is None:
                out_range = make_range_sum([operand.format.range for operand in operands])
                out_format = RealFormat(range=out_range)
            else:
                out_format = format
        elif is_uint_fmt(format) or is_sint_fmt(format):
            if format.width is None:
                min_val = sum(operand.format.min_val for operand in operands)
                max_val = sum(operand.format.max_val for operand in operands)
                out_width = max(format.width_of(min_val), format.width_of(max_val))
                out_format = IntegerFormat(width=out_width, signed=format.signed)
            else:
                out_format = format
        else:
            raise Exception('Unknown format type.')

        super().__init__(operands=operands, format=out_format)

    def __str__(self):
        return '(' + '+'.join(str(operand) for operand in self.operands) + ')'

# Product

def make_product(operands):
    operands, format = promote([wrap_if_necessary(operand) for operand in operands])

    # perform optimizations
    operands = Product.merge_with_same_operator(operands)
    operands = Product.merge_constants(operands, format)
    operands = Product.check_for_zero(operands, format)

    # generate output
    return Product.flatten(operands, format)

class Product(ArithmeticOperator):
    initial = 1

    @classmethod
    def function(cls, a, b):
        return a*b

    def __init__(self, operands, format):
        if is_real_fmt(format):
            if format.range is None:
                out_range = make_range_product([operand.format.range for operand in operands])
                out_format = RealFormat(range=out_range)
            else:
                out_format = format
        elif is_sint_fmt(format) or is_uint_fmt(format):
            if format.width is None:
                operand_ranges = [max(abs(operand.format.min_val), abs(operand.format.max_val)) for operand in operands]
                out_range = reduce(lambda x, y: x*y, operand_ranges)
                out_width = format.width_of(out_range)
                out_format = IntegerFormat(width=out_width, signed=format.signed)
            else:
                out_format = format
        else:
            raise Exception('Unknown format type.')

        super().__init__(operands=operands, format=out_format)

    @classmethod
    def check_for_zero(cls, operands, format):
        if any(((isinstance(operand, Constant) and operand.value == 0) or
                (isinstance(operand, Array) and operand.all_zeros)) for operand in operands):
            return [Constant(value=0, format=format)]
        else:
            return operands

    def __str__(self):
        return '(' + '*'.join(str(operand) for operand in self.operands) + ')'

# Min

def make_min(operands):
    operands, format = promote([wrap_if_necessary(operand) for operand in operands])

    # perform optimizations
    operands = Min.merge_with_same_operator(operands)
    operands = Min.merge_constants(operands, format)

    # generate output
    return Min.flatten(operands, format)

class Min(ArithmeticOperator):
    initial = +float('inf')

    @classmethod
    def function(cls, a, b):
        return min(a, b)

    def __init__(self, operands, format):
        if is_real_fmt(format):
            if format.range is None:
                out_range = make_range_min([operand.format.range for operand in operands])
                out_format = RealFormat(range=out_range)
            else:
                out_format = format
        elif is_sint_fmt(format) or is_uint_fmt(format):
            if format.width is None:
                out_width = min(operand.format.width for operand in operands)
                out_format = IntegerFormat(width=out_width, signed=format.signed)
            else:
                out_format = format
        else:
            raise Exception('Unknown format type.')

        super().__init__(operands=operands, format=out_format)

    def __str__(self):
        return 'min(' + ', '.join(str(operand) for operand in self.operands) + ')'

# Max

def make_max(operands):
    operands, format = promote([wrap_if_necessary(operand) for operand in operands])

    # perform optimizations
    operands = Max.merge_with_same_operator(operands)
    operands = Max.merge_constants(operands, format)

    # generate output
    return Max.flatten(operands, format)

class Max(ArithmeticOperator):
    initial = -float('inf')

    @classmethod
    def function(cls, a, b):
        return max(a, b)

    def __init__(self, operands, format):
        if is_real_fmt(format):
            if format.range is None:
                out_range = make_range_max([operand.format.range for operand in operands])
                out_format = RealFormat(range=out_range)
            else:
                out_format = format
        elif is_sint_fmt(format) or is_uint_fmt(format):
            if format.width is None:
                out_width = max(operand.format.width for operand in operands)
                out_format = IntegerFormat(width=out_width, signed=format.signed)
            else:
                out_format = format
        else:
            raise Exception('Unknown format type.')

        super().__init__(operands=operands, format=out_format)

    def __str__(self):
        return 'max(' + ', '.join(str(operand) for operand in self.operands) + ')'

# specific bitwise operations

class BitwiseInv(BitwiseOperator):
    def __init__(self, operand):
        super().__init__(operands=[operand])

    @property
    def operand(self):
        return self.operands[0]

    def __str__(self):
        return f'(~{self.operand})'

class BitwiseAnd(BitwiseOperator):
    def __str__(self):
        return '(' + '&'.join(str(operand) for operand in self.operands) + ')'

class BitwiseOr(BitwiseOperator):
    def __str__(self):
        return '(' + '|'.join(str(operand) for operand in self.operands) + ')'

class BitwiseXor(BitwiseOperator):
    def __str__(self):
        return '(' + '^'.join(str(operand) for operand in self.operands) + ')'

# specific comparison operations

class LessThan(ComparisonOperator):
    def __str__(self):
        return f'({self.lhs} < {self.rhs})'

class LessThanOrEquals(ComparisonOperator):
    def __str__(self):
        return f'({self.lhs} <= {self.rhs})'

class GreaterThan(ComparisonOperator):
    def __str__(self):
        return f'({self.lhs} > {self.rhs})'

class GreaterThanOrEquals(ComparisonOperator):
    def __str__(self):
        return f'({self.lhs} >= {self.rhs})'

class EqualTo(ComparisonOperator):
    def __str__(self):
        return f'({self.lhs} == {self.rhs})'

class NotEqualTo(ComparisonOperator):
    def __str__(self):
        return f'({self.lhs} != {self.rhs})'

# concatenation of digital signals

class Concatenate(ModelOperator):
    def __init__(self, operands):
        # wrap constants as needed
        operands = [wrap_if_necessary(operand) for operand in operands]

        # Make sure that all operands are unsigned
        assert all(is_uint_fmt(operand.format) for operand in operands), 'Concatenation only currently support unsigned operands.'

        # Compute the width of the output
        width = sum(operand.format.width for operand in operands)

        # Call the super constructor
        super().__init__(operands=operands, format=IntegerFormat(width=width, signed=False))

    def __str__(self):
        return '{' + ', '.join(str(operand) for operand in self.operands) + '}'

# array types

class Array(ModelOperator):
    def __init__(self, elements: List, address):
        super().__init__(operands=elements+[address], format=format)

    @property
    def all_zeros(self):
        return all(isinstance(element, Constant) and element.value==0 for element in self.elements)

    @property
    def elements(self):
        return self.operands[:-1]

    @property
    def address(self):
        return self.operands[-1]

# case statement mimicking

class Cases(Array):
    def __init__(self, cases: List[Tuple], default):
        # unpack the cases
        bits, values = zip(*cases)

        # call the super constructor
        super().__init__(elements=self.case_table(values, default=default), address=Concatenate(bits))

    @classmethod
    def case_table(cls, values: List, default):
        # set up the table
        table_length = 1<<len(values)
        table = [None for _ in range(table_length)]

        # fill the table
        for k, value in enumerate(values):
            for idx in range(1<<(len(values)-k-1), 1<<(len(values)-k)):
                table[idx] = value
        table[0] = default

        # return the table
        return table

# type conversions

def uint_to_sint(operand):
    if isinstance(operand, Constant):
        return IntegerConstant(value=operand.value, signed=True)
    else:
        return UIntToSInt(operand)

class UIntToSInt(UnaryOperator):
    def __init__(self, operand: ModelExpr):
        assert is_uint_fmt(operand.format), 'Operand provided to UIntToSInt is not an unsigned integer.'
        super().__init__(operand, format=IntegerFormat(width=operand.format.width+1, signed=True))

    def __str__(self):
        return 'uint2sint(' + str(self.operand) + ')'

def sint_to_real(operand):
    if isinstance(operand, Constant):
        return RealConstant(value=operand.value)
    else:
        return SIntToReal(operand)

class SIntToReal(UnaryOperator):
    def __init__(self, operand):
        assert is_sint_fmt(operand.format), 'Operand provided to SIntToReal is not a signed integer.'
        range = max(abs(operand.format.min_val), abs(operand.format.max_val))
        super().__init__(operand, format=RealFormat(range=range))

    def __str__(self):
        return 'sint2real(' + str(self.operand) + ')'

# numeric constants

class Constant(ModelExpr):
    def __init__(self, value: Number, format: Format):
        self.value = value
        super().__init__(format=format.from_value(value))

    def __str__(self):
        return str(self.value)

class RealConstant(Constant):
    def __init__(self, value: Number, range=None):
        super().__init__(value=value, format=RealFormat(range=range))

    @property
    def range(self):
        return self.format.range

class IntegerConstant(Constant):
    def __init__(self, value: Number, width=None, signed=None):
        super().__init__(value=value, format=IntegerFormat(width=width, signed=signed))

    @property
    def width(self):
        return self.format.width

    @property
    def signed(self):
        return self.format.signed