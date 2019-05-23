from collections import OrderedDict

from msdsl.expr.expr import Constant, Sum, sum_op, Product
from msdsl.expr.signals import Signal

def distribute_mult(expr):
    if isinstance(expr, Sum):
        # distribute multiplication in a bottom-up fashion
        operands = [distribute_mult(operand) for operand in expr.operands]
        return sum_op(operands)
    elif isinstance(expr, Product) and len(expr.operands) == 2:
        # distribute multiplication in a bottom-up fashion
        operands = [distribute_mult(operand) for operand in expr.operands]

        if isinstance(operands[0], Constant) and isinstance(operands[1], Sum):
            const, sum_operands = operands[0], operands[1].operands
        elif isinstance(operands[1], Constant) and isinstance(operands[0], Sum):
            const, sum_operands = operands[1], operands[0].operands
        else:
            return expr

        # distribute constant multiplication into summation
        return sum_op([const*sum_operand for sum_operand in sum_operands])
    else:
        return expr

def extract_coeffs(expr: Sum):
    # initialize
    pairs, others = [], []

    # extract coefficients for all terms
    if isinstance(expr, Signal):
        pairs.append((1, expr))
    else:
        for operand in expr.operands:
            if isinstance(operand, Signal):
                pairs.append((1, operand))
            elif isinstance(operand, Product) and len(operand.operands) == 2:
                if isinstance(operand.operands[0], Constant) and isinstance(operand.operands[1], Signal):
                    pairs.append((operand.operands[0].value, operand.operands[1]))
                elif isinstance(operand.operands[1], Constant) and isinstance(operand.operands[0], Signal):
                    pairs.append((operand.operands[1].value, operand.operands[0]))
                else:
                    others.append(operand)
            else:
                others.append(operand)

    # return result
    return pairs, others

def collect_terms(expr):
    # only apply this operation to Sum expressions
    if not isinstance(expr, Sum):
        return expr

    # extract pairs of coefficients and signal names
    pairs, others = extract_coeffs(expr)
    signals = {}

    # collect terms with same coefficient
    coeffs = OrderedDict()
    for coeff, signal in pairs:
        if signal.name not in coeffs:
            coeffs[signal.name] = 0
            signals[signal.name] = signal
        coeffs[signal.name] += coeff

    # construct full expression
    operands = [signals[key]*val for key, val in coeffs.items()]
    operands += others

    # return the result
    return sum_op(operands)

def main():
    from msdsl.expr.signals import AnalogSignal

    a = AnalogSignal('a')
    b = AnalogSignal('b')
    c = AnalogSignal('c')
    d = AnalogSignal('d')
    e = AnalogSignal('e')

    print(distribute_mult(1*a+2*b+3*(4+5*(6+7*c))))

    pairs, others = extract_coeffs(a+2*b+3*c)
    print('pairs: ' + str({k: v.name for k, v in pairs}))
    print('others: ' + str([str(other) for other in others]))

    def simplify(expr):
        return collect_terms(distribute_mult(expr))

    print(simplify(1*a+2*b+3*c+4*d+7*(c+(d+e)*(4+5))))
    print(simplify((2*a+2*b)/2))
    print(simplify(a/2+(a+2*b)/2))
    print(simplify(a+b-b))
    print(simplify(a+2*(1-b)+1*(2*b-a)-2))

if __name__ == '__main__':
    main()