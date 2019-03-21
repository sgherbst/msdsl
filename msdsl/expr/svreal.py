from numbers import Number

# Handling symbolic exponents

class ExponentExpr:
    pass

class ExponentOf(ExponentExpr):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return 'ExponentOf(' + self.name + ')'

# Handling symbolic widths

class WidthExpr:
    pass

class WidthOf(WidthExpr):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return 'WidthOf(' + self.name + ')'

# Handling symbolic ranges

class RangeExpr:
    def __add__(self, other):
        return range_sum([self, other])

    def __mul__(self, other):
        return range_product([self, other])

    def __radd__(self, other):
        return self.__add__(other)

    def __rmul__(self, other):
        return self.__mul__(other)

class RangeOf(RangeExpr):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return 'RangeOf(' + self.name + ')'

class ParamRange(RangeExpr):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return 'ParamRange(' + self.name + ')'

class UndefinedRange(RangeExpr):
    def __str__(self):
        return 'UndefinedRange'

# Generic range operator -- not be directly instantiated

class RangeOperator(RangeExpr):
    initial = None

    def __init__(self, operands):
        self.operands = operands

    @classmethod
    def function(cls, a, b):
        raise NotImplementedError

    @classmethod
    def merge_with_same_operator(cls, operands):
        # merge operators of the same type
        new_operands = []
        for operand in operands:
            if isinstance(operand, cls):
                new_operands.extend(operand.operands)
            else:
                new_operands.append(operand)

        # set operands of the expression and return it
        return new_operands

    @classmethod
    def merge_constants(cls, operands):
        # extract and process constants
        new_operands = []
        const_term = cls.initial
        for operand in operands:
            if isinstance(operand, Number):
                const_term = cls.function(const_term, operand)
            else:
                new_operands.append(operand)

        # add the const_term as a new operand if necessary
        if const_term != cls.initial:
            new_operands.append(const_term)

        return new_operands

    @classmethod
    def flatten(cls, operands):
        if len(operands) == 0:
            return cls.initial
        elif len(operands) == 1:
            return operands[0]
        else:
            return cls(operands)

# Sum

def range_sum(operands):
    # optimizations
    operands = RangeSum.merge_with_same_operator(operands)
    operands = RangeSum.merge_constants(operands)

    # return result
    return RangeSum.flatten(operands)

class RangeSum(RangeOperator):
    initial = 0

    @classmethod
    def function(cls, a, b):
        return a + b

    def __str__(self):
        return '(' + '+'.join(str(operand) for operand in self.operands) + ')'

# Product

def range_product(operands):
    # optimizations
    operands = RangeProduct.merge_with_same_operator(operands)
    operands = RangeProduct.merge_constants(operands)
    operands = RangeProduct.check_for_zero(operands)

    # return result
    return RangeProduct.flatten(operands)

class RangeProduct(RangeOperator):
    initial = 1

    @classmethod
    def function(cls, a, b):
        return a*b

    @classmethod
    def check_for_zero(cls, operands):
        if any((isinstance(operand, Number) and operand == 0) for operand in operands):
            return [0]
        else:
            return operands

    def __str__(self):
        return '(' + '*'.join(str(operand) for operand in self.operands) + ')'

# Max

def range_max(operands):
    # optimizations
    operands = RangeMax.merge_with_same_operator(operands)
    operands = RangeMax.merge_constants(operands)

    # return result
    return RangeMax.flatten(operands)

class RangeMax(RangeOperator):
    initial = -float('inf')

    @classmethod
    def function(cls, a, b):
        return max(a, b)

    def __str__(self):
        return 'max(' + ', '.join(str(operand) for operand in self.operands) + ')'

# Testing

def main():
    print(3+RangeOf('a'))
    print(range_max([3, 4, 5, RangeOf('b'), RangeOf('c')]))
    print(range_max([3, 4, 5]))

if __name__ == '__main__':
    main()