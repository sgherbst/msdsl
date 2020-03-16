from pathlib import Path
from math import ceil, log2
from .format import RealFormat, UIntFormat, SIntFormat

def clog2(val):
    return int(ceil(log2(val)))

class Table:
    @property
    def format_(self):
        raise NotImplementedError

class UIntTable(Table):
    def __init__(self, uint_vals, width=None, name='uint_table', dir='.'):
        # set defaults
        if width is None:
            width = max(self.get_unsigned_width(uint_val)
                        for uint_val in uint_vals)
        self.uint_vals = uint_vals
        self.width = width
        self.name = name
        self.dir = dir

    @property
    def path(self):
        return Path(self.dir) / f'{self.name}.mem'

    @property
    def format_(self):
        return UIntFormat(width=self.width, min_val=min(self.uint_vals),
                          max_val=max(self.uint_vals))

    def to_file(self, path=None):
        # set path if needed
        if path is None:
            path = self.path

        # make sure path to file exists
        path.parent.mkdir(exist_ok='True', parents=True)

        # write to file
        with open(path, 'w') as f:
            for elem in self.uint_vals:
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
        uint_vals = [int(bin_str, 2) for bin_str in bin_strs]

        # convert binary values back to integers
        return cls(uint_vals=uint_vals, width=width, name=name, dir=dir)

    @classmethod
    def get_unsigned_width(cls, val):
        if val == 0:
            return 1
        elif val < 0:
            raise Exception('UIntTable can only represent non-negative numbers.')
        else:
            return clog2(val+1)

class SIntTable(Table):
    def __init__(self, sint_vals, width=None, name='sint_table', dir='.'):
        # set defaults
        if width is None:
            width = max(self.get_signed_width(int_val)
                        for int_val in sint_vals)

        # save settings
        self.sint_vals = sint_vals
        self.width = width
        self.name = name
        self.dir = dir

    @property
    def path(self):
        return Path(self.dir) / f'{self.name}.mem'

    @property
    def format_(self):
        return SIntFormat(width=self.width, min_val=min(self.sint_vals),
                          max_val=max(self.sint_vals))

    @classmethod
    def from_file(cls, name='sint_table', dir='.'):
        # get binary values from file
        uint_table = UIntTable.from_file(name=name, dir=dir)

        # convert to signed integers
        sint_vals = []
        for uint_val in uint_table.uint_vals:
            if uint_val < (1<<(uint_table.width-1)):
                sint_vals.append(uint_val)
            else:
                sint_vals.append(uint_val-(1<<(uint_table.width)))

        return cls(sint_vals=sint_vals, width=uint_table.width, name=name, dir=dir)

    def to_file(self, path=None):
        # set path if needed
        if path is None:
            path = self.path

        # convert values to UInts and write those to a file
        uint_vals = [sint_val & ((1<<self.width)-1)
                    for sint_val in self.sint_vals]
        uint_table = UIntTable(uint_vals=uint_vals, width=self.width)
        uint_table.to_file(path)

    @classmethod
    def get_signed_width(cls, val):
        if val == 0:
            return 1
        elif val < 0:
            return clog2(-val)+1
        else:
            return clog2(val+1)+1

class RealTable(Table):
    def __init__(self, real_vals, width=18, exp=None, name='real_table', dir='.'):
        # calculate defaults
        if exp is None:
            range_ = max([abs(real_val) for real_val in real_vals])
            exp = self.get_fixed_point_exp(range_, width=width)

        # save settings
        self.real_vals = real_vals
        self.width = width
        self.exp = exp
        self.name = name
        self.dir = dir

        # call the superconstructor
        super().__init__()

    @property
    def path(self):
        return Path(self.dir) / f'{self.name}_exp_{self.exp}.mem'

    @property
    def format_(self):
        range_ = max(abs(real_val) for real_val in self.real_vals)
        return RealFormat(range_=range_, width=self.width,
                          exponent=self.exp)

    def to_file(self, path=None):
        # set path if needed
        if path is None:
            path = self.path

        # convert values to SInts and write those to a file
        sint_vals = [self.float_to_fixed(real_val, exp=self.exp)
                     for real_val in self.real_vals]
        sint_table = SIntTable(sint_vals=sint_vals, width=self.width)
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
        real_vals = [cls.fixed_to_float(sint_val, exp=exp)
                     for sint_val in sint_table.sint_vals]

        # return RealTable
        name = '_'.join(sint_table.name.split('_')[:-2])
        return cls(real_vals=real_vals, width=sint_table.width,
                   exp=exp, name=name, dir=dir)

    @classmethod
    def get_fixed_point_exp(cls, val, width):
        # calculate the exponent value
        if val == 0:
            # val = 0 is a special case because log2(0)=-inf
            # hence any value for the exponent will work
            exp = 0
        else:
            exp = clog2(abs(val)/((1<<(width-1))-1))

        # return the exponent
        return exp

    @classmethod
    def fixed_to_float(cls, val, exp):
        return val*(2**exp)

    @classmethod
    def float_to_fixed(cls, val, exp):
        return int(round(val*(2**(-exp))))
