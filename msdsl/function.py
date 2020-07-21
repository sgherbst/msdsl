import numpy as np
from math import ceil, log2
from scipy.sparse import coo_matrix, diags
from .expr.table import RealTable
from .expr.format import RealFormat

class GeneralFunction:
    def __init__(self, domain, name='real_func', numel=512, order=0,
                 clamp=True, coeff_widths=None, coeff_exps=None):
        # set defaults
        if coeff_widths is None:
            coeff_widths = [18]*(order+1)
        if coeff_exps is None:
            coeff_exps = [None]*(order+1)

        self.domain = domain
        self.name = name
        self.numel = numel
        self.order = order
        self.clamp = clamp
        self.coeff_widths = coeff_widths
        self.coeff_exps = coeff_exps

    @property
    def addr_bits(self):
        return int(ceil(log2(self.numel)))

class PlaceholderFunction(GeneralFunction):
    def __init__(self, domain, name='real_func', numel=512, order=0,
                 clamp=True, coeff_ranges=None, coeff_exps=None,
                 coeff_widths=None):
        # set default for coefficient widths
        if coeff_widths is None:
            if coeff_exps is None:
                coeff_widths = [18]*(order+1)
            else:
                coeff_widths = [self.calc_width(range_, exponent)
                                for range_, exponent in zip(coeff_ranges, coeff_widths)]

        # set default for coefficient exponents
        if coeff_exps is None:
            coeff_exps = [self.calc_exponent(range_, width)
                          for range_, width in zip(coeff_ranges, coeff_widths)]

        # set default values for coefficient ranges
        if coeff_ranges is None:
            coeff_ranges = [self.calc_range(width, exponent)
                            for width, exponent in zip(coeff_widths, coeff_exps)]

        # save formatting information
        self.formats = [RealFormat(range_=range_, width=width, exponent=exponent)
                        for range_, width, exponent in zip(coeff_ranges, coeff_widths, coeff_exps)]

        # call super constructor
        super().__init__(domain=domain, name=name, numel=numel, order=order,
                         clamp=clamp, coeff_widths=coeff_widths,
                         coeff_exps=coeff_exps)

    @staticmethod
    def calc_exponent(range, width):
        if range == 0:
            return 0
        else:
            return int(ceil(log2(range/(2**(width-1)-1))))

    @staticmethod
    def calc_width(range, exponent):
        if range == 0:
            return 1
        else:
            return int(ceil(1+log2((range/(2**exponent))+1)))

    @staticmethod
    def calc_range(width, exponent):
        return 2**(width+exponent-1)

class Function(GeneralFunction):
    def __init__(self, func, domain, name='real_func', dir='.',
                 numel=512, order=0, clamp=True, coeff_widths=None,
                 coeff_exps=None, verif_per_seg=10, strategy=None):
        # call super constructor
        super().__init__(domain=domain, name=name, numel=numel, order=order,
                         clamp=clamp, coeff_widths=coeff_widths,
                         coeff_exps=coeff_exps)

        # set defaults
        if strategy is None:
            if order in {0, 1}:
                strategy = 'spline'
            else:
                strategy = 'cvxpy'

        # save settings
        self.func = func
        self.dir = dir
        self.verif_per_seg = verif_per_seg
        self.strategy = strategy

        # initialize variables
        self.tables = None
        self.create_tables()

    def create_tables(self):
        if self.strategy == 'cvxpy':
            self.create_tables_cvxpy()
        elif self.strategy == 'spline':
            self.create_tables_spline()
        else:
            raise Exception(f'Unknown strategy: {self.strategy}')

    def create_tables_cvxpy(self):
        # load cvxpy module
        try:
            import cvxpy as cp
        except:
            raise Exception(f"ERROR: module cvxpy could not be loaded, cannot use strategy='cvxpy'")

        # create list of sample points
        lsb = (self.domain[1] - self.domain[0])/(self.numel-1)
        x_vec = self.domain[0] + np.arange(self.numel-1)*lsb
        x_vec = np.repeat(x_vec, self.verif_per_seg)
        x_vec = x_vec + np.random.uniform(0, lsb, x_vec.shape)

        # evaluate the function at the sample poitns
        y_vec = self.func(x_vec)

        # create vectors of integer and fractional addresses
        addr_real = (x_vec - self.domain[0])*((self.numel-1)/(self.domain[1]-self.domain[0]))
        if self.clamp:
            addr_real = np.clip(addr_real, 0, self.numel-1)
        addr_int = addr_real.astype(np.int)
        addr_frac = addr_real - addr_int

        # create coefficient vectors
        coeffs = []
        for k in range(self.order+1):
            coeffs.append(cp.Variable(self.numel))

        # utility function to specify weighting
        def Amat(ord):
            data = np.power(addr_frac, ord)
            row = np.arange(len(x_vec))
            col = addr_int
            shape = (len(x_vec), self.numel)
            return coo_matrix((data, (row, col)), shape=shape, dtype=float)

        # create the cost function
        cost = (Amat(0) @ coeffs[0]) - y_vec
        for ord in range(1, self.order+1):
            cost += (Amat(ord) @ coeffs[ord])

        # set up the equality constraints
        eqn_cons = []

        # utility function for diagonal matrics
        def Cmat(offset):
            return diags([1], [offset], shape=(self.numel-1, self.numel), dtype=float)

        # ensure waveform is continuous
        eqn = -(Cmat(1) @ coeffs[0])
        for ord in range(self.order+1):
            eqn += (Cmat(0) @ coeffs[ord])

        # special treatment for the very last entry -- no higher-order terms
        for ord in range(1, self.order+1):
            eqn_cons += [coeffs[ord][-1] == 0]

        # solve the optimization problem
        prob = cp.Problem(cp.Minimize(cp.sum_squares(cost)), eqn_cons)
        prob.solve()

        # unpack solution into tables
        self.tables = []
        for k in range(self.order+1):
            name = f'{self.name}_lut_{k}'
            vals = coeffs[k].value
            table = RealTable(vals=vals, width=self.coeff_widths[k],
                              exp=self.coeff_exps[k], name=name,
                              dir=self.dir)
            self.tables.append(table)

    def create_tables_spline(self):
        # sample the function
        x_vec = np.linspace(self.domain[0], self.domain[1], self.numel)
        y_vec = self.func(x_vec)

        # create the tables
        self.tables = []
        for k in range(self.order+1):
            # name the table
            name = f'{self.name}_lut_{k}'

            # compute table values
            # TODO: make this more generic
            if k == 0:
                vals = y_vec[:]
            elif k == 1:
                vals = np.concatenate((np.diff(y_vec), [0]))
            else:
                raise Exception('Only order=0 and order=1 are supported for now.')

            # convert to a synthesizable table
            table = RealTable(vals=vals, width=self.coeff_widths[k], exp=self.coeff_exps[k],
                              name=name, dir=self.dir)

            # add table to the list of tables
            self.tables.append(table)

    def eval_on(self, samp):
        # calculate address as a real value
        addr_real = (samp - self.domain[0])*((self.numel-1)/(self.domain[1]-self.domain[0]))
        if self.clamp:
            addr_real = np.clip(addr_real, 0, self.numel-1)
        # calculate integer and fractional addresses
        addr_int = addr_real.astype(np.int)
        addr_frac = addr_real - addr_int
        # sum up output contributions
        out = np.zeros(len(samp))
        for k in range(self.order+1):
            out += self.tables[k].vals[addr_int] * np.power(addr_frac, k)
        # return output
        return out
