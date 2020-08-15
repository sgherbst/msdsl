from svreal import RealType, DEF_HARD_FLOAT_EXP_WIDTH, DEF_HARD_FLOAT_SIG_WIDTH
from msdsl.expr.expr import ModelExpr
from msdsl.expr.signals import Signal, DigitalSignal, AnalogSignal
from msdsl.expr.format import RealFormat
from msdsl.expr.table import Table

class Assignment:
    def __init__(self, signal: Signal, expr: ModelExpr):
        self.signal = signal
        self.expr = expr

class BindingAssignment(Assignment):
    pass

class ThisCycleAssignment(Assignment):
    pass

class NextCycleAssignment(Assignment):
    def __init__(self, *args, clk=None, rst=None, ce=None, **kwargs):
        self.clk = clk
        self.rst = rst
        self.ce = ce
        super().__init__(*args, **kwargs)

class SyncRomAssignment(Assignment):
    def __init__(self, signal: Signal, table: Table, addr: ModelExpr,
                 clk=None, ce=None, should_bind=False):
        self.table = table
        self.clk = clk
        self.ce = ce
        self.should_bind = should_bind
        super().__init__(signal=signal, expr=addr)

class SyncRamAssignment(Assignment):
    def __init__(self, signal: AnalogSignal, format_: RealFormat, addr: ModelExpr,
                 clk: Signal=None, ce: Signal=None, we: Signal=None,
                 din: Signal=None, should_bind=False, real_type=RealType.FixedPoint,
                 rec_fn_exp_width=None, rec_fn_sig_width=None):
        # set defaults
        if rec_fn_exp_width is None:
            rec_fn_exp_width = DEF_HARD_FLOAT_EXP_WIDTH
        if rec_fn_sig_width is None:
            rec_fn_sig_width = DEF_HARD_FLOAT_SIG_WIDTH

        # save settings
        self.format_ = format_
        self.clk = clk
        self.ce = ce
        self.we = we
        self.din = din
        self.should_bind = should_bind
        self.real_type = real_type
        self.rec_fn_exp_width = rec_fn_exp_width
        self.rec_fn_sig_width = rec_fn_sig_width
        super().__init__(signal=signal, expr=addr)
