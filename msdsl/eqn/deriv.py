from copy import deepcopy

from msdsl.expr import ModelExpr, ModelOperator, ExprType
from msdsl.signals import AnalogSignal

def deriv_str(name):
    return 'D(' + str(name) + ')'

class Deriv(ModelExpr):
    def __init__(self, signal: AnalogSignal):
        # save settings
        self.signal = signal

        # call the super constructor
        super().__init__(format=ExprType.REAL)

    def __str__(self):
        return deriv_str(self.signal.name)

def _subst_deriv(expr):
    if not isinstance(expr, ModelExpr):
        raise Exception('Encountered object that is not a ModelExpr')

    if isinstance(expr, ModelOperator):
        expr.operands = [_subst_deriv(operand) for operand in expr.operands]
        return expr
    elif isinstance(expr, Deriv):
        return AnalogSignal(deriv_str(expr.signal.name))
    else:
        return expr

def subst_deriv(expr):
    # the deepcopy is needed because _subst_deriv modifies expr
    return _subst_deriv(deepcopy(expr))

def main():
    print(subst_deriv(Deriv(AnalogSignal('x'))+AnalogSignal('y')+1))

if __name__ == '__main__':
    main()