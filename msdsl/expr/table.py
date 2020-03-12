from pathlib import Path

from msdsl.fixed_point import get_fixed_point_exp, fixed_to_float, float_to_fixed

class RealTable:
    def __init__(self, real_vals, width=18, exp=None, name='real_table', dir='.'):
        # calculate defaults
        if exp is None:
            range_ = max([abs(real_val) for real_val in real_vals])
            exp = get_fixed_point_exp(range_, width=width)

        # save settings
        self.real_vals = real_vals
        self.width = width
        self.exp = exp
        self.name = name
        self.dir = dir

    def to_file(self):
        int_vals = [float_to_fixed(real_val, exp=self.exp)
                    for real_val in self.real_vals]
        int_table = IntTable(int_vals=int_vals, width=self.width,
                             name=f'{self.name}_exp_{self.exp}', dir=self.dir)
        int_table.to_file()

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
        int_table = IntTable.from_file(name=match.stem, dir=match.parent)

        # determine exponent from file name
        if exp is None:
            tokens = int_table.name.split('_')
            assert tokens[-2] == 'exp'
            exp = int(tokens[-1])

        # convert integers to floating point
        real_vals = [fixed_to_float(int_val, exp=exp)
                     for int_val in int_table.int_vals]

        # return RealTable
        name = '_'.join(int_table.name.split('_')[:-2])
        return RealTable(real_vals=real_vals, width=int_table.width, exp=exp,
                         name=name, dir=dir)

class IntTable:
    def __init__(self, int_vals, width, name='int_table', dir='.'):
        self.int_vals = int_vals
        self.width = width
        self.name = name
        self.dir = dir

    @classmethod
    def from_file(cls, name='int_table', dir='.'):
        # get binary values from file
        bin_table = BinTable.from_file(name=name, dir=dir)

        # convert to signed integers
        int_vals = []
        for bin_val in bin_table.bin_vals:
            if bin_val < (1<<(bin_table.width-1)):
                int_vals.append(bin_val)
            else:
                int_vals.append(bin_val-(1<<(bin_table.width)))

        return cls(int_vals=int_vals, width=bin_table.width, name=name, dir=dir)

    def to_file(self):
        bin_vals = [int_val & ((1<<self.width)-1)
                    for int_val in self.int_vals]
        bin_table = BinTable(bin_vals=bin_vals, width=self.width,
                             name=self.name, dir=self.dir)
        bin_table.to_file()

class BinTable:
    def __init__(self, bin_vals, width, name='bin_table', dir='.'):
        self.bin_vals = bin_vals
        self.width = width
        self.name = name
        self.dir = dir

    def to_file(self):
        # make sure path to file exists
        path = Path(self.dir) / f'{self.name}.mem'
        path.parent.mkdir(exist_ok='True', parents=True)

        # write to file
        with open(path, 'w') as f:
            for elem in self.bin_vals:
                bin_str = '{0:0{1}b}'.format(elem, self.width)
                f.write(f'{bin_str}\n')

    @classmethod
    def from_file(cls, name='bin_table', dir='.'):
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
        bin_vals = [int(bin_str, 2) for bin_str in bin_strs]

        # convert binary values back to integers
        return cls(bin_vals=bin_vals, width=width, name=name, dir=dir)