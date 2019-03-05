from typing import Union
from numbers import Number
from math import log2, ceil

from msdsl.expr.svreal import RangeExpr, range_max

class Format:
    shortname = None

    @classmethod
    def from_value(cls, value):
        return cls.from_values([value])

    @classmethod
    def from_values(cls, values):
        raise NotImplementedError

    def min_with(self, other):
        raise NotImplementedError

    def max_with(self, other):
        raise NotImplementedError

    @classmethod
    def cover(cls, formats):
        raise NotImplementedError

class RealFormat(Format):
    # format shortname to aid with human-readable output
    shortname = 'real'

    def __init__(self, range_: Union[Number, RangeExpr], width=None, exponent=None):
        self.range_ = range_
        self.width = width
        self.exponent = exponent

    @classmethod
    def from_values(cls, values):
        # determine range
        range_ = max(abs(value) for value in values)

        # return format
        return RealFormat(range_=range_)

    def __add__(self, other):
        if isinstance(other, RealFormat):
            # note that "+" is overloaded for RangeExpr so that this will work with both numbers and RangeExpr's
            range_ = self.range_ + other.range_
            return RealFormat(range_=range_)
        else:
            raise NotImplementedError

    def __mul__(self, other):
        if isinstance(other, RealFormat):
            # note that "*" is overloaded for RangeExpr so that this will work with both numbers and RangeExpr's
            range_ = self.range_ * other.range_
            return RealFormat(range_=range_)
        else:
            raise NotImplementedError

    def __radd__(self, other):
        return self.__add__(other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def min_with(self, other):
        if isinstance(other, RealFormat):
            # not a typo -- consider range_1 = [-a, +a] and range_2 = [-b, +b], with a < b.  then the output spans
            # [-b, +a], and since a < b, the output range needs to be [-b, +b].  or, in other words, +/- max(a, b)
            range_ = range_max([self.range_, other.range_])
            return RealFormat(range_=range_)
        else:
            raise NotImplementedError

    def max_with(self, other):
        if isinstance(other, RealFormat):
            range_ = range_max([self.range_, other.range_])
            return RealFormat(range_=range_)
        else:
            raise NotImplementedError

    @classmethod
    def cover(cls, formats):
        assert all(isinstance(format_, cls) for format_ in formats), \
            f'Function can only be applied to a list of {cls.__name__} objects.'

        range_ = range_max([format_.range_ for format_ in formats])
        return cls(range_=range_)

    def __str__(self):
        return (f'{self.__class__.__name__}(range={self.range_})')

class IntFormat(Format):
    def __init__(self, width, min_val, max_val):
        self.width = width
        self.min_val = min_val
        self.max_val = max_val

    def __add__(self, other):
        # check that input types match
        if type(self) is not type(other):
            raise NotImplementedError

        # determine possible extrema of the operation
        a = self.min_val + other.min_val
        b = self.max_val + other.max_val

        # return new format
        return self.from_values([a, b])

    def __mul__(self, other):
        # check that input types match
        if type(self) is not type(other):
            raise NotImplementedError

        # determine possible extrema of the operation
        a = self.min_val * other.min_val
        b = self.min_val * other.max_val
        c = self.max_val * other.min_val
        d = self.max_val * other.max_val

        # return new format
        return self.from_values([a, b, c, d])

    def __radd__(self, other):
        return self.__add__(other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def min_with(self, other):
        # check that input types match
        if type(self) is not type(other):
            raise NotImplementedError

        # determine possible extrema of the operation
        a = min(self.min_val, other.min_val)
        b = min(self.max_val, other.max_val)

        # return new format
        return self.from_values([a, b])

    def max_with(self, other):
        # check that input types match
        if type(self) is not type(other):
            raise NotImplementedError

        # determine possible extrema of the operation
        a = max(self.min_val, other.min_val)
        b = max(self.max_val, other.max_val)

        # return new format
        return self.from_values([a, b])

    def can_represent(self, value):
        return self.min_val <= value <= self.max_val

    @classmethod
    def width_of(cls, value):
        raise NotImplementedError

    @classmethod
    def from_values(cls, values):
        # compute maximum width required to represent the values
        width = max(cls.width_of(value) for value in values)

        # return new format
        return cls(width=width, min_val=min(values), max_val=max(values))

    @classmethod
    def cover(cls, formats):
        # check that the input types match
        assert all(isinstance(format_, cls) for format_ in formats), \
            f'Function can only be applied to a list of {cls.__name__} objects.'

        # determine parameters of new format
        width   = max([format_.width   for format_ in formats])
        min_val = min([format_.min_val for format_ in formats])
        max_val = max([format_.max_val for format_ in formats])

        # return new format
        return cls(width=width, min_val=min_val, max_val=max_val)

    def __str__(self):
        return (f'{self.__class__.__name__}(width={self.width}, min_val={self.min_val}, max_val={self.max_val})')

class SIntFormat(IntFormat):
    # format shortname to aid with human-readable output
    shortname = 'sint'

    def __init__(self, width, min_val=None, max_val=None):
        # pick default minimum value (and validate input if one is provided)
        abs_min_val = -(1<<(width-1))
        min_val = min_val if min_val is not None else abs_min_val
        assert min_val >= abs_min_val, \
            f'The given signed integer width {width} cannot have a minimum value below {abs_min_val}'

        # pick default minimum value (and validate input if one is provided)
        abs_max_val = (1<<(width-1))-1
        max_val = max_val if max_val is not None else abs_max_val
        assert max_val <= abs_max_val, \
            f'The given signed integer width {width} cannot have a maximum value above {abs_max_val}'

        # call the super constructor
        super().__init__(width=width, min_val=min_val, max_val=max_val)

    @classmethod
    def width_of(cls, value):
        if value < 0:
            return ceil(log2(0 - value)) + 1
        elif value == 0:
            return 1
        else:
            return ceil(log2(1 + value)) + 1

class UIntFormat(IntFormat):
    # format shortname to aid with human-readable output
    shortname = 'uint'

    def __init__(self, width, min_val=None, max_val=None):
        # pick default minimum value (and validate input if one is provided)
        abs_min_val = 0
        min_val = min_val if min_val is not None else abs_min_val
        assert min_val >= abs_min_val, \
            f'The given unsigned integer width {width} cannot have a minimum value below {abs_min_val}'

        # pick default minimum value (and validate input if one is provided)
        abs_max_val = (1<<width)-1
        max_val = max_val if max_val is not None else abs_max_val
        assert max_val <= abs_max_val, \
            f'The given unsigned integer width {width} cannot have a maximum value above {abs_max_val}'

        # call the super constructor
        super().__init__(width=width, min_val=min_val, max_val=max_val)

    @classmethod
    def width_of(cls, value):
        if value < 0:
            raise ValueError('Unsigned data type cannot store a negative number.')
        elif value == 0:
            return 1
        else:
            return ceil(log2(1 + value))

def is_signed(format_: IntFormat):
    if isinstance(format_, UIntFormat):
        return False
    elif isinstance(format_, SIntFormat):
        return True
    else:
        raise Exception(f'Cannot determine whether this type is signed or unsigned: {format_.__class__.__name__}.')

def main():
    print(RealFormat.from_value(5))
    print(UIntFormat.from_value(5))
    print(SIntFormat.from_value(5))

    print(RealFormat(5)*RealFormat(4))
    print(UIntFormat.from_values([3, 4])*UIntFormat.from_values([6, 7]))
    print(SIntFormat.from_values([-3, 4])*SIntFormat.from_values([-6, 7]))

    print(RealFormat(5).max_with(RealFormat(4)))
    print(RealFormat(5).min_with(RealFormat(4)))

    print(UIntFormat.from_values([3, 4]).max_with(UIntFormat.from_values([6, 7])))
    print(UIntFormat.from_values([3, 4]).min_with(UIntFormat.from_values([6, 7])))

    print(SIntFormat.from_values([-3, 4]).max_with(SIntFormat.from_values([-6, 7])))
    print(SIntFormat.from_values([-3, 4]).min_with(SIntFormat.from_values([-6, 7])))

if __name__ == '__main__':
    main()