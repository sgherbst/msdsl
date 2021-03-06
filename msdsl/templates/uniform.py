from msdsl import MixedSignalModel

class UniformRandom(MixedSignalModel):
    def __init__(self, seed=None, width=32, min_val='min_val', max_val='max_val', out='out',
                 clk=None, rst=None, ce=None, **kwargs):
        # call the super constructor
        super().__init__(**kwargs)

        # create IOs
        min_val = self.add_analog_input(min_val)
        max_val = self.add_analog_input(max_val)
        out = self.add_analog_output(out)
        if clk is not None:
            clk = self.add_digital_input(clk)
        if rst is not None:
            rst = self.add_digital_input(rst)
        if ce is not None:
            ce = self.add_digital_input(ce)

        # assign the uniform signal to the output
        self.uniform_signal(min_val=min_val, max_val=max_val, clk=clk, rst=rst, ce=ce,
                            lfsr_name='rand_uint', lfsr_width=width, lfsr_init=seed,
                            uniform_name=out)
