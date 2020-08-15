from pathlib import Path
from math import ceil, log2
from svreal import (RealType, fixed2real, real2fixed,
                    real2recfn, recfn2real, DEF_HARD_FLOAT_SIG_WIDTH,
                    DEF_HARD_FLOAT_EXP_WIDTH)
from .format import RealFormat, UIntFormat, SIntFormat
from numbers import Integral

def clog2(val):
    return int(ceil(log2(val)))

class Table:
    def __init__(self, vals, width, name, dir, format_):
        # validate input
        assert isinstance(width, Integral), 'Width must be an integer'

        # save settings
        self.vals = vals
        self.width = width
        self.name = name
        self.dir = Path(dir)
        self.format_ = format_

    @property
    def addr_bits(self):
        return int(ceil(log2(len(self.vals))))

    @property
    def path(self):
        return self.dir / f'{self.name}.mem'

class UIntTable(Table):
    def __init__(self, vals, width=None, name='uint_table', dir='.'):
        # set defaults
        if width is None:
            width = max(self.get_width(val) for val in vals)
        # determine the format
        format_ = UIntFormat(width=width, min_val=min(vals), max_val=max(vals))
        # call super constructor
        super().__init__(vals=vals, width=width, name=name, dir=dir, format_=format_)

    def to_file(self, path=None):
        # set path if needed
        if path is None:
            path = self.path

        # make sure path to file exists
        path.parent.mkdir(exist_ok='True', parents=True)

        # write to file
        with open(path, 'w') as f:
            for elem in self.vals:
                bin_str = '{0:0{1}b}'.format(elem, self.width)
                f.write(f'{bin_str}\n')

    @classmethod
    def from_file(cls, name='uint_table', dir='.'):
        # determine the file path
        path = Path(dir) / f'{name}.mem'

        # get binary values in string representation
        bin_strs = []
        with open(path, 'r') as f:
            for line in f:
                bin_strs.append(line.strip())

        # determine the width
        width = len(bin_strs[0])
        if not all([len(elem) == width for elem in bin_strs[1:]]):
            print(f'Failed to determine the width of binary values in file: {path}')
            print('All values in a *.mem file must be in binary format and have exactly the same width')
            raise Exception(f'Could not determine the width of binary values in a file.')

        # convert binary strings to binary values
        vals = [int(bin_str, 2) for bin_str in bin_strs]

        # convert binary values back to integers
        return cls(vals=vals, width=width, name=name, dir=dir)

    @classmethod
    def get_width(cls, val):
        if val == 0:
            return 1
        elif val < 0:
            raise Exception('UIntTable can only represent non-negative numbers.')
        else:
            return clog2(val+1)

class SIntTable(Table):
    def __init__(self, vals, width=None, name='sint_table', dir='.'):
        # set defaults
        if width is None:
            width = max(self.get_width(val) for val in vals)
        # determine the format
        format_ = SIntFormat(width=width, min_val=min(vals), max_val=max(vals))
        # call super constructor
        super().__init__(vals=vals, width=width, name=name, dir=dir, format_=format_)

    @classmethod
    def from_file(cls, name='sint_table', dir='.'):
        # get unsigned integer values from file
        uint_table = UIntTable.from_file(name=name, dir=dir)

        # convert to signed integers
        vals = []
        for uint_val in uint_table.vals:
            if uint_val < (1<<(uint_table.width-1)):
                vals.append(uint_val)
            else:
                vals.append(uint_val-(1<<(uint_table.width)))

        return cls(vals=vals, width=uint_table.width, name=name, dir=dir)

    def to_file(self, path=None):
        # set path if needed
        if path is None:
            path = self.path

        # convert values to UInts and write those to a file
        uint_vals = [val & ((1<<self.width)-1) for val in self.vals]
        uint_table = UIntTable(vals=uint_vals, width=self.width)
        uint_table.to_file(path)

    @classmethod
    def get_width(cls, val):
        if val == 0:
            return 1
        elif val < 0:
            return clog2(-val)+1
        else:
            return clog2(val+1)+1

class RealTable(Table):
    def __init__(self, vals, width=18, exp=None, name='real_table', dir='.',
                 real_type=None, rec_fn_sig_width=None, rec_fn_exp_width=None):
        # calculate the range of values
        range_ = max([abs(val) for val in vals])

        # set defaults
        if exp is None:
            exp = self.get_exp(range_, width=width)
        if real_type is None:
            real_type = RealType.FixedPoint
        if rec_fn_sig_width is None:
            rec_fn_sig_width = DEF_HARD_FLOAT_SIG_WIDTH
        if rec_fn_exp_width is None:
            rec_fn_exp_width = DEF_HARD_FLOAT_EXP_WIDTH

        # input validation
        assert isinstance(exp, Integral), 'Exponent must be an integer value.'

        # determine the format
        format_ = RealFormat(range_=range_, width=width, exponent=exp)

        # call the super constructor
        super().__init__(vals=vals, width=width, name=name, dir=dir, format_=format_)

        # save additional settings
        self.exp = exp
        self.real_type = real_type
        self.rec_fn_sig_width = rec_fn_sig_width
        self.rec_fn_exp_width = rec_fn_exp_width

    @property
    def path(self):
        return self.dir / f'{self.name}_exp_{self.exp}.mem'

    def to_file(self, path=None):
        # set path if needed
        if path is None:
            path = self.path

        # specify the conversion function
        if self.real_type in {RealType.FixedPoint, RealType.FloatReal}:
            conv_func = lambda x: real2fixed(x, exp=self.exp, width=self.width,
                                             treat_as_unsigned=True)
            conv_width = self.width
        elif self.real_type == RealType.HardFloat:
            conv_func = lambda x: real2recfn(x, exp_width=self.rec_fn_exp_width,
                                             sig_width=self.rec_fn_sig_width)
            conv_width = 1 + self.rec_fn_exp_width + self.rec_fn_sig_width
        else:
            raise Exception('Unsupported RealType.')

        # write the table
        uint_table = UIntTable(vals=[conv_func(_) for _ in self.vals],
                               width=conv_width)
        uint_table.to_file(path)

    @classmethod
    def from_file(cls, name='real_table', dir='.', exp=None,
                  real_type=RealType.FixedPoint,
                  rec_fn_sig_width=DEF_HARD_FLOAT_SIG_WIDTH,
                  rec_fn_exp_width=DEF_HARD_FLOAT_EXP_WIDTH):
        # assemble file naming pattern
        if exp is None:
            pattern = f'{name}_exp_*.mem'
        else:
            pattern = f'{name}_exp_{exp}.mem'

        # find matching files
        matches = list(Path(dir).glob(pattern))
        if len(matches) == 0:
            raise Exception(f'Found no RealTables matching "{pattern}" directory: {dir}')
        elif len(matches) > 1:
            raise Exception(f'Found multiple RealTables matching "{pattern}" directory: {dir}')
        else:
            match = matches[0]

        # read integers from file
        uint_table = UIntTable.from_file(name=match.stem, dir=match.parent)

        # determine exponent from file name
        if exp is None:
            tokens = uint_table.name.split('_')
            assert tokens[-2] == 'exp'
            exp = int(tokens[-1])

        # specify the conversion function
        if real_type in {RealType.FixedPoint, RealType.FloatReal}:
            conv_func = lambda x: fixed2real(x, exp=exp, width=uint_table.width,
                                             treat_as_unsigned=True)
        elif real_type == RealType.HardFloat:
            conv_func = lambda x: recfn2real(x, exp_width=rec_fn_exp_width,
                                             sig_width=rec_fn_sig_width)
        else:
            raise Exception('Unsupported RealType.')

        # return RealTable
        name = '_'.join(uint_table.name.split('_')[:-2])
        return cls(
            vals=[conv_func(_) for _ in uint_table.vals],
            width=uint_table.width,
            exp=exp,
            name=name,
            dir=dir,
            real_type=real_type,
            rec_fn_sig_width=rec_fn_sig_width,
            rec_fn_exp_width=rec_fn_exp_width
        )

    @classmethod
    def get_exp(cls, range_, width):
        # calculate the exponent value
        if range_ == 0:
            # val = 0 is a special case because log2(0)=-inf
            # hence any value for the exponent will work
            exp = 0
        else:
            exp = clog2(abs(range_)/((1<<(width-1))-1))

        # return the exponent
        return exp
