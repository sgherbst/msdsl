from msdsl.expr.expr import ModelExpr
from msdsl.expr.signals import Signal
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