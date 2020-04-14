from functools import reduce
from typing import List, Tuple
from numbers import Number, Integral, Real
from math import floor, ceil
from copy import deepcopy

from msdsl.expr.format import RealFormat, SIntFormat, UIntFormat, Format, IntFormat

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
    if any(isinstance(operand.format_, RealFormat) for operand in operands):
        return RealFormat
    elif any(isinstance(operand.format_, SIntFormat) for operand in operands):
        return SIntFormat
    elif any(isinstance(operand.format_, UIntFormat) for operand in operands):
        return UIntFormat
    else:
        raise Exception('Cannot determine highest format class.')

def promote_operand(operand, promoted_cls):
    if issubclass(promoted_cls, UIntFormat):
        return to_uint(operand)
    elif issubclass(promoted_cls, SIntFormat):
        return to_sint(operand)
    elif issubclass(promoted_cls, RealFormat):
        return to_real(operand)
    else:
        raise Exception('Unknown format type: ' + promoted_cls.__name__)

def promote_operands(operands, promoted_cls):
    return [promote_operand(operand=operand, promoted_cls=promoted_cls) for operand in operands]

class ModelExpr:
    def __init__(self, format_):
        self.format_ = format_

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

    # arithmetic shift

    def __rshift__(self, other):
        return ArithmeticRightShift(self, other)

    def __lshift__(self, other):
        return ArithmeticLeftShift(self, other)

    # bitwise access

    def __getitem__(self, item):
        return BitwiseAccess(self, item)

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
    def __init__(self, operands: List, format_):
        # call the super constructor
        super().__init__(format_=format_)

        # save the operand list
        self.operands = wrap_constants(operands)

class UnaryOperator(ModelOperator):
    def __init__(self, operand, format_):
        super().__init__(operands=[operand], format_=format_)

    @property
    def operand(self):
        return self.operands[0]

class BinaryOperator(ModelOperator):
    def __init__(self, lhs, rhs, format_):
        super().__init__(operands=[lhs, rhs], format_=format_)

    @property
    def lhs(self):
        return self.operands[0]

    @property
    def rhs(self):
        return self.operands[1]

class ComparisonOperator(BinaryOperator):
    comp_op = None

    def __init__(self, lhs, rhs):
        # wrap constants as needed
        lhs = wrap_constant(lhs)
        rhs = wrap_constant(rhs)

        # apply promotion as needed
        format_cls = get_highest_format_cls([lhs, rhs])
        lhs, rhs = promote_operands([lhs, rhs], format_cls)

        # call the super constructor
        super().__init__(lhs=lhs, rhs=rhs, format_=UIntFormat(width=1))

    def __str__(self):
        return f'{self.lhs} {self.comp_op} {self.rhs}'

class ArithmeticOperator(ModelOperator):
    initial = None

    def __init__(self, operands):
        # determine the output format
        format_ = reduce(self.function, [operand.format_ for operand in operands])

        # call the super constructor
        super().__init__(operands=operands, format_=format_)

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
            new_operands.append(Constant(value=const_term, format_=format_cls.from_value(const_term)))

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
        assert all(isinstance(operand.format_, UIntFormat) for operand in operands), \
               'Bitwise operations only currently support unsigned operands.'

        # Compute the width of the output
        width = max(operand.format_.width for operand in operands)

        # Call the super constructor
        super().__init__(operands=operands, format_=UIntFormat(width=width))

# Sum

def sum_op(operands):
    operands = list(operands)

    if len(operands) == 0:
        operands = [0]

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
    """
    Compare a list of operands provided in *operands* with each other. Smallest operand will be returned.

    :param operands:    List of operands to be compared
    :return:            Minimal operand
    """

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
            raise Exception('Min can only be applied to numbers and Format operands at this time.')

    def __str__(self):
        return 'min(' + ', '.join(str(operand) for operand in self.operands) + ')'

# Max

def max_op(operands):
    """
    Compare a list of operands provided in *operands* with each other. Largest operand will be returned.

    :param operands:    List of operands to be compared
    :return:            Largest operand
    """

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
            raise Exception('Max can only be applied to numbers and Format operands at this time.')

    def __str__(self):
        return 'max(' + ', '.join(str(operand) for operand in self.operands) + ')'

# bitwise operations that work on any number of arguments

class BitwiseAnd(BitwiseOperator):
    def __str__(self):
        return '(' + '&'.join(str(operand) for operand in self.operands) + ')'

class BitwiseOr(BitwiseOperator):
    def __str__(self):
        return '(' + '|'.join(str(operand) for operand in self.operands) + ')'

