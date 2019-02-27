from typing import Union
from numbers import Number
from math import log2, ceil

from msdsl.expr.svreal import RangeExpr, range_max

class Format:
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

    def union_with(self, other):
        raise NotImplementedError

class RealFormat(Format):
    def __init__(self, range: Union[Number, RangeExpr], width=None, exponent=None):
        self.range = range
        self.width = width
        self.exponent = exponent

    @classmethod
    def from_values(cls, values):
        # determine range
        range = max(abs(value) for value in values)

        # return format
        return RealFormat(range=range)

    def __add__(self, other):
        if isinstance(other, RealFormat):
            # note that "+" is overloaded for RangeExpr so that this will work with both numbers and RangeExpr's
            range = self.range+other.range
            return RealFormat(range=range)
        else:
            raise NotImplementedError

    def __mul__(self, other):
        if isinstance(other, RealFormat):
            # note that "*" is overloaded for RangeExpr so that this will work with both numbers and RangeExpr's
            range = self.range*other.range
            return RealFormat(range=range)
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
            range = range_max([self.range, other.range])
            return RealFormat(range=range)
        else:
            raise NotImplementedError

    def max_with(self, other):
        if isinstance(other, RealFormat):
            range = range_max([self.range, other.range])
            return RealFormat(range=range)
        else:
            raise NotImplementedError

    def union_with(self, other):
        if isinstance(other, RealFormat):
            range = range_max([self.range, other.range])
            return RealFormat(range=range)
        else:
            raise NotImplementedError

    def __str__(self):
        return (f'{self.__class__.__name__}(range={self.range})')

class IntFormat(Format):
    def __init__(self, min_val, max_val):
        self.min_val = min_val
        self.max_val = max_val

    def __add__(self, other):
        a = self.min_val + other.min_val
        b = self.max_val + other.max_val
        return self.from_values([a, b])

    def __mul__(self, other):
        a = self.min_val * other.min_val
        b = self.min_val * other.max_val
        c = self.max_val * other.min_val
        d = self.max_val * other.max_val
        return self.from_values([a, b, c, d])

    def __radd__(self, other):
        return self.__add__(other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def min_with(self, other):
        a = min(self.min_val, other.min_val)
        b = min(self.max_val, other.max_val)
        return self.from_values([a, b])

    def max_with(self, other):
        a = max(self.min_val, other.min_val)
        b = max(self.max_val, other.max_val)
        return self.from_values([a, b])

    def union_with(self, other):
        a = min(self.min_val, other.min_val)
        b = max(self.max_val, other.max_val)
        return self.from_values([a, b])

class SIntFormat(IntFormat):
    def __init__(self, width, min_val=None, max_val=None):
        # pick default minimum value (and validate input if one is provided)
        abs_min_val = -(1<<(width-1))
        min_val = min_val if min_val is not None else abs_min_val
        assert min_val >= abs_min_val

        # pick default minimum value (and validate input if one is provided)
        abs_max_val = (1<<(width-1))-1
        max_val = max_val if max_val is not None else abs_max_val
        assert max_val <= abs_max_val

        # save settings
        self.width = width

        # call the super constructor
        super().__init__(min_val=min_val, max_val=max_val)

    @classmethod
    def from_values(cls, values):
        width = max(cls.width_of(value) for value in values)
        return cls(width=width, min_val=min(values), max_val=max(values))

    @classmethod
    def width_of(cls, value):
        if value < 0:
            return ceil(log2(0 - value)) + 1
        elif value == 0:
            return 1
        else:
            return ceil(log2(1 + value)) + 1

    def __add__(self, other):
        if isinstance(other, SIntFormat):
            return super().__add__(other)
        else:
            raise NotImplementedError

    def __mul__(self, other):
        if isinstance(other, SIntFormat):
            return super().__mul__(other)
        else:
            raise NotImplementedError

    def min_with(self, other):
        if isinstance(other, SIntFormat):
            return super().min_with(other)
        else:
            raise NotImplementedError

    def max_with(self, other):
        if isinstance(other, SIntFormat):
            return super().max_with(other)
        else:
            raise NotImplementedError

    def union_with(self, other):
        if isinstance(other, SIntFormat):
            return super().union_with(other)
        else:
            raise NotImplementedError

    def __str__(self):
        return (f'{self.__class__.__name__}(width={self.width}, min_val={self.min_val}, max_val={self.max_val})')

class UIntFormat(IntFormat):
    def __init__(self, width, min_val=None, max_val=None):
        # pick default minimum value (and validate input if one is provided)
        abs_min_val = 0
        min_val = min_val if min_val is not None else abs_min_val
        assert min_val >= abs_min_val

        # pick default minimum value (and validate input if one is provided)
        abs_max_val = (1<<width)-1
        max_val = max_val if max_val is not None else abs_max_val
        assert max_val <= abs_max_val

        # save settings
        self.width = width

        # call the super constructor
        super().__init__(min_val=min_val, max_val=max_val)

    @classmethod
    def from_values(cls, values):
        width = max(cls.width_of(value) for value in values)
        return cls(width=width, min_val=min(values), max_val=max(values))

    @classmethod
    def width_of(cls, value):
        if value < 0:
            raise ValueError('Unsigned data type cannot store a negative number.')
        elif value == 0:
            return 1
        else:
            return ceil(log2(1 + value))

    def __add__(self, other):
        if isinstance(other, UIntFormat):
            return super().__add__(other)
        else:
            raise NotImplementedError

    def __mul__(self, other):
        if isinstance(other, UIntFormat):
            return super().__mul__(other)
        else:
            raise NotImplementedError

    def min_with(self, other):
        if isinstance(other, UIntFormat):
            return super().min_with(other)
        else:
            raise NotImplementedError

    def max_with(self, other):
        if isinstance(other, UIntFormat):
            return super().max_with(other)
        else:
            raise NotImplementedError

    def union_with(self, other):
        if isinstance(other, UIntFormat):
            return super().union_with(other)
        else:
            raise NotImplementedError

    def __str__(self):
        return (f'{self.__class__.__name__}(width={self.width}, min_val={self.min_val}, max_val={self.max_val})')

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