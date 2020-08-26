import numpy as np
from math import ceil, log2
from scipy.sparse import coo_matrix, diags
from .expr.table import RealTable
from .expr.format import RealFormat
from svreal import (real2recfn, real2fixed, RealType, DEF_HARD_FLOAT_SIG_WIDTH,
                    DEF_HARD_FLOAT_EXP_WIDTH)

class GeneralFunction:
    def __init__(self, domain, name='real_func', numel=512, order=0,
                 clamp=True, coeff_widths=None, coeff_exps=None,
                 verif_per_seg=10, strategy=None, rec_fn_sig_width=None,
                 rec_fn_exp_width=None, real_type=None, log_bits=0):
        # set defaults
        if coeff_widths is None:
            coeff_widths = [18]*(order+1)
        if coeff_exps is None:
            coeff_exps = [None]*(order+1)
        if strategy is None:
            if order in {0, 1}:
                strategy = 'spline'
            else:
                strategy = 'cvxpy'
        if rec_fn_sig_width is None:
            rec_fn_sig_width = DEF_HARD_FLOAT_SIG_WIDTH
        if rec_fn_exp_width is None:
            rec_fn_exp_width = DEF_HARD_FLOAT_EXP_WIDTH
        if real_type is None:
            real_type = RealType.FixedPoint

        # save settings
        self.domain = domain
        self.name = name
        self.numel = numel
        self.order = order
        self.clamp = clamp
        self.coeff_widths = coeff_widths
        self.coeff_exps = coeff_exps
        self.verif_per_seg = verif_per_seg
        self.strategy = strategy
        self.rec_fn_sig_width = rec_fn_sig_width
        self.rec_fn_exp_width = rec_fn_exp_width
        self.real_type = real_type
        self.log_bits = log_bits

    @property
    def addr_bits(self):
        return int(ceil(log2(self.numel)))

    @property
    def linear_bits(self):
        return self.addr_bits - self.log_bits

    @property
    def linear_segm(self):
        return 1 << self.linear_bits

    def get_coeffs(self, func):
        if self.strategy == 'cvxpy':
            return self.get_coeffs_cvxpy(func)
        elif self.strategy == 'spline':
            return self.get_coeffs_spline(func)
        else:
            raise Exception(f'Unknown strategy: {self.strategy}')

    def calc_addr(self, x_vec):
        if self.log_bits == 0:
            # compute address as a real number
            addr_real = (x_vec - self.domain[0])*((self.numel-1)/(self.domain[1]-self.domain[0]))

            # clamp address
            if self.clamp:
                addr_real = np.clip(addr_real, 0, self.numel-1)

            # convert address to an integer
            addr_int = addr_real.astype(np.int)

            # compute fractional part of address
            addr_frac = addr_real - addr_int

            # return both integer and fractional address
            return addr_int, addr_frac
        else:
            # convert to an integer
            int_vec = np.round(x_vec / self.domain[1]).astype(np.int64)

            # determine the top bit of each signal
            top_bit = np.floor(np.log2(int_vec)).astype(np.int)

            # determine the linear address bits
            lin_addr = (int_vec >> (top_bit - self.linear_bits)) & ((1 << self.linear_bits) - 1)

            # determine the remaining bits

            # com

    def get_samp_points_cvxpy(self):
        if self.log_bits == 0:
            # compute step size
            lsb = (self.domain[1] - self.domain[0]) / (self.numel - 1)

            # sample points between domain[0] and domain[1] with linear spacing
            x_vec = self.domain[0] + np.arange(self.numel - 1) * lsb

            # run multiple samples within each segment
            x_vec = np.repeat(x_vec, self.verif_per_seg)
            x_vec = x_vec + np.random.uniform(0, lsb, x_vec.shape)

            # return the vector of samples
            return x_vec
        else:
            # TODO
            pass

    def get_coeffs_cvxpy(self, func):
        # load cvxpy module
        try:
            import cvxpy as cp
        except:
            raise Exception(f"ERROR: module cvxpy could not be loaded, cannot use strategy='cvxpy'")

        # create list of sample points
        x_vec = self.get_samp_points_cvxpy()

        # evaluate the function at the sample poitns
        y_vec = func(x_vec)

        # create vectors of integer and fractional addresses
        addr_int, addr_frac = self.calc_addr(x_vec)

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

        # unpack solution
        return [coeffs[k].value for k in range(self.order+1)]

    def get_samp_points_spline(self):
        if self.log_bits == 0:
            pts = np.linspace(self.domain[0], self.domain[1], self.numel)
            pts = np.append(pts, self.domain[1])
            return [pts]
        else:
            # TODO
            pass


    def get_coeffs_spline(self, func):
        # sample the function
        pts_list = self.get_samp_points_spline()
        y_list = [func(pts) for pts in pts_list]

        # create the coefficient vectors
        retval = []
        if self.order >= 0:
            retval.append(
                np.concatenate(
                    [y[:-1] for y in y_list]
                )
            )
        if self.order >= 1:
            retval.append(
                np.concatenate(
                    [np.diff(y) for y in y_list]
                )
            )
        if self.order >= 2:
            raise Exception('The spline method only supports order=0 and order=1 for now.')

        # return the coefficient vector
        return retval

    def eval_on(self, samp, coeffs):
        # calculate integer and fractional addresses
        addr_int, addr_frac = self.calc_addr(samp)

        # sum up output contributions
        out = np.zeros(len(samp))
        for k in range(self.order+1):
            out += coeffs[k][addr_int] * np.power(addr_frac, k)

        # return output
        return out

class PlaceholderFunction(GeneralFunction):
    def __init__(self, domain, name='real_func', numel=512, order=0,
                 clamp=True, coeff_ranges=None, coeff_exps=None,
                 coeff_widths=None, verif_per_seg=10, strategy=None,
                 rec_fn_sig_width=None, rec_fn_exp_width=None,
                 real_type=None, log_bits=0):
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
                         coeff_exps=coeff_exps, verif_per_seg=verif_per_seg,
                         strategy=strategy, rec_fn_sig_width=rec_fn_sig_width,
                         rec_fn_exp_width=rec_fn_exp_width, real_type=real_type,
                         log_bits=log_bits)

    def coeffs_to_fixed(self, coeffs, treat_as_unsigned=False):
        retval = []
        for k in range(self.order+1):
            retval.append([
                real2fixed(
                    coeff,
                    exp=self.coeff_exps[k],
                    width=self.coeff_widths[k],
                    treat_as_unsigned=treat_as_unsigned
                ) for coeff in coeffs[k]
            ])
        return retval

    def coeffs_to_rec_fn(self, coeffs):
        retval = []
        for k in range(self.order+1):
            retval.append([
                real2recfn(
                    in_=coeff,
                    exp_width=self.rec_fn_exp_width,
                    sig_width=self.rec_fn_sig_width
                ) for coeff in coeffs[k]
            ])
        return retval

    def get_coeffs_fixed_fmt(self, func, treat_as_unsigned=False):
        coeffs = self.get_coeffs(func)
        return self.coeffs_to_fixed(coeffs, treat_as_unsigned=treat_as_unsigned)

    def get_coeffs_rec_fn(self, func):
        coeffs = self.get_coeffs(func)
        return self.coeffs_to_rec_fn(coeffs)

    def get_coeffs_bin_fmt(self, func):
        if self.real_type in {RealType.FixedPoint, RealType.FloatReal}:
            return self.get_coeffs_fixed_fmt(func, treat_as_unsigned=True)
        elif self.real_type == RealType.HardFloat:
            return self.get_coeffs_rec_fn(func)
        else:
            raise Exception('Unsupported RealType.')

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
                 coeff_exps=None, verif_per_seg=10, strategy=None,
                 rec_fn_sig_width=None, rec_fn_exp_width=None,
                 real_type=None, log_mode=False, log_bits=0):
        # call super constructor
        super().__init__(domain=domain, name=name, numel=numel, order=order,
                         clamp=clamp, coeff_widths=coeff_widths,
                         coeff_exps=coeff_exps, verif_per_seg=verif_per_seg,
                         strategy=strategy, rec_fn_sig_width=rec_fn_sig_width,
                         rec_fn_exp_width=rec_fn_exp_width, real_type=real_type,
                         log_bits=log_bits)

        # save settings
        self.func = func
        self.dir = dir

        # initialize variables
        self.tables = None
        self.create_tables()

    def create_tables(self):
        # calculate coefficients
        coeffs = self.get_coeffs(self.func)

        # write coefficients in tables
        self.tables = []
        for k, coeff_vec in enumerate(coeffs):
            name = f'{self.name}_lut_{k}'
            table = RealTable(vals=coeff_vec, width=self.coeff_widths[k],
                              exp=self.coeff_exps[k], name=name, dir=self.dir,
                              real_type=self.real_type)
            self.tables.append(table)

    def eval_on(self, samp, coeffs=None):
        # set defaults
        if coeffs is None:
            coeffs = [self.tables[k].vals for k in range(self.order+1)]

        # call the parent method
        return super().eval_on(samp=samp, coeffs=coeffs)