class BitwiseXor(BitwiseOperator):
    def __str__(self):
        return '(' + '^'.join(str(operand) for operand in self.operands) + ')'

# unary bitwise operations

class BitwiseInv(UnaryOperator):
    def __init__(self, operand):
        # wrap constant if needed
        operand = wrap_constant(operand)

        # make sure operand is unsigned
        assert isinstance(operand.format_, UIntFormat), \
               'Bitwise inversion only currently support unsigned operands.'

        # Call the super constructor
        super().__init__(operand=operand, format_=operand.format_)

    def __str__(self):
        return f'(~{self.operand})'

class ArithmeticShift(UnaryOperator):
    shift_op = None

    @classmethod
    def function(cls, operand, shift: Integral):
        raise NotImplementedError

    @classmethod
    def compute_output_width(cls, in_format: IntFormat, shift: Integral):
        raise NotImplementedError

    def __init__(self, operand, shift: Integral):
        # wrap constant if needed
        operand = wrap_constant(operand)

        # make sure operand is an integer
        assert isinstance(operand.format_, (UIntFormat, SIntFormat)), \
               f'{self.__class__.__name__} only supports integer operands.'

        # compute parameters of the output format
        width   = self.compute_output_width(in_format=operand.format_, shift=shift)
        min_val = self.function(operand=operand.format_.min_val, shift=shift)
        max_val = self.function(operand=operand.format_.max_val, shift=shift)

        # create the output format
        if isinstance(operand.format_, UIntFormat):
            format_ = UIntFormat(width=width, min_val=min_val, max_val=max_val)
        elif isinstance(operand.format_, SIntFormat):
            format_ = SIntFormat(width=width, min_val=min_val, max_val=max_val)
        else:
            raise Exception('Unknown format type.')

        # save settings
        self.shift = shift

        # call the super constructor
        super().__init__(operand=operand, format_=format_)

    def __str__(self):
        return f'({self.operand}{self.shift_op}{self.shift})'

class ArithmeticLeftShift(ArithmeticShift):
    shift_op = '<<<'

    @classmethod
    def function(cls, operand, shift: Integral):
        return (operand << shift)

    @classmethod
    def compute_output_width(cls, in_format: IntFormat, shift: Integral):
        return (in_format.width + shift)

class ArithmeticRightShift(ArithmeticShift):
    shift_op = '>>>'

    @classmethod
    def function(cls, operand, shift: Integral):
        return (operand >> shift)

    @classmethod
    def compute_output_width(cls, in_format: IntFormat, shift: Integral):
        return max(in_format.width - shift, 1)

class BitwiseAccess(UnaryOperator):
    def __init__(self, operand, key):
        # wrap constant if needed
        operand = wrap_constant(operand)

        # make sure operand is an integer
        assert isinstance(operand.format_, (UIntFormat, SIntFormat)), \
               f'{self.__class__.__name__} only supports integer operands.'

        # determine MSB and LSB of the slice
        if isinstance(key, Integral):
            msb = key
            lsb = key
        elif isinstance(key, slice):
            msb = key.start
            lsb = key.stop
        else:
            raise Exception(f'Unknown indexing type: {key.__class__.__name__}')

        # sanity checks for MSB
        assert isinstance(msb, Integral), 'MSB must be an integer.'
        assert 0 <= msb < operand.format_.width, f'MSB value out of range: {msb} (input width is {operand.format_.width})'

        # sanity checks for LSB
        assert isinstance(lsb, Integral), 'LSB must be an integer.'
        assert 0 <= lsb < operand.format_.width, f'LSB value out of range: {lsb} (input width is {operand.format_.width})'

        # sanity check for relative values of MSB and LSB
        assert lsb <= msb, 'LSB must be less than or equal to MSB.'

        # compute parameters of the output format
        width = msb - lsb + 1

        # create the output format
        if isinstance(operand.format_, UIntFormat):
            format_ = UIntFormat(width=width)
        elif isinstance(operand.format_, SIntFormat):
            format_ = SIntFormat(width=width)
        else:
            raise Exception('Unknown format type.')

        # save settings
        self.msb = msb
        self.lsb = lsb

        # call the super constructor
        super().__init__(operand=operand, format_=format_)

    def __str__(self):
        return f'({self.operand}[{self.msb}:{self.lsb}])'

# specific comparison operations

class LessThan(ComparisonOperator):
    comp_op = '<'

class LessThanOrEquals(ComparisonOperator):
    comp_op = '<='

class GreaterThan(ComparisonOperator):
    comp_op = '>'

class GreaterThanOrEquals(ComparisonOperator):
    comp_op = '>='

class EqualTo(ComparisonOperator):
    comp_op = '=='

class NotEqualTo(ComparisonOperator):
    comp_op = '!='

# concatenation of digital signals

def concatenate(operands):
    """
    Concatenate a list of operands given in *operands*.

    :param operands:    Operands that shall be concatenated
    :return:            All operands concatenated
    """

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
        width = sum(operand.format_.width for operand in operands)
        super().__init__(operands=operands, format_=UIntFormat(width=width))

    def __str__(self):
        return '{' + ', '.join(str(operand) for operand in self.operands) + '}'

# array types

def array(elements: List, address: ModelExpr, real_range_hint: Number=None,
          width=None, exponent=None):
    """
    Create an array

    :param elements:        Elements that shall be added to the array
    :param address:         Address that will be added as final element to array
    :param real_range_hint: Hint for the real datatype range.
    :param width:           Hint for the real datatype width.
    :param exponent:        Hint for the real datatype exponent.
    :return:                Array
    """

    # wrap constants as necessary
    elements = wrap_constants(elements)
    address = wrap_constant(address)

    # return the result
    if len(elements) == 0:
        raise ValueError('An array must have at least one element.')
    elif len(elements) == 1:
        return elements[0]
    else:
        # apply promotion if needed
        format_cls = get_highest_format_cls(elements)
        elements = promote_operands(elements, format_cls)

        # determine the format to use for the array output
        # TODO: clean up handling of symbolic real ranges
        if issubclass(format_cls, RealFormat) and (
                (real_range_hint is not None) or
                (width is not None) or
                (exponent is not None)
        ):
            kwargs = {}
            if real_range_hint is not None:
                kwargs['range_'] = real_range_hint
            if width is not None:
                kwargs['width'] = width
            if exponent is not None:
                kwargs['exponent'] = exponent
            output_format = RealFormat(**kwargs)
        else:
            output_format = format_cls.cover([element.format_ for element in elements])

        # create the Array object
        return Array(elements=elements, address=address, output_format=output_format)

class Array(ModelOperator):
    def __init__(self, elements: List, address, output_format: Format):
        super().__init__(operands=elements+[address], format_=output_format)

    @property
    def all_constants(self):
        return all(isinstance(element, Constant) for element in self.elements)

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
        return f'Array({elements}, {self.address})'

    def __len__(self):
        return len(self.elements)

# case statement mimicking

def cases(cases: List[Tuple], default):
    """
    Create a case statement using the list of tuples provided in *cases*. The default behavior is provided in *default*.

    :param cases:   List of tuples for all cases
    :param default: default case
    :return:        Case Statement
    """

    # unpack input
    bits, values = zip(*cases)

    # wrap constant bits if necessary.  no need to wrap the values or default since that is taken care of by the
    # array function
    bits = wrap_constants(bits)

    # sanity check -- all cases should have a single selection bit
    assert all(isinstance(bit.format_, UIntFormat) and bit.format_.width == 1 for bit in bits), \
        'All of the selection conditions must evaluate to a 1-bit UInt.'

    # compute the elements of the array and its address
    elements = case_table(values=values, default=default)
    address = Concatenate(bits)

    # return the array
    return array(elements=elements, address=address)

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

# generic type conversion

def handle_type_conversion(operand, make_constant, make_class):
    if isinstance(operand, Constant):
        return make_constant(operand.value)
    elif isinstance(operand, Array) and operand.all_constants:
        elements = [make_constant(element.value) for element in operand.elements]
        return array(elements=elements, address=operand.address)
    else:
        return make_class(operand)

class TypeConversion(UnaryOperator):
    input_format_cls = None
    output_format_cls = None

    def __init__(self, operand: ModelExpr, output_format):
        # input checking
        assert isinstance(operand.format_, self.input_format_cls), \
               f'Operand provided to {self.__class__.__name__} does not have the required format {self.input_format_cls.__name__}'

        # output checking
        assert isinstance(output_format, self.output_format_cls), \
            f'Output format {output_format.__class__.__name__} does not match required type {self.output_format_cls.__name__}.'

        # call the superconstructor
        super().__init__(operand=operand, format_=output_format)

    def __str__(self):
        return f'{self.input_format_cls.shortname}_to_{self.output_format_cls.shortname}({self.operand})'

# UInt to SInt

def uint_to_sint(operand, width=None):
    """
    Convert an unsigned integer object *operand* to a signed integer object.

    :param operand: name of signal
    :param width:   specify signal width, in case a custom width is necessary
    :return:        signed integer object
    """
    make_constant = lambda x: SIntConstant(x, width=width)
    make_class = lambda x: UIntToSInt(operand=x, width=width)

    return handle_type_conversion(operand=operand, make_constant=make_constant, make_class=make_class)

class UIntToSInt(TypeConversion):
    input_format_cls  = UIntFormat
    output_format_cls = SIntFormat

    def __init__(self, operand: ModelExpr, width=None):
        # create the output format
        if width is None:
            output_format = SIntFormat.from_values([operand.format_.min_val, operand.format_.max_val])
        else:
            output_format = SIntFormat(width=width)
            assert output_format.can_represent(operand.format_.min_val), \
                f'The given signed integer width {width} cannot represent the operand min value {operand.format.min_val}.'
            assert output_format.can_represent(operand.format_.max_val), \
                f'The given signed integer width {width} cannot represent the operand max value {operand.format.max_val}.'

        # call the super constructor
        super().__init__(operand=operand, output_format=output_format)

# SInt to UInt

def sint_to_uint(operand, width=None):
    """
    Convert a signed integer object *operand* to an unsigned integer object.

    :param operand: name of signal
    :param width:   specify signal width, in case a custom width is necessary
    :return:        unsigned integer object
    """
    make_constant = lambda x: UIntConstant(x, width=width)
    make_class = lambda x: SIntToUInt(operand=x, width=width)

    return handle_type_conversion(operand=operand, make_constant=make_constant, make_class=make_class)

class SIntToUInt(TypeConversion):
    input_format_cls  = SIntFormat
    output_format_cls = UIntFormat

    def __init__(self, operand: ModelExpr, width=None):
        # create the output format
        if width is None:
            output_format = UIntFormat.from_values([operand.format_.min_val, operand.format_.max_val])
        else:
            output_format = UIntFormat(width=width)
            assert output_format.can_represent(operand.format_.min_val), \
                f'The given unsigned integer width {width} cannot represent the operand min value {operand.format_.min_val}.'
            assert output_format.can_represent(operand.format_.max_val), \
                f'The given unsigned integer width {width} cannot represent the operand max value {operand.format_.max_val}.'

        # call the super constructor
        super().__init__(operand=operand, output_format=output_format)

# SInt to Real

def sint_to_real(operand):
    """
    Convert a signed integer object *operand* to a real object.

    :param operand: name of signal
    :return:        real object
    """
    make_constant = lambda x: RealConstant(x)
    make_class = lambda x: SIntToReal(x)

    return handle_type_conversion(operand=operand, make_constant=make_constant, make_class=make_class)

class SIntToReal(TypeConversion):
    input_format_cls  = SIntFormat
    output_format_cls = RealFormat

    def __init__(self, operand: ModelExpr):
        # create the output format
        output_format = RealFormat.from_values([operand.format_.min_val, operand.format_.max_val])

        # call the super constructor
        super().__init__(operand=operand, output_format=output_format)

def real_to_sint(operand, width=None):
    """
    Convert a real object *operand* to a signed integer object.

    :param operand: name of signal
    :param width:   specify signal width, in case a custom width is necessary
    :return:        real object
    """
    make_constant = lambda x: SIntConstant(x, width=width)
    make_class = lambda x: RealToSInt(x, width=width)

    return handle_type_conversion(operand=operand, make_constant=make_constant, make_class=make_class)

class RealToSInt(TypeConversion):
    input_format_cls  = RealFormat
    output_format_cls = SIntFormat

    def __init__(self, operand: ModelExpr, width=None):
        # create the output format
        if width is None:
            # make sure we can handle this case
            assert isinstance(operand.format_.range_, Number), \
                f'The SInt width has to be specified in this case because the operand range is symbolic.  For reference, the operand range expression is {operand.format_.range_}.'

            # create the output format
            min_int_val = int(floor(-operand.format_.range_))
            max_int_val = int(ceil(operand.format_.range_))
            output_format = SIntFormat.from_values([min_int_val, max_int_val])
        else:
            output_format = SIntFormat(width=width)

        # call the superconstructor
        super().__init__(operand=operand, output_format=output_format)

# easy-to-use type conversion

