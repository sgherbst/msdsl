from msdsl import MixedSignalModel, to_sint, to_uint, clamp_op
from msdsl.expr.extras import if_

class OscillatorModel(MixedSignalModel):
    def __init__(self, period='period', dt_req='dt_req', emu_dt='emu_dt', clk_en='clk_en',
                 emu_clk=None, emu_rst=None, dt_width=32, dt_scale=1e-15, **kwargs):
        # call the super constructor
        super().__init__(**kwargs)

        # add other signals
        period = self.add_analog_input(period)
        emu_dt = self.add_digital_input(emu_dt, width=dt_width)
        dt_req = self.add_digital_output(dt_req, width=dt_width)
        clk_en = self.add_digital_output(clk_en)
        if emu_clk is not None:
            emu_clk = self.add_digital_input(emu_clk)
        if emu_rst is not None:
            emu_rst = self.add_digital_input(emu_rst)

        # determine if the request was granted
        self.set_this_cycle(clk_en, self.dt_req == self.emu_dt)

        # discretize the period to a uint
        period_real = self.set_this_cycle(
            'period_real', period/dt_scale)
        period_sint = self.set_this_cycle(
            'period_sint', clamp_op(to_sint(period_real, width=dt_width+1), 0, (1<<dt_width)-1))
        period_uint = self.set_this_cycle(
            'period_uint', to_uint(period_sint, width=dt_width))

        # update the timestep request
        dt_req_decr = self.set_this_cycle('dt_req_decr', to_uint(clamp_op(dt_req-emu_dt, 0, (1<<dt_width)-1)))
        dt_req_imm = self.set_this_cycle('dt_req_imm', if_(clk_en, period_uint, dt_req_decr))
        self.set_next_cycle(dt_req, dt_req_imm, clk=emu_clk, rst=emu_rst)
