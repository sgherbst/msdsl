print('WARNING: The msdsl.circuit module is experimental!')

from msdsl.expr.signals import AnalogSignal
from msdsl.eqn.deriv import Deriv
from random import randint

class Circuit:
    def __init__(self):
        self.kcl = {}
        self.eqn = [AnalogSignal('gnd')==0]

    def add_to_kcl(self, a, b, curr):
        if a not in self.kcl:
            self.kcl[a] = 0
        self.kcl[a] -= curr

        if b not in self.kcl:
            self.kcl[b] = 0
        self.kcl[b] += curr

    def capacitor(self, a, b, value, state):
        # make signals
        # TODO: keep track of variable names
        ia = AnalogSignal(a+'_'+str(randint(0, 1e9)))

        # TODO: make use of b value
        self.eqn.append(Deriv(state) == ia/value)
        self.eqn.append(AnalogSignal(a)-AnalogSignal(b) == state)
        self.add_to_kcl(a, b, ia)

    def resistor(self, a, b, value):
        self.add_to_kcl(a, b, (AnalogSignal(a)-AnalogSignal(b))/value)

    def current_source(self, a, b, i, v=None):
        self.add_to_kcl(a, b, i)

        if v is not None:
            self.eqn.append(v == AnalogSignal(a)-AnalogSignal(b))

    def voltage_source(self, a, b, v, i=None):
        self.eqn.append(AnalogSignal(a)-AnalogSignal(b) == v)

        if i is None:
            i = AnalogSignal(a+'_'+str(randint(0, 1e9)))

        self.add_to_kcl(a, b, i)

    def compile(self):
        kcl = self.kcl.copy()
        if 'gnd' in kcl:
            del kcl['gnd']

        retval = self.eqn.copy()
        for val in kcl.values():
            retval.append(val == 0)

        return retval