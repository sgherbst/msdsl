from numbers import Number
from math import log2, ceil

from msdsl.util import warn

class Format:
    def from_value(self, value):
        raise NotImplementedError

class RealFormat(Format):
    def __init__(self, range=None):
        self.range = range

    def from_value(self, value):
        # fill range parameters
        range = self.range
        if range is None:
            range = abs(value)

        # create format
        fmt = RealFormat(range=range)

        # sanity check
        if isinstance(range, Number):
            assert abs(value) <= range, f'Cannot represent real value={value} using range={fmt.range}.'
        else:
            warn(f'Unknown whether real value={value} can fit in range={str(range)}.')

        # return format
        return fmt

class IntegerFormat(Format):
    def __init__(self, width=None, signed=None):
        self.width = width
        self.signed = signed

    def from_value(self, value):
        # determine signed property
        signed = self.signed
        if signed is None:
            signed = value < 0

        # determine width property
        width = self.width
        if width is None:
            width = self.width_of(value)

        # create format
        fmt = IntegerFormat(width=width, signed=signed)

        # sanity check: make sure that the format can actually represent the given value
        # this is mainly needed when the user provides 'width' and/or 'signed'
        assert fmt.min_val <= value <= fmt.max_val, \
               f'Cannot represent integer value={value} using width={fmt.width} and signed={fmt.signed}.'

        # return format
        return fmt

    def width_of(self, value):
        if value == 0:
            return 1
        elif value < 0:
            assert self.signed, 'signed property must be set if value is negative.'
            return ceil(log2(0 - value)) + 1
        else:
            return ceil(log2(1 + value)) + (1 if self.signed else 0)

    @property
    def min_val(self):
        if self.signed:
            return -(1<<(self.width-1))
        else:
            return 0

    @property
    def max_val(self):
        if self.signed:
            return (1<<(self.width-1))-1
        else:
            return (1<<(self.width-0))-1

def is_real_fmt(fmt: Format):
    return isinstance(fmt, RealFormat)

def is_sint_fmt(fmt: Format):
    return isinstance(fmt, IntegerFormat) and fmt.signed

def is_uint_fmt(fmt: Format):
    return isinstance(fmt, IntegerFormat) and not fmt.signed