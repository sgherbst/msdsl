import numpy as np

from typing import List
from msdsl.expr import ListOp, BinaryOp, Deriv, AnalogSignal, Times, Constant
from msdsl.optimize import simplify
from msdsl.util import list2dict

def names(l: List[AnalogSignal]):
    return [elem.name for elem in l]

def deriv_str(name):
    return f'D({name})'

def subst_deriv(expr):
    if isinstance(expr, Deriv):
        assert isinstance(expr.expr, AnalogSignal)
        return AnalogSignal(deriv_str(expr.expr.name))
    if isinstance(expr, ListOp):
        return type(expr)(subst_deriv(term) for term in expr.terms)
    elif isinstance(expr, BinaryOp):
        return type(expr)(subst_deriv(expr.lhs), subst_deriv(expr.rhs))
    else:
        return expr

def eqn_sys_to_lds(eqns=None, internals=None, inputs=None, outputs=None, states=None):
    # set defaults
    eqns = eqns if eqns is not None else []
    internals = internals if internals is not None else []
    inputs = inputs if inputs is not None else []
    outputs = outputs if outputs is not None else []
    states = states if states is not None else []

    # indices of known and unknown variables
    unknowns = list2dict(names(internals) + names(outputs) + [deriv_str(name) for name in names(states)])
    knowns = list2dict(names(inputs) + names(states))

    # check that matrix is sensible
    assert len(unknowns) == len(eqns)

    # build up matrices
    U = np.zeros((len(eqns), len(unknowns)), dtype=float)
    V = np.zeros((len(eqns), len(knowns)), dtype=float)

    for row, eqn in enumerate(eqns):
        eqn = eqn.lhs - eqn.rhs
        eqn = subst_deriv(eqn)
        eqn = simplify(eqn)
        print(eqn)

        for term in eqn.terms:
            if isinstance(term, AnalogSignal):
                coeff, variable = 1.0, term.name
            elif isinstance(term, Times):
                assert len(term.terms) == 2
                if isinstance(term.terms[0], Constant) and isinstance(term.terms[1], AnalogSignal):
                    coeff, variable = term.terms[0].value, term.terms[1].name
                elif isinstance(term.terms[1], Constant) and isinstance(term.terms[0], AnalogSignal):
                    coeff, variable = term.terms[1].value, term.terms[0].name
                else:
                    raise Exception('Cannot handle this type of expression yet.')
            else:
                raise Exception('Cannot handle this type of expression yet.')

            if variable in unknowns:
                U[row, unknowns[variable]] = coeff
            elif variable in knowns:
                V[row, knowns[variable]] = -coeff
            else:
                raise Exception('Cannot determine if variable is known or unknown!')

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

    return A, B, C, D

def main():
    x = AnalogSignal('x')
    y = AnalogSignal('y')

    sys = eqn_sys_to_lds(eqns=[Deriv(y) == 0.1*(x-y)], inputs=[x], states=[y])

    print(sys)

if __name__ == '__main__':
    main()