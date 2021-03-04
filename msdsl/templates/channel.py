from scipy.interpolate import interp1d

from msdsl import MixedSignalModel, sum_op, clamp_op
from msdsl.expr.signals import AnalogState
from msdsl.expr.extras import if_
from msdsl.rf import s4p_to_step

# consumes piecewise-constant waveform and produces a spline
class ChannelModel(MixedSignalModel):
    def __init__(self, t_step, v_step, dtmax, num_spline=4, num_terms=50,
                 func_order=1, func_numel=512, in_='in_', out_prefix='out',
                 dt='dt', clk=None, rst=None, ce=None, **kwargs):
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

        # create the step response function
        chan_func = self.make_function(
            interp1d(t_step, v_step),
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
                mem_sig = AnalogState(name=f'time_mem_{j}', range_=t_step[-1], init=0.0)
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

        # loop over all output points
        for i in range(num_spline):
            # build up list of step & pulse responses
            step = []
            prod = []

            # compute the offset for this spline point
            offset = (i/(num_spline-1))*dtmax

            # evaluate step response function
            for j in range(num_terms+1):
                step_sig = self.set_from_sync_func(
                    f'step_{i}_{j}', chan_func, offset+time_mux[j], clk=clk, rst=rst)
                step.append(step_sig)

            # compute the products to be summed
            for j in range(num_terms+1):
                if j == 0:
                    prod_sig = self.bind_name(f'prod_{i}_{j}', value_hist[j]*step[j])
                else:
                    prod_sig = self.bind_name(f'prod_{i}_{j}', value_hist[j]*(step[j]-step[j-1]))
                prod.append(prod_sig)

            # define model behavior
            self.set_this_cycle(outputs[i], sum_op(prod))


class S4PModel(ChannelModel):
    def __init__(self, s4p_file, tover=0.1e-12, tdur=10e-9, zs=50, zl=50, **kwargs):
        # call the super constructor
        t_step, v_step = s4p_to_step(s4p_file, dt=tover, T=tdur, zs=zs, zl=zl)
        super().__init__(t_step=t_step, v_step=v_step, **kwargs)
