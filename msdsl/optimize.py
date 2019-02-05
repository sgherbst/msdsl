from msdsl.expr import Constant, ListOp, Plus, Times, Signal, AnalogArray

def expand_list_op_terms(expr: ListOp):
    terms = []
    op_cls = type(expr)

    for term in expr.terms:
        if isinstance(term, op_cls):
            terms.extend(term.terms)
        else:
            terms.append(term)

    return op_cls(terms)

def collapse_list_op_constants(expr: ListOp):
    terms = []
    op_cls = type(expr)

    const_term = Constant(expr.identity)

    for term in expr.terms:
        if isinstance(term, Constant):
            const_term = Constant(expr.func([const_term.value, term.value]))
        else:
            terms.append(term)

    if const_term.value != expr.identity:
        terms.append(const_term)

    # in the unlikely case that the product just evaluates to the default, add that value back
    if len(terms) == 0:
        terms.append(Constant(expr.identity))
    elif len(terms) == 1:
        return terms[0]
    else:
        return op_cls(terms)

def simplify_list_op(expr: ListOp):
    op_cls = type(expr)

    expr = op_cls([simplify(term) for term in expr.terms])
    expr = expand_list_op_terms(expr)
    expr = collapse_list_op_constants(expr)

    return expr

def collect_terms(expr: Plus):
    terms = []
    pairs = {}

    # extract coefficients for all terms
    for term in expr.terms:
        coeff, signal = None, None

        if isinstance(term, Signal):
            coeff, signal = Constant(1), term
        elif isinstance(term, Times):
            if len(term.terms) == 2:
                if isinstance(term.terms[0], Constant) and isinstance(term.terms[1], Signal):
                    coeff, signal = term.terms[0], term.terms[1]
                elif isinstance(term.terms[1], Constant) and isinstance(term.terms[0], Signal):
                    coeff, signal = term.terms[1], term.terms[0]

        if not ((coeff is not None) and (signal is not None)):
            terms.append(term)
        else:
            if signal.name not in pairs:
                pairs[signal.name] = (Constant(0), signal)
            pairs[signal.name] = (Constant(pairs[signal.name][0].value + coeff.value), signal)

    # add collected terms
    for coeff, signal in pairs.values():
        if coeff.value == 0:
            pass
        elif coeff.value == 1:
            terms.append(signal)
        else:
            terms.append(coeff*signal)

    # in the event that there are no terms, add the constant zero
    if len(terms) == 0:
        terms.append(Constant(0))

    # if there is only one term, return it directly
    if len(terms) == 1:
        return terms[0]
    else:
        return Plus(terms)

def distribute_mult(expr):
    # this optimization is only for the product between a constant and a sum
    if len(expr.terms) != 2:
        return expr

    # find out if one side of the expression is a constant while the other is a summation
    if isinstance(expr.terms[0], Constant) and isinstance(expr.terms[1], Plus):
        const, plus_op = expr.terms[0], expr.terms[1]
    elif isinstance(expr.terms[1], Constant) and isinstance(expr.terms[0], Plus):
        const, plus_op = expr.terms[1], expr.terms[0]
    else:
        return expr

    # distribute constant multiplication into summation
    terms = []
    const_term = const
    for plus_term in plus_op.terms:
        terms.append(collapse_list_op_constants(expand_list_op_terms(const_term*plus_term)))

    # return result
    return Plus(terms)

def simplify(expr):
    if isinstance(expr, ListOp):
        expr = simplify_list_op(expr)

    if isinstance(expr, Times):
        # if any of the terms in the product are a constant zero, set the result to a constant zero
        if any((isinstance(term, Constant) and term.value==0) or
               (isinstance(term, AnalogArray) and all(elem==0 for elem in term.terms))
               for term in expr.terms):
            expr = Constant(0)

    if isinstance(expr, Times):
        # try to distribute constant into summation
        expr = distribute_mult(expr)

    if isinstance(expr, Plus):
        # collect the coefficients for each signal
        expr = collect_terms(expr)

    return expr

def main():
    from msdsl.expr import AnalogSignal

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