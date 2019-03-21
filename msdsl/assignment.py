from msdsl.expr.expr import ModelExpr
from msdsl.expr.signals import Signal

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