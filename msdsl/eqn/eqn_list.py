from typing import List

from msdsl.expr.analyze import walk_expr, signal_names
from msdsl.expr.signals import AnalogSignal, DigitalSignal, Signal
from msdsl.expr.format import RealFormat
from msdsl.eqn.deriv import Deriv
from msdsl.eqn.cases import EqnCase
from msdsl.expr.expr import ModelExpr

class EqnList:
    def __init__(self, eqns: List[ModelExpr]=None):
        self.eqns = eqns[:] if eqns is not None else []

    # adding equations to the system

    def add_eqn(self, eqn: ModelExpr):
        """
        Adds equations *eqn* to self.eqns attribute of EqnList class object.

        :param eqn: List of equations that shall be added
        :return:
        """
        self.add_eqns([eqn])

    def add_eqns(self, eqns: List[ModelExpr]):
        self.eqns = self.eqns + eqns

    # signal access functions

    def get_all_signals(self):
        return [signal for eqn in self.eqns for signal in walk_expr(eqn, lambda e: isinstance(e, Signal) and isinstance(e.format_, RealFormat))]

    def get_derivs(self):
        return [deriv for eqn in self.eqns for deriv in walk_expr(eqn, lambda e: isinstance(e, Deriv))]

    def get_states(self):
        return [deriv.signal for eqn in self.eqns for deriv in walk_expr(eqn, lambda e: isinstance(e, Deriv))]

    def get_eqn_cases(self):
        return [eqn_case for eqn in self.eqns for eqn_case in walk_expr(eqn, lambda e: isinstance(e, EqnCase))]

    def get_sel_bits(self):
        return [sel_bit for eqn_case in self.get_eqn_cases() for sel_bit in eqn_case.sel_bits]

    # overloaded methods

    def __len__(self):
        return len(self.eqns)

    def __iter__(self):
        return (eqn for eqn in self.eqns)

    def __str__(self):
        retval = ['*** System of Equations ***']

        for eqn in self:
            retval.append(str(eqn))
        retval = '\n'.join(retval)

        return retval

def main():
    # equation display
    print(EqnList([AnalogSignal('a') == AnalogSignal('b')]))
    print()

    # signal extraction
    print(signal_names(EqnList([AnalogSignal('a') == AnalogSignal('b')]).get_all_signals()))
    print(signal_names(EqnList([AnalogSignal('a') == Deriv(AnalogSignal('b'))]).get_derivs()))
    print(signal_names(EqnList([AnalogSignal('a') == Deriv(AnalogSignal('b'))]).get_states()))
    print(signal_names(EqnList([AnalogSignal('a') == EqnCase([1, 2], [DigitalSignal('s')])]).get_sel_bits()))

if __name__ == '__main__':
    main()