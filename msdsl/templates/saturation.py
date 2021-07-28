from msdsl import MixedSignalModel
from msdsl.interp.nonlin import calc_tanh_vsat, tanhsat


class NonlinModel(MixedSignalModel):
    def __init__(self, func, in_='in_', out='out', domain=None, order=1, numel=64,
                 in_range=None, out_range=None, clk=None, rst=None, **kwargs):
        # call the super constructor
        super().__init__(**kwargs)

        # create IOs
        self.add_analog_input(in_)
        self.add_analog_output(out)

        # save settings
        self.in_range = in_range
        self.out_range = out_range
        self.func = func

        # create and apply function
        real_func = self.make_function(func, domain=domain, order=order, numel=numel, write_tables=False)
        self.set_from_func(self.get_signal(out), real_func, self.get_signal(in_), func_mode='async')


class SaturationModel(NonlinModel):
    def __init__(self, compr=-1, units='dB', veval=1.0, domain=None, in_range=None, out_range=None, **kwargs):
        # set defaults
        if domain is None:
            domain = [-2*abs(veval), +2*abs(veval)]

        # find and save vsat
        vsat = calc_tanh_vsat(compr=compr, units=units)
        def func(v):
            return tanhsat(v, vsat)
        self.vsat = vsat

        # calculate the output range if needed
        if out_range is None:
            if in_range is not None:
                out_range = (func(in_range[0]), func(in_range[1]))

        # call the super constructor
        super().__init__(func=func, domain=domain, in_range=in_range, out_range=out_range, **kwargs)