def to_uint(operand, width=None):
    """
    Convert either a signed integer or real object *operand* to an unsigned integer object.

    :param operand: name of signal
    :param width:   specify signal width, in case a custom width is necessary
    :return:        unsigned integer object
    """
    if isinstance(operand.format_, RealFormat):
        # Note that the conversion to SInt adds "1" to the width to hold the sign bit, which is removed
        # upon the demotion to UInt
        return sint_to_uint(real_to_sint(operand=operand, width=(width+1)), width=width)
    elif isinstance(operand.format_, SIntFormat):
        return sint_to_uint(operand, width=width)
    elif isinstance(operand.format_, UIntFormat):
        # This is a kind of tricky case, even though it doesn't likely come up too often.  If the width is specified
        # and doesn't match that of the operand, then we have to return a version of the operand with the requested
        # width.  A deepcopy is used because this function is not supposed to mutate its arguments.
        if (width is not None) and (width != operand.format_.width):
            operand = deepcopy(operand)
            operand.format_ = UIntFormat(width=width, min_val=operand.format_.min_val, max_val=operand.format_.max_val)

        return operand
    else:
        raise Exception(f'Unknown format type: {operand.format_.__class__.__name__}')

def to_sint(operand, width=None):
    """
    Convert either an unsigned integer or real object *operand* to a signed integer object.

    :param operand: name of signal
    :param width:   specify signal width, in case a custom width is necessary
    :return:        signed integer object
    """
    if isinstance(operand.format_, RealFormat):
        return real_to_sint(operand=operand, width=width)
    elif isinstance(operand.format_, SIntFormat):
        # This is a kind of tricky case, even though it doesn't likely come up too often.  If the width is specified
        # and doesn't match that of the operand, then we have to return a version of the operand with the requested
        # width.  A deepcopy is used because this function is not supposed to mutate its arguments.

        if (width is not None) and (width != operand.format_.width):
            operand = deepcopy(operand)
            operand.format_ = SIntFormat(width=width, min_val=operand.format_.min_val, max_val=operand.format_.max_val)

        return operand
    elif isinstance(operand.format_, UIntFormat):
        return uint_to_sint(operand, width=width)
    else:
        raise Exception(f'Unknown format type: {operand.format.__class__.__name__}')

def to_real(operand):
    """
    Convert either an unsigned integer or a signed integer object *operand* to a real object.

    :param operand: name of signal
    :return:        real object
    """
    if isinstance(operand.format_, RealFormat):
        return operand
    elif isinstance(operand.format_, SIntFormat):
        return sint_to_real(operand)
    elif isinstance(operand.format_, UIntFormat):
        return sint_to_real(uint_to_sint(operand))
    else:
        raise Exception(f'Unknown format type: {operand.format_.__class__.__name__}')

# numeric constants

class Constant(ModelExpr):
    def __init__(self, value: Number, format_: Format):
        self.value = value
        super().__init__(format_=format_)

    def __str__(self):
        return str(self.value)

class RealConstant(Constant):
    """
    Container for a constant real datatype within MSDSL.
    """
    def __init__(self, value: Number):
        # determine constant format
        format_ = RealFormat.from_value(value)

        # call the super constructor
        super().__init__(value=value, format_=format_)

class SIntConstant(Constant):
    """
    Container for a constant signed integer datatype within MSDSL.
    """
    def __init__(self, value: Integral, width: Integral=None):
        # check input
        assert isinstance(value, Integral), f'{self.__class__.__name__} requires an integer value, but was given a {value.__class__.__name__}.'

        # determine constant format
        if width is None:
            format_ = SIntFormat.from_value(value)
        else:
            format_ = SIntFormat(width=width, min_val=value, max_val=value)

        # call the super constructor
        super().__init__(value=value, format_=format_)

class UIntConstant(Constant):
    """
    Container for a constant unsigned integer datatype within MSDSL.
    """
    def __init__(self, value: Integral, width: Integral=None):
        # check input
        assert isinstance(value, Integral), f'{self.__class__.__name__} requires an integer value, but was given a {value.__class__.__name__}.'

        # determine constant format
        if width is None:
            format_ = UIntFormat.from_value(value)
        else:
            format_ = UIntFormat(width=width, min_val=value, max_val=value)

        # call the super constructor
        super().__init__(value=value, format_=format_)

# derived operations
def clamp_op(val_expr, min_expr, max_expr):
    return min_op([max_op([val_expr, min_expr]), max_expr])

# testing

def main():
    a = RealConstant(1)
    b = RealConstant(2)
    c = RealConstant(3)
    print(cases([(a>b, 1.23), (b>c, 4.56)], 7.89))

if __name__ == '__main__':
    main()