import numpy as np

from msdsl.expr.signals import AnalogSignal
from msdsl.expr.simplify import distribute_mult, extract_coeffs
from msdsl.util import list2dict, warn
from msdsl.eqn.deriv import deriv_str, Deriv
from msdsl.eqn.analyze import get_all_signal_names, names
from msdsl.eqn.lds import LDS

def eqn_sys_to_lds(eqns=None, inputs=None, states=None, outputs=None):
    # set defaults
    inputs = inputs if inputs is not None else []
    states = states if states is not None else []
    outputs = outputs if outputs is not None else []

    # create list of derivatives of state variables
    derivs = [Deriv(state) for state in states]

    # create list of all internal signals, then use it to figure out what signals are completely internal
    internal_name_set = get_all_signal_names(eqns) - set(names(inputs) + names(outputs) + names(states) + names(derivs))

    # indices of known and unknown variables
    unknowns = list2dict(list(internal_name_set) + names(outputs) + names(derivs))
    knowns   = list2dict(names(inputs) + names(states))

    # sanity checks
    if len(eqns) > len(unknowns):
        warn(f'System of equations is over-constrained with {len(eqns)} equations and {len(unknowns)} unknowns.')
    elif len(eqns) < len(unknowns):
        warn(f'System of equations is under-constrained with {len(eqns)} equations and {len(unknowns)} unknowns.')

    # build up matrices
    U = np.zeros((len(eqns), len(unknowns)), dtype=float)
    V = np.zeros((len(eqns), len(knowns)), dtype=float)

    for row, eqn in enumerate(eqns):
        # prepare equation for analysis
        eqn = eqn.lhs - eqn.rhs
        eqn = distribute_mult(eqn)

        # extract coefficients of signals (note that some signals may be repeated - we deal with this in the next step
        coeffs, others = extract_coeffs(eqn)
        assert len(others) == 0, \
            'The following terms are not yet handled: ['+ ', '.join(str(other) for other in others)+']'

        for coeff, signal in coeffs:
            if signal.name in unknowns:
                U[row, unknowns[signal.name]] = +coeff
            elif signal.name in knowns:
                V[row,   knowns[signal.name]] = -coeff
            else:
                raise Exception('Variable is not marked as known vs. unknown: ' + signal.name)

    # solve for unknowns in terms of knowns
    M = np.linalg.solve(U, V)

    # separate into A, B, C, D matrices
    if len(states) > 0:
        A = np.zeros((len(states), len(states)), dtype=float)
        for row, out_state in enumerate(names(states)):
            for col, in_state in enumerate(names(states)):
                A[row, col] = M[unknowns[deriv_str(out_state)], knowns[in_state]]
    else:
        A = None

    if len(states) > 0 and len(inputs) > 0:
        B = np.zeros((len(states), len(inputs)), dtype=float)
        for row, out_state in enumerate(names(states)):
            for col, in_input in enumerate(names(inputs)):
                B[row, col] = M[unknowns[deriv_str(out_state)], knowns[in_input]]
    else:
        B = None

    if len(outputs) > 0 and len(states) > 0:
        C = np.zeros((len(outputs), len(states)), dtype=float)
        for row, out_output in enumerate(names(outputs)):
            for col, in_state in enumerate(names(states)):
                C[row, col] = M[unknowns[out_output], knowns[in_state]]
    else:
        C = None

    if len(outputs) > 0 and len(inputs) > 0:
        D = np.zeros((len(outputs), len(inputs)), dtype=float)
        for row, out_output in enumerate(names(outputs)):
            for col, in_input in enumerate(names(inputs)):
                D[row, col] = M[unknowns[out_output], knowns[in_input]]
    else:
        D = None

    return LDS(A=A, B=B, C=C, D=D)

# additional classes

def main():
    x = AnalogSignal('x')
    y = AnalogSignal('y')

    sys = eqn_sys_to_lds(eqns=[Deriv(y) == 0.1*(x-y)], inputs=[x], states=[y])

    print(sys)

if __name__ == '__main__':
    main()