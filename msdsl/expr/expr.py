from functools import reduce
from typing import List, Tuple
from numbers import Number, Integral, Real

from msdsl.expr.format import RealFormat, SIntFormat, UIntFormat, Format

# constant wrapping

def wrap_constant(operand):
    if isinstance(operand, Integral):
        if operand < 0:
            return SIntConstant(operand)
        else:
            return UIntConstant(operand)
    elif isinstance(operand, Real):
        return RealConstant(operand)
    else:
        return operand

def wrap_constants(operands):
    return [wrap_constant(operand) for operand in operands]

# type promotion

def get_highest_format_cls(operands):
    if any(isinstance(operand.format, RealFormat) for operand in operands):
        return RealFormat
    elif any(isinstance(operand.format, SIntFormat) for operand in operands):
        return SIntFormat
    else:
        return UIntFormat

def promote_operand(operand, promoted_cls):
    if isinstance(operand.format, UIntFormat) and issubclass(promoted_cls, SIntFormat):
        return uint_to_sint(operand)
    elif isinstance(operand.format, UIntFormat) and issubclass(promoted_cls, RealFormat):
        return sint_to_real(uint_to_sint(operand))
    elif isinstance(operand.format, SIntFormat) and issubclass(promoted_cls, RealFormat):
        return sint_to_real(operand)
    else:
        return operand

def promote_operands(operands, promoted_cls):
    return [promote_operand(operand=operand, promoted_cls=promoted_cls) for operand in operands]

class ModelExpr:
    def __init__(self, format):
        self.format = format

    # arithmetic operations

    def __add__(self, other):
        return sum_op([self, other])

    def __mul__(self, other):
        return prod_op([self, other])

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
    def __init__(self, operands: List, format):
        # call the super constructor
        super().__init__(format=format)

        # save the operand list
        self.operands = wrap_constants(operands)

class UnaryOperator(ModelOperator):
    def __init__(self, operand, format):
        super().__init__(operands=[operand], format=format)

    @property
    def operand(self):
        return self.operands[0]

class BinaryOperator(ModelOperator):
    def __init__(self, lhs, rhs, format):
        super().__init__(operands=[lhs, rhs], format=format)

    @property
    def lhs(self):
        return self.operands[0]

    @property
    def rhs(self):
        return self.operands[1]

class ComparisonOperator(BinaryOperator):
    def __init__(self, lhs, rhs):
        # wrap constants as needed
        lhs = wrap_constant(lhs)
        rhs = wrap_constant(rhs)

        # apply promotion as needed
        format_cls = get_highest_format_cls([lhs, rhs])
        lhs, rhs = promote_operands([lhs, rhs], format_cls)

        # call the super constructor
        super().__init__(lhs=lhs, rhs=rhs, format=UIntFormat(width=1))

class ArithmeticOperator(ModelOperator):
    initial = None

    def __init__(self, operands):
        # determine the output format
        format = reduce(self.function, [operand.format for operand in operands])

        # call the super constructor
        super().__init__(operands=operands, format=format)

    @classmethod
    def function(cls, a, b):
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
    def merge_constants(cls, operands, format_cls):
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
            new_operands.append(Constant(value=const_term, format_cls=format_cls))

        return new_operands

    @classmethod
    def flatten(cls, operands):
        if len(operands) == 0:
            return wrap_constant(cls.initial)
        elif len(operands) == 1:
            return operands[0]
        else:
            return cls(operands)

class BitwiseOperator(ModelOperator):
    def __init__(self, operands):
        # wrap constants as needed
        operands = wrap_constants(operands)

        # Make sure that all operands are unsigned
        assert all(isinstance(operand.format, UIntFormat) for operand in operands), \
               'Bitwise operations only currently support unsigned operands.'

        # Compute the width of the output
        width = max(operand.format.width for operand in operands)

        # Call the super constructor
        super().__init__(operands=operands, format=UIntFormat(width=width))

# Sum

def sum_op(operands):
    # wrap constants as necessary
    operands = wrap_constants(operands)

    # apply promotion if needed
    format_cls = get_highest_format_cls(operands)
    operands = promote_operands(operands, format_cls)

    # perform optimizations
    operands = Sum.merge_with_same_operator(operands)
    operands = Sum.merge_constants(operands, format_cls)

    # generate output
    return Sum.flatten(operands)

class Sum(ArithmeticOperator):
    initial = 0

    @classmethod
    def function(cls, a, b):
        return a + b

    def __str__(self):
        return '(' + '+'.join(str(operand) for operand in self.operands) + ')'

# Product

def prod_op(operands):
    # wrap constants as necessary
    operands = wrap_constants(operands)

    # apply promotion if needed
    format_cls = get_highest_format_cls(operands)
    operands = promote_operands(operands, format_cls)

    # perform optimizations
    operands = Product.merge_with_same_operator(operands)
    operands = Product.merge_constants(operands, format_cls)
    operands = Product.check_for_zero(operands)

    # generate output
    return Product.flatten(operands)

class Product(ArithmeticOperator):
    initial = 1

    @classmethod
    def function(cls, a, b):
        return a * b

    @classmethod
    def check_for_zero(cls, operands):
        if any(((isinstance(operand, Constant) and operand.value == 0) or
                (isinstance(operand, Array) and operand.all_zeros)) for operand in operands):
            return [wrap_constant(0)]
        else:
            return operands

    def __str__(self):
        return '(' + '*'.join(str(operand) for operand in self.operands) + ')'

# Min

def min_op(operands):
    # wrap constants as necessary
    operands = wrap_constants(operands)

    # apply promotion if needed
    format_cls = get_highest_format_cls(operands)
    operands = promote_operands(operands, format_cls)

    # perform optimizations
    operands = Min.merge_with_same_operator(operands)
    operands = Min.merge_constants(operands, format_cls)

    # generate output
    return Min.flatten(operands)

class Min(ArithmeticOperator):
    initial = +float('inf')

    @classmethod
    def function(cls, a, b):
        if isinstance(a, Format) and isinstance(b, Format):
            return a.min_with(b)
        elif isinstance(a, Number) and isinstance(b, Number):
            return min(a, b)
        else:
            raise NotImplementedError

    def __str__(self):
        return 'min(' + ', '.join(str(operand) for operand in self.operands) + ')'

# Max

def max_op(operands):
    # wrap constants as necessary
    operands = wrap_constants(operands)

    # apply promotion if needed
    format_cls = get_highest_format_cls(operands)
    operands = promote_operands(operands, format_cls)

    # perform optimizations
    operands = Max.merge_with_same_operator(operands)
    operands = Max.merge_constants(operands, format_cls)

    # generate output
    return Max.flatten(operands)

class Max(ArithmeticOperator):
    initial = -float('inf')

    @classmethod
    def function(cls, a, b):
        if isinstance(a, Format) and isinstance(b, Format):
            return a.max_with(b)
        elif isinstance(a, Number) and isinstance(b, Number):
            return max(a, b)
        else:
            raise NotImplementedError

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

def concatenate(operands):
    # wrap constants as necessary
    operands = wrap_constants(operands)

    # sanity check
    format_cls = get_highest_format_cls(operands)
    assert issubclass(format_cls, UIntFormat)

    # return result
    if len(operands) == 0:
        raise ValueError('Concatenation requires at least one operand.')
    elif len(operands) == 1:
        return operands[0]
    else:
        return Concatenate(operands)

class Concatenate(ModelOperator):
    def __init__(self, operands):
        width = sum(operand.format.width for operand in operands)
        super().__init__(operands=operands, format=UIntFormat(width=width))

    def __str__(self):
        return '{' + ', '.join(str(operand) for operand in self.operands) + '}'

# array types

def array(elements, address):
    # wrap constants as necessary
    elements = wrap_constants(elements)
    address = wrap_constants(address)

    # apply promotion if needed
    format_cls = get_highest_format_cls(elements)
    elements = promote_operands(elements, format_cls)

    # return the result
    if len(elements) == 0:
        raise ValueError('An array must have at least one element.')
    elif len(elements) == 1:
        return elements[0]
    else:
        return Array(elements=elements, address=address)

class Array(ModelOperator):
    def __init__(self, elements: List, address):
        format = reduce(lambda x, y: x.union_with(y), [element.format for element in elements])
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

    def __str__(self):
        elements = '[' + ', '.join(str(element) for element in self.elements) + ']'
        return f'Array({elements}, {str(self.address)})'

# case statement mimicking

def cases(cases: List[Tuple], default):
    # unpack input
    bits, values = zip(*cases)

    # wrap constants as necessary
    bits = wrap_constants(bits)
    values = wrap_constants(values)
    default = wrap_constant(default)

    # sanity check -- all cases should have a single selection bit
    assert all(isinstance(bit.format, UIntFormat) and bit.format.width==1 for bit in bits)

    # apply promotion as needed
    format_cls = get_highest_format_cls(values + [default])
    values = promote_operands(values, format_cls)
    default = promote_operand(default, format_cls)

    if len(values) == 0:
        return default
    else:
        return Array(elements=case_table(values=values, default=default), address=Concatenate(bits))

def case_table(values: List, default):
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

class TypeConversion(UnaryOperator):
    pass

def uint_to_sint(operand):
    if isinstance(operand, Constant):
        return SIntConstant(operand.value)
    else:
        return UIntToSInt(operand)

class UIntToSInt(TypeConversion):
    def __init__(self, operand: ModelExpr):
        # input checking
        assert isinstance(operand.format, UIntFormat), \
               'Operand provided to UIntToSInt is not an unsigned integer.'

        # construct new format
        format = SIntFormat.from_values([operand.format.min_val, operand.format.max_val])

        # call the super constructor
        super().__init__(operand, format=format)

    def __str__(self):
        return 'uint2sint(' + str(self.operand) + ')'

def sint_to_real(operand):
    if isinstance(operand, Constant):
        return RealConstant(operand.value)
    else:
        return SIntToReal(operand)

class SIntToReal(TypeConversion):
    def __init__(self, operand):
        # input checking
        assert isinstance(operand.format, SIntFormat), \
               'Operand provided to SIntToReal is not a signed integer.'

        # construct new format
        format = RealFormat.from_values([operand.format.min_val, operand.format.max_val])

        # call the super constructor
        super().__init__(operand, format=format)

    def __str__(self):
        return 'sint2real(' + str(self.operand) + ')'

# numeric constants

class Constant(ModelExpr):
    def __init__(self, value: Number, format_cls):
        self.value = value
        super().__init__(format=format_cls.from_value(value))

    def __str__(self):
        return str(self.value)

class RealConstant(Constant):
    def __init__(self, value: Number):
        super().__init__(value=value, format_cls=RealFormat)

class SIntConstant(Constant):
    def __init__(self, value: Number):
        super().__init__(value=value, format_cls=SIntFormat)

class UIntConstant(Constant):
    def __init__(self, value: Number):
        super().__init__(value=value, format_cls=UIntFormat)

# testing

def main():
    a = RealConstant(1)
    b = RealConstant(2)
    c = RealConstant(3)
    print(cases([(a>b, 1.23), (b>c, 4.56)], 7.89))

if __name__ == '__main__':
    main()