from typing import List, Dict

from msdsl.eqn.deriv import Deriv
from msdsl.eqn.cases import EqnCase
from msdsl.expr.expr import ModelOperator, ModelExpr
from msdsl.expr.signals import AnalogSignal, DigitalSignal, AnalogInput, AnalogOutput, DigitalInput, DigitalOutput, \
                               Signal

def names(l: List[Signal]):
    return [elem.name for elem in l]

def walk_expr(expr, cond_fun):
    retval = []

    if cond_fun(expr):
        retval.append(expr)

    if isinstance(expr, ModelOperator):
        retval = []
        for operand in expr.operands:
            retval.extend(walk_expr(operand, cond_fun))

    return retval

def get_all_signal_names(eqns: List[ModelExpr]):
    all_signals = [signal for eqn in eqns for signal in walk_expr(eqn, lambda e: isinstance(e, AnalogSignal))]
    return set(names(all_signals))

def get_deriv_names(eqns: List[ModelExpr]):
    derivs = [deriv for eqn in eqns for deriv in walk_expr(eqn, lambda e: isinstance(e, Deriv))]
    return set(names(derivs))

def get_state_names(eqns: List[ModelExpr]):
    states = [deriv.signal for eqn in eqns for deriv in walk_expr(eqn, lambda e: isinstance(e, Deriv))]
    return set(names(states))

def get_sel_bit_names(eqns: List[ModelExpr]):
    eqn_cases = [eqn_case for eqn in eqns for eqn_case in walk_expr(eqn, lambda e: isinstance(e, EqnCase))]
    sel_bits = [sel_bit for eqn_case in eqn_cases for sel_bit in eqn_case.sel_bits]
    return set(names(sel_bits))

def get_analog_input_names(signals: Dict[str, Signal]):
    return set(names([signal for signal in signals.values() if isinstance(signal, AnalogInput)]))

def get_analog_output_names(signals: Dict[str, Signal]):
    return set(names([signal for signal in signals.values() if isinstance(signal, AnalogOutput)]))

def get_digital_input_names(signals: Dict[str, Signal]):
    return set(names([signal for signal in signals.values() if isinstance(signal, DigitalInput)]))

def get_digital_output_names(signals: Dict[str, Signal]):
    return set(names([signal for signal in signals.values() if isinstance(signal, DigitalOutput)]))

def main():
    print(get_all_signal_names([AnalogSignal('a') == AnalogSignal('b')]))
    print(get_deriv_names([AnalogSignal('a') == Deriv(AnalogSignal('b'))]))
    print(get_state_names([AnalogSignal('a') == Deriv(AnalogSignal('b'))]))
    print(get_sel_bit_names([AnalogSignal('a') == EqnCase([1, 2], [DigitalSignal('s')])]))

if __name__ == '__main__':
    main()