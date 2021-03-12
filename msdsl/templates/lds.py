import numpy as np
from tqdm import tqdm
from scipy.linalg import expm
from scipy.interpolate import interp1d

from msdsl import MixedSignalModel, RangeOf
from msdsl.interp.interp import calc_interp_w
from msdsl.interp.lds import SplineLDS
from msdsl.interp.ctle import calc_ctle_abcd

# consumes and produces splines for LDS behavior
# implicitly assumes time has been normalized so dtmax=1
class LDSModel(MixedSignalModel):
    def __init__(self, A, B, C, D, num_spline=4, spline_order=3, func_order=1, func_numel=512,
                 in_prefix='in', out_prefix='out', dt='dt', clk=None, rst=None, ce=None,
                 state_ranges=None, out_range=None, num_terms=100, state_range_safety=10,
                 AB_spline=False, **kwargs):
        # call the super constructor
        super().__init__(**kwargs)

        # set defaults
        if (state_ranges is None) or (out_range is None):
            state_ranges_calc, out_range_calc = self.calc_ranges(
                A=A, B=B, C=C, D=D, in_range=[-1, 1], dt=1/(num_spline-1),
                num_terms=((num_spline-1)*num_terms)+1)
            if state_ranges is None:
                state_ranges = state_ranges_calc
            if out_range is None:
                out_range = out_range_calc

        # save settings
        self.state_ranges = state_ranges
        self.out_range = out_range

        # create IOs
        inputs, outputs = [], []
        for k in range(num_spline):
            inputs.append(self.add_analog_input(f'{in_prefix}_{k}'))
            outputs.append(self.add_analog_output(f'{out_prefix}_{k}'))

        # add other signals
        dt = self.add_analog_input(dt)
        if clk is not None:
            clk = self.add_digital_input(clk)
        if rst is not None:
            rst = self.add_digital_input(rst)
        if ce is not None:
            ce = self.add_digital_input(ce)

        # create internal state variable
        num_states = A.shape[0]
        states = []
        for k in range(num_states):
            state_min, state_max = self.state_ranges[k]
            state_range = max(abs(state_min), abs(state_max))
            states.append(self.add_analog_state(
                f'state_{k}', range_=RangeOf(inputs[0])*state_range*state_range_safety))

        # store previous values
        states_prev = []
        for k in range(num_states):
            states_prev.append(self.cycle_delay(states[k], 1, clk=clk, rst=rst, ce=ce))
        inputs_prev = []
        for k in range(num_spline):
            inputs_prev.append(self.cycle_delay(inputs[k], 1, clk=clk, rst=rst, ce=ce))

        # calculate the interpolation matrix
        W = calc_interp_w(npts=num_spline, order=spline_order)
        self.lds = SplineLDS(A=A, B=B, C=C, D=D, W=W, AB_spline=AB_spline)

        # build A_tilde functions
        print("Building A_tilde functions...")
        A_tilde_funcs = self.build_a_tilde_funcs(order=func_order, numel=func_numel)
        A_tilde = []
        for i in range(num_states):
            A_tilde.append([])
            for j in range(num_states):
                A_tilde[-1].append(self.set_from_sync_func(
                    signal=f'A_tilde_{i}_{j}', func=A_tilde_funcs[i][j],
                    in_=dt, clk=clk, ce=ce, rst=rst))

        # build B_tilde functions
        print("Building B_tilde functions...")
        B_tilde_funcs = self.build_b_tilde_funcs(order=func_order, numel=func_numel)
        B_tilde = []
        for i in range(num_spline):
            B_tilde.append([])
            for j in range(num_states):
                B_tilde[-1].append(self.set_from_sync_func(
                    signal=f'B_tilde_{i}_{j}', func=B_tilde_funcs[i][j],
                    in_=dt, clk=clk, ce=ce, rst=rst))

        # build "tilde" matrices
        C_tilde = self.build_c_tilde()
        D_tilde = self.build_d_tilde()

        ##########################
        ### output calculation ###
        ##########################

        # calculate state-to-output contribution
        y = [0] * num_spline
        for p in range(num_spline):
            for i in range(num_states):
                y[p] += C_tilde[p, i] * states[i]

        # calculate the input-to-output contribution
        for p in range(num_spline):
            for i in range(num_spline):
                y[p] += D_tilde[p, i] * inputs[i]

        # assign the output
        for i in range(num_spline):
            self.set_this_cycle(outputs[i], y[i])

        ####################
        ### state update ###
        ####################

        # calculate state-to-state update
        xn = [0] * num_states
        for i in range(num_states):
            for j in range(num_states):
                xn[i] += A_tilde[i][j] * states_prev[j]

        # calculate input-to-state update
        for i in range(num_spline):
            for j in range(num_states):
                xn[j] += B_tilde[i][j] * inputs_prev[i]

        # update the state
        for i in range(num_states):
            self.set_this_cycle(states[i], xn[i])

    def build_a_tilde_funcs(self, order, numel):
        # sample A_tilde
        tvec = np.linspace(0, 1, numel)
        vvec = np.zeros((len(tvec), self.lds.nstates, self.lds.nstates), dtype=float)
        for i in tqdm(range(len(tvec))):
            # lds.A_tilde returns a matrix that is (num_state, num_state)
            vvec[i, :, :] = self.lds.A_tilde(tvec[i])

        # build functions
        A_tilde_funcs = []
        for i in range(self.lds.nstates):
            A_tilde_funcs.append([])
            for j in range(self.lds.nstates):
                A_tilde_func = self.make_function(
                    interp1d(tvec, vvec[:, i, j]),
                    name=f'A_tilde_func_{i}_{j}',
                    domain=[0, 1], order=order, numel=numel
                )
                A_tilde_funcs[-1].append(A_tilde_func)

        # return functions
        return A_tilde_funcs

    def build_b_tilde_funcs(self, order, numel):
        # sample B_tilde
        tvec = np.linspace(0, 1, numel)
        vvec = np.zeros((len(tvec), self.lds.npts, self.lds.nstates), dtype=float)
        for i in tqdm(range(len(tvec))):
            # lds.B_tilde returns a list of num_spline elements, each of which is (num_state, 1)
            v = self.lds.B_tilde(tvec[i])
            for j in range(self.lds.npts):
                vvec[i, j, :] = v[j].flatten()

        # build functions
        B_tilde_funcs = []
        for i in range(self.lds.npts):
            B_tilde_funcs.append([])
            for j in range(self.lds.nstates):
                B_tilde_func = self.make_function(
                    interp1d(tvec, vvec[:, i, j]),
                    name=f'B_tilde_func_{i}_{j}',
                    domain=[0, 1], order=order, numel=numel
                )
                B_tilde_funcs[-1].append(B_tilde_func)

        # return functions
        return B_tilde_funcs

    def build_c_tilde(self):
        C_tilde = np.zeros((self.lds.npts, self.lds.nstates))
        for i in range(self.lds.npts):
            for j in range(self.lds.nstates):
                # lds.C_tilde is a list of num_spline elements, each of which is (1, num_state)
                C_tilde[i, j] = self.lds.C_tilde[i][0, j]
        return C_tilde

    def build_d_tilde(self):
        # lds.D_tilde is a matrix that is (num_spline, num_spline)
        return self.lds.D_tilde


    @staticmethod
    def calc_ranges(A, B, C, D, in_range, dt, num_terms):
        # convenience definitions
        num_states = A.shape[0]
        min_in, max_in = in_range[0], in_range[1]

        # calculate transfer matrices
        A_tilde = expm(dt*A)
        I = np.eye(*A.shape)
        B_tilde = np.linalg.solve(A, (A_tilde-I).dot(B))

        # calculate powers of Atilde (first is most recent)
        A_tilde_pow = [I]
        for i in range(num_terms-1):
            A_tilde_pow.append(A_tilde_pow[-1].dot(A_tilde))

        # calculate contribution of inputs to states
        inputs_to_states = []
        for i in range(num_terms):
            inputs_to_states.append((A_tilde_pow[i].dot(B_tilde)).flatten())

        state_ranges = []
        for j in range(num_states):
            state_ranges.append(np.zeros((2,), dtype=float))
        for i in range(num_terms):
            for j in range(num_states):
                coeff = inputs_to_states[i][j]
                if coeff >= 0:
                    state_ranges[j] += [coeff*min_in, coeff*max_in]
                else:
                    state_ranges[j] += [coeff*max_in, coeff*min_in]

        # calculate contribution of inputs to outputs
        inputs_to_outputs = []
        for i in range(num_terms):
            inputs_to_outputs.append(float(C.dot(A_tilde_pow[i].dot(B_tilde))))
        inputs_to_outputs[0] += float(D)

        out_range = np.zeros((2,), dtype=float)
        for i in range(num_terms):
            coeff = inputs_to_outputs[i]
            if coeff >= 0:
                out_range += [coeff*min_in, coeff*max_in]
            else:
                out_range += [coeff*max_in, coeff*min_in]

        # return results
        return state_ranges, out_range


class CTLEModel(LDSModel):
    def __init__(self, fz, fp1, dtmax, fp2=None, gbw=None, **kwargs):
        # calculate the state-space representation
        fz = fz*dtmax
        fp1 = fp1*dtmax
        fp2 = fp2*dtmax if fp2 is not None else None
        gbw = gbw*dtmax if gbw is not None else None
        A, B, C, D = calc_ctle_abcd(fz=fz, fp1=fp1, fp2=fp2, gbw=gbw)

        # call the super constructor
        super().__init__(A=A, B=B, C=C, D=D, **kwargs)
