from msdsl import MixedSignalModel, to_sint, to_uint, clamp_op
from msdsl.expr.format import SIntFormat
from msdsl.expr.extras import if_

class OscillatorModel(MixedSignalModel):
    def __init__(self, period='period', dt_req='dt_req', emu_dt='emu_dt', clk_en='clk_en',
                 clk=None, rst=None, init=0, dt_width=32, dt_scale=1e-15, **kwargs):
        # call the super constructor
        super().__init__(**kwargs)

        # add other signals
        period = self.add_analog_input(period)
        emu_dt = self.add_digital_input(emu_dt, width=dt_width)
        dt_req = self.add_digital_output(dt_req, width=dt_width, init=init)
        clk_en = self.add_digital_output(clk_en)
        if clk is not None:
            clk = self.add_digital_input(clk)
        if rst is not None:
            rst = self.add_digital_input(rst)

        # determine if the request was granted
        self.set_this_cycle(clk_en, self.dt_req == self.emu_dt)

        # discretize the period to a uint
        # TODO: cleanup
        period_real = self.set_this_cycle(
            'period_real', period/dt_scale)
        period_sint = self.set_this_cycle(
            'period_sint', to_sint(period_real, width=dt_width+1))
        period_sint.format_ = SIntFormat(
            width=dt_width+1, min_val=0, max_val=((1<<dt_width)-1))
        period_uint = self.set_this_cycle(
            'period_uint', to_uint(period_sint, width=dt_width))

        # update the timestep request
        # TODO: cleanup
        dt_req_decr_sint = self.set_this_cycle('dt_req_decr_sint', dt_req-emu_dt)
        dt_req_decr_sint.format_ = SIntFormat(
            width=dt_width+1, min_val=0, max_val=((1<<dt_width)-1))
        dt_req_decr_uint = self.set_this_cycle(
            'dt_req_decr_uint', to_uint(dt_req_decr_sint, width=dt_width))
        dt_req_imm = self.set_this_cycle('dt_req_imm', if_(clk_en, period_uint, dt_req_decr_uint))
        self.set_next_cycle(dt_req, dt_req_imm, clk=clk, rst=rst)
