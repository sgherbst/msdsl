import numpy as np
from math import ceil, log2
from .expr.table import RealTable
from .expr.expr import clamp_op, to_uint, to_sint

class Function:
    def __init__(self, func, domain, name='real_func', dir='.',
                 numel=512, order=0, clamp=True, coeff_widths=None,
                 coeff_exps=None):
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

        # initialize variables
        self.tables = None
        self.create_tables()

    @property
    def addr_bits(self):
        return int(ceil(log2(self.numel)))

    def create_tables(self):
        self.tables = []
        samp = np.linspace(self.domain[0], self.domain[1], self.numel)
        vals = self.func(samp)
        name = f'{self.name}_0'
        table = RealTable(vals=vals, width=self.coeff_widths[0],
                          exp=self.coeff_exps[0], name=name,
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

    def get_addr_expr(self, in_):
        # calculate result as a real number
        addr_real = (in_ - self.domain[0])*((self.numel-1)/(self.domain[1]-self.domain[0]))
        # convert to a signed integer
        addr_sint = to_sint(addr_real, width=self.addr_bits+1)
        # clamp if needed
        if self.clamp:
            addr_sint = clamp_op(addr_sint, 0, self.numel-1)
        # convert address to an unsigned integer
        addr_uint = to_uint(addr_sint, width=self.addr_bits)
        # calculate fractional address
        addr_frac = addr_real - addr_sint
        # convert to an unsigned integer
        return addr_uint, addr_frac
