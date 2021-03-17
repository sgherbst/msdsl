import numpy as np
from scipy.interpolate import interp1d

from msdsl import MixedSignalModel, sum_op, clamp_op
from msdsl.expr.signals import AnalogState
from msdsl.expr.extras import if_
from msdsl.rf import s4p_to_step

# consumes piecewise-constant waveform and produces a spline
class ChannelModel(MixedSignalModel):
    def __init__(self, t_step, v_step, dtmax, num_spline=4, num_terms=50,
                 func_order=1, func_numel=512, in_='in_', out_prefix='out',
                 dt='dt', clk=None, rst=None, ce=None, out_range=None, **kwargs):
        # call the super constructor
        super().__init__(**kwargs)

        # define IOs
        in_ = self.add_analog_input(in_)
        outputs = []
        for i in range(num_spline):
            outputs.append(self.add_analog_output(f'{out_prefix}_{i}'))
        dt = self.add_analog_input(dt)
        if clk is not None:
            clk = self.add_digital_input(clk)
        if rst is not None:
            rst = self.add_digital_input(rst)
        if ce is not None:
            ce = self.add_digital_input(ce)

        # calculate the output range if needed
        if out_range is None:
            out_range = self.calc_out_range(
                t_step=t_step, v_step=v_step, in_range=[-1, 1],
                dt=dtmax/(num_spline-1), num_terms=((num_spline-1)*num_terms)+1)
        self.out_range = out_range

        # create an interpolator for the step response
        chan_interp_base = interp1d(
            t_step, v_step, bounds_error=False, fill_value=(v_step[0], v_step[-1]))

        # generate a list of functions that evaluate the
        # step response at various offsets
        chan_interp_funs = []
        for i in range(num_spline):
            chan_interp_funs.append(
                lambda t, i=i: chan_interp_base(t + (i/(num_spline-1))*dtmax))

        # create the single-input, multi-output step response function
        chan_func = self.make_function(
            chan_interp_funs,
            name=f'chan_func',
            domain=[t_step[0], t_step[-1]],
            order=func_order,
            numel=func_numel
        )

        # create a history of past inputs
        new_v = self.add_digital_signal('new_v')
        value_hist = self.make_history(in_, num_terms+1, clk=clk, rst=rst, ce=new_v)
        self.set_this_cycle(new_v, value_hist[0] != value_hist[1])

        # create a history times in the past when the input changed
        time_incr = []
        time_mux = []
        for j in range(num_terms+1):
            if j == 0:
                time_incr.append(dt)
                time_mux.append(0)
            else:
                # create the signal
                mem_sig = AnalogState(name=f'time_mem_{j}', range_=t_step[-1]*1.01, init=0.0)
                self.add_signal(mem_sig)

                # increment time by dt_sig (this is the output from the current tap)
                # note that incrementing is clamped so that it doesn't exceed the range of mem_sig
                incr_sig = self.bind_name(f'time_incr_{j}', clamp_op(mem_sig+dt, 0, t_step[-1]))
                time_incr.append(incr_sig)

                # mux input of DFF between current and previous memory value
                mux_sig = self.bind_name(f'time_mux_{j}', if_(new_v, time_incr[j-1], time_incr[j]))
                time_mux.append(mux_sig)

                # delayed assignment
                self.set_next_cycle(signal=mem_sig, expr=mux_sig, clk=clk, rst=rst)

        # evaluate the step response function
        step = []
        for j in range(num_terms+1):
            # generate names for the step response evaluations
            names = [f'step_{j}_{i}' for i in range(num_spline)]

            # evaluate the step response function
            step.append(
                self.set_from_sync_func(
                    names, chan_func, time_mux[j], clk=clk, rst=rst))

        # loop over all output points
        for i in range(num_spline):
            # build up list of step & pulse responses
            prod = []

            # compute the products to be summed
            for j in range(num_terms+1):
                if j == 0:
                    prod_sig = self.bind_name(f'prod_{i}_{j}', value_hist[j]*step[j][i])
                else:
                    prod_sig = self.bind_name(f'prod_{i}_{j}', value_hist[j]*(step[j][i]-step[j-1][i]))
                prod.append(prod_sig)

            # define model behavior
            self.set_this_cycle(outputs[i], sum_op(prod))

    @staticmethod
    def calc_out_range(t_step, v_step, in_range, dt, num_terms):
        # determine edge times for the output range calculation
        t_edge = dt * np.arange(num_terms + 1)

        # calculate the pulse response for each PWC input segment
        f = interp1d(t_step, v_step, bounds_error=False, fill_value=(v_step[0], v_step[-1]))
        coeffs = f(t_edge[1:]) - f(t_edge[:-1])

        # determine minimum and maximum input value
        min_in, max_in = in_range[0], in_range[1]

        # determine minimum and maximum output value
        min_out = 0
        max_out = 0
        for coeff in coeffs:
            if coeff >= 0:
                # non-negative coefficient
                min_out += min_in*coeff
                max_out += max_in*coeff
            else:
                # negative coefficient
                min_out += max_in*coeff
                max_out += min_in*coeff

        # return output range
        return (min_out, max_out)

class S4PModel(ChannelModel):
    def __init__(self, s4p_file, tover=0.1e-12, tdur=10e-9, zs=50, zl=50, **kwargs):
        # call the super constructor
        t_step, v_step = s4p_to_step(s4p_file, dt=tover, T=tdur, zs=zs, zl=zl)
        super().__init__(t_step=t_step, v_step=v_step, **kwargs)
