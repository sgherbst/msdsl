from typing import List
import numpy as np

from msdsl.expr.signals import AnalogSignal, Signal
from msdsl.expr.simplify import distribute_mult, extract_coeffs
from msdsl.util import list2dict
from msdsl.eqn.deriv import deriv_str, Deriv
from msdsl.expr.analyze import signal_names
from msdsl.eqn.lds import LDS
from msdsl.eqn.eqn_list import EqnList
from msdsl.eqn.cases import subst_case

class EqnSys(EqnList):
    def subst_case(self, sel_bit_settings):
        return EqnSys([subst_case(expr=eqn, sel_bit_settings=sel_bit_settings) for eqn in self])

    def to_lds(self, inputs: List[Signal]=None, states: List[Signal]=None, outputs: List[Signal]=None):
        # set defaults
        inputs = inputs if inputs is not None else []
        states = states if states is not None else []
        outputs = outputs if outputs is not None else []

        # create list of derivatives of state variables
        deriv_dict = {deriv.name: deriv for deriv in self.get_derivs()}
        derivs = list(deriv_dict.values())

        # sanity check: no repeated entries in inputs, states, derivatives, or outputs
        assert len(set(signal_names(inputs))) == len(inputs), 'Repeated entries in inputs.'
        assert len(set(signal_names(outputs))) == len(outputs), 'Repeated entries in outputs.'
        assert len(set(signal_names(states))) == len(states), 'Repeated entries in states.'
        assert len(set(signal_names(derivs))) == len(derivs), 'Repeated entries in derivatives.'

        # sanity check: inputs, states, derivatives, and outputs should be disjoint
        assert set(signal_names(inputs)).isdisjoint(signal_names(outputs)), 'Inputs and outputs are not disjoint.'
        assert set(signal_names(inputs)).isdisjoint(signal_names(states)), 'Inputs and states are not disjoint.'
        assert set(signal_names(inputs)).isdisjoint(signal_names(derivs)), 'Inputs and state derivatives are not disjoint.'
        assert set(signal_names(outputs)).isdisjoint(signal_names(states)), 'Outputs and states are not disjoint.'
        assert set(signal_names(outputs)).isdisjoint(signal_names(derivs)), 'Outputs and state derivatives are not disjoint.'
        assert set(signal_names(states)).isdisjoint(signal_names(derivs)), 'States and state derivatives are not disjoint.'

        # sanity check: signal names of derivatives should be the states
        assert set(signal_names(states)) == set(signal_names([deriv.signal for deriv in derivs]))

        # create list of all internal signals, then use it to figure out what signals are completely internal
        external_names = set(signal_names(inputs + outputs + states + derivs))
        internal_name_set = set(signal_names(self.get_all_signals())) - external_names

        # indices of known and unknown variables
        unknowns = list2dict(list(internal_name_set) + signal_names(outputs) + signal_names(derivs))
        knowns   = list2dict(signal_names(inputs) + signal_names(states))

        # sanity checks
        assert not(len(self) > len(unknowns)), f'System of equations is over-constrained with {len(self)} equations and {len(unknowns)} unknowns.'
        assert not (len(self) < len(unknowns)), f'System of equations is under-constrained with {len(self)} equations and {len(unknowns)} unknowns.'

        # build up matrices
        U = np.zeros((len(self), len(unknowns)), dtype=float)
        V = np.zeros((len(self), len(knowns)), dtype=float)

        for row, eqn in enumerate(self):
            # prepare equation for analysis
            eqn = eqn.lhs - eqn.rhs
            eqn = distribute_mult(eqn)

            # extract coefficients of signals (note that some signals may be repeated - we deal with this in the next step
            coeffs, others = extract_coeffs(eqn)
            assert len(others) == 0, \
                'The following terms are not yet handled: ['+ ', '.join(str(other) for other in others)+']'

            # sum up all of the coefficients for each signal
            for coeff, signal in coeffs:
                if signal.name in unknowns:
                    U[row, unknowns[signal.name]] += +coeff
                elif signal.name in knowns:
                    V[row,   knowns[signal.name]] += -coeff
                else:
                    raise Exception('Variable is not marked as known vs. unknown: ' + signal.name)

        # solve for unknowns in terms of knowns
        M = np.linalg.solve(U, V)

        # separate into A, B, C, D matrices
        if len(states) > 0:
            A = np.zeros((len(states), len(states)), dtype=float)
            for row, out_state in enumerate(signal_names(states)):
                for col, in_state in enumerate(signal_names(states)):
                    A[row, col] = M[unknowns[deriv_str(out_state)], knowns[in_state]]
        else:
            A = None

        if len(states) > 0 and len(inputs) > 0:
            B = np.zeros((len(states), len(inputs)), dtype=float)
            for row, out_state in enumerate(signal_names(states)):
                for col, in_input in enumerate(signal_names(inputs)):
                    B[row, col] = M[unknowns[deriv_str(out_state)], knowns[in_input]]
        else:
            B = None

        if len(outputs) > 0 and len(states) > 0:
            C = np.zeros((len(outputs), len(states)), dtype=float)
            for row, out_output in enumerate(signal_names(outputs)):
                for col, in_state in enumerate(signal_names(states)):
                    C[row, col] = M[unknowns[out_output], knowns[in_state]]
        else:
            C = None

        if len(outputs) > 0 and len(inputs) > 0:
            D = np.zeros((len(outputs), len(inputs)), dtype=float)
            for row, out_output in enumerate(signal_names(outputs)):
                for col, in_input in enumerate(signal_names(inputs)):
                    D[row, col] = M[unknowns[out_output], knowns[in_input]]
        else:
            D = None

        return LDS(A=A, B=B, C=C, D=D)

# additional classes

def main():
    x = AnalogSignal('x')
    y = AnalogSignal('y')

    eqn_sys = EqnSys()
    eqn_sys.add_eqn(Deriv(y) == 0.1*(x-y))
    lds = eqn_sys.to_lds(inputs=[x], states=[y])

    print(lds)

if __name__ == '__main__':
    main()