from typing import Optional
from numbers import Number
from itertools import chain

from msdsl.generator import CodeGenerator
from msdsl.util import adder_tree

class LinearExpr:
    def __init__(self, mapping=None, const: Optional[Number] = 0):
        # set defaults
        if mapping is None:
            mapping = {}

        # save settings
        self.mapping = mapping
        self.const = const

    # addition

    def __add__(self, other):
        if isinstance(other, Number):
            return LinearExpr(mapping=self.mapping.copy(), const=self.const+other)
        elif isinstance(other, LinearExpr):
            mapping = {}

            for var, coeff in chain(self.mapping.items(), other.mapping.items()):
                if var not in mapping:
                    mapping[var] = 0
                mapping[var] += coeff

            return LinearExpr(mapping=mapping, const=self.const+other.const)
        else:
            raise Exception('Invalid type for other.')

    def __radd__(self, other):
        return self.__add__(other)

    # multiplication

    def __mul__(self, other):
        if isinstance(other, Number):
            return LinearExpr(mapping={var: coeff*other for var, coeff in self.mapping.items()},
                              const=self.const*other)
        else:
            raise Exception('Invalid type for other.')

    def __rmul__(self, other):
        return self.__mul__(other)

    # subtraction

    def __sub__(self, other):
        return self.__add__(-other)

    def __rsub__(self, other):
        return (-self).__add__(other)

    # negation

    def __neg__(self):
        return -1.0*self

    # division

    def __truediv__(self, other):
        return (1.0/other) * self

    # implementation

    def run_generator(self, gen: CodeGenerator):
        # compute products of coefficients with signals
        prod_vars = [gen.mul_const_real(coeff, var) for var, coeff in self.mapping.items() if coeff != 0]

        # if there is a non-zero constant in the update expression, include it in the list of terms to be summed
        if self.const != 0:
            prod_vars.append(gen.make_const_real(self.const))

        # add up all of these products
        return adder_tree(prod_vars,
                          zero_func=lambda: gen.make_const_real(0),
                          add_func=lambda a, b: gen.add_real(a, b))

def main():
    a = LinearExpr({'a': 1.2}, 3.4)
    b = LinearExpr({'a': 5.6, 'b': 7.8}, 9.1)

    expr = (a+b)/3
    print(expr.mapping, expr.const)

if __name__ == '__main__':
    main()