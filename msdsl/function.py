import numpy as np
import cvxpy as cp
from math import ceil, log2
from scipy.sparse import coo_matrix, diags
from .expr.table import RealTable

class Function:
    def __init__(self, func, domain, name='real_func', dir='.',
                 numel=512, order=0, clamp=True, coeff_widths=None,
                 coeff_exps=None, verif_per_seg=10):
        # set defaults
        if coeff_widths is None:
            coeff_widths = [18]*(order+1)
        if coeff_exps is None:
            coeff_exps = [None]*(order+1)

        # save settings
        self.func = func
        self.domain = domain
        self.name = name
        self.dir = dir
        self.numel = numel
        self.order = order
        self.clamp = clamp
        self.coeff_widths = coeff_widths
        self.coeff_exps = coeff_exps
        self.verif_per_seg = verif_per_seg

        # initialize variables
        self.tables = None
        self.create_tables()

    @property
    def addr_bits(self):
        return int(ceil(log2(self.numel)))

    def create_tables(self):
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