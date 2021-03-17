from msdsl import MixedSignalModel
from msdsl.interp.nonlin import calc_tanh_vsat, tanhsat

class SaturationModel(MixedSignalModel):
    def __init__(self, compr=-1, units='dB', veval=1.0, in_='in_', out='out', domain=None, order=1,
                 numel=64, in_range=None, out_range=None, clk=None, rst=None, **kwargs):
        # call the super constructor
        super().__init__(**kwargs)

        # set defaults
        if domain is None:
            domain = [-2*abs(veval), +2*abs(veval)]

        # find vsat
        self.vsat = calc_tanh_vsat(compr=compr, units=units)

        # calculate the output range if needed
        if out_range is None:
            if in_range is not None:
                out_range = (self.func(in_range[0]), self.func(in_range[1]))
        self.out_range = out_range

        # create IOs
        self.add_analog_input(in_)
        self.add_analog_output(out)

        # create and apply function
        real_func = self.make_function(self.func, domain=domain, order=order, numel=numel, write_tables=False)
        self.set_from_func(self.get_signal(out), real_func, self.get_signal(in_), func_mode='async')

    def func(self, v):
        return tanhsat(v, self.vsat)
