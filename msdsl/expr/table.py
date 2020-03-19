from pathlib import Path
from math import ceil, log2
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
    def __init__(self, vals, width=18, exp=None, name='real_table', dir='.'):
        # calculate the range of values
        range_ = max([abs(val) for val in vals])

        # set defaults
        if exp is None:
            exp = self.get_exp(range_, width=width)
        assert isinstance(exp, Integral), 'Exponent must be an integer value.'

        # determine the format
        format_ = RealFormat(range_=range_, width=width, exponent=exp)

        # call the super constructor
        super().__init__(vals=vals, width=width, name=name, dir=dir, format_=format_)

        # save additional settings
        self.exp = exp

    @property
    def path(self):
        return self.dir / f'{self.name}_exp_{self.exp}.mem'

    def to_file(self, path=None):
        # set path if needed
        if path is None:
            path = self.path

        # convert values to SInts and write those to a file
        sint_vals = [self.float_to_fixed(val, exp=self.exp) for val in self.vals]
        sint_table = SIntTable(vals=sint_vals, width=self.width)
        sint_table.to_file(path)

    @classmethod
    def from_file(cls, name='real_table', dir='.', exp=None):
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
        sint_table = SIntTable.from_file(name=match.stem, dir=match.parent)

        # determine exponent from file name
        if exp is None:
            tokens = sint_table.name.split('_')
            assert tokens[-2] == 'exp'
            exp = int(tokens[-1])

        # convert integers to floating point
        vals = [cls.fixed_to_float(sint_val, exp=exp)
                for sint_val in sint_table.vals]

        # return RealTable
        name = '_'.join(sint_table.name.split('_')[:-2])
        return cls(vals=vals, width=sint_table.width, exp=exp, name=name, dir=dir)

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

    @classmethod
    def fixed_to_float(cls, val, exp):
        return val*(2**exp)

    @classmethod
    def float_to_fixed(cls, val, exp):
        return int(round(val*(2**(-exp))))
