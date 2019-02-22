from copy import deepcopy
from collections import OrderedDict

from msdsl.expr.expr import AnalogConstant, ModelOperator, Sum, Product, AnalogConstantArray, ArithmeticOperator
from msdsl.expr.signals import AnalogSignal

def collect_terms(expr: Sum):
    # initialize list of new operands for expr
    new_operands = []

    # dictionaries of signals and coefficients, both indexed by signal name
    signals = OrderedDict()
    coeffs = {}

    # extract coefficients for all terms
    for operand in expr.operands:
        coeff, signal = None, None

        if isinstance(operand, AnalogSignal):
            coeff, signal = AnalogConstant(1), operand
        elif isinstance(operand, Product):
            if len(operand.operands) == 2:
                if isinstance(operand.operands[0], AnalogConstant) and isinstance(operand.operands[1], AnalogSignal):
                    coeff, signal = operand.operands[0], operand.operands[1]
                elif isinstance(operand.operands[1], AnalogConstant) and isinstance(operand.operands[0], AnalogSignal):
                    coeff, signal = operand.operands[1], operand.operands[0]

        if coeff is not None and signal is not None:
            # add the signal if necessary
            if signal.name not in signals:
                signals[signal.name] = signal
                coeffs[signal.name] = AnalogConstant(0)

            # update the coefficient value
            coeffs[signal.name].value += coeff.value
        else:
            new_operands.append(operand)

    # add collected terms
    for name in signals.keys():
        # extract coefficient and signal
        coeff, signal = coeffs[name], signals[name]

        # if the coefficient is zero, skip the corresponding signal
        if coeff.value == 0:
            pass
        # if the coefficient is one, there is no need to include it
        elif coeff.value == 1:
            new_operands.append(signal)
        # otherwise include the product
        else:
            new_operands.append(coeff*signal)

    # in the event that there are no terms, add the constant zero
    if len(new_operands) == 0:
        new_operands.append(AnalogConstant(0))

    # if there is only one term, return it directly
    if len(new_operands) == 1:
        return new_operands[0]
    else:
        return Sum(new_operands)

def distribute_mult(expr):
    # this optimization is only for the product between a constant and a sum
    if len(expr.operands) != 2:
        return expr

    # find out if one side of the expression is a constant while the other is a summation
    if isinstance(expr.operands[0], AnalogConstant) and isinstance(expr.operands[1], Sum):
        const, plus_op = expr.operands[0], expr.operands[1]
    elif isinstance(expr.operands[1], AnalogConstant) and isinstance(expr.operands[0], Sum):
        const, plus_op = expr.operands[1], expr.operands[0]
    else:
        return expr

    # distribute constant multiplication into summation
    new_operands = []
    const_term = const
    for operand in plus_op.operands:
        new_operands.append(merge_arithmetic_constants(merge_arithmetic_operands(const_term*operand)))

    # return result
    return Sum(new_operands)

    # for a product of terms, set the result to a constant zero if any term is always zero


def main():
    a = AnalogSignal('a')
    b = AnalogSignal('b')
    c = AnalogSignal('c')
    d = AnalogSignal('d')
    e = AnalogSignal('e')

    print(simplify(1*a+2*b+3*c+4*d+7*(c+(d+e)*(4+5))))
    print(simplify((2*a+2*b)/2))
    print(simplify(a/2+(a+2*b)/2))

if __name__ == '__main__':
    main()