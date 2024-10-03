from itertools import count

class Namer:
    def __init__(self, prefix: str='tmp', max_attempts=100):
        # save settings
        self.prefix = prefix
        self.max_attempts = max_attempts

        # initialize
        self.names = set()
        self.count = count()

    def add_name(self, name):
        assert name not in self.names, 'The request name ' + str(name) + ' has already been taken.'
        self.names.add(name)

    def _next_name(self):
        # not intended to be called directly, since the name may conflict with existing names
        return self.prefix + str(next(self.count))

    def __next__(self):
        for _ in range(self.max_attempts):
            name = self._next_name()
            if name not in self.names:
                self.add_name(name)
                return name
        else:
            raise Exception('Failed to produce a temporary name.')

def warn(s):
    print('WARNING: ' + str(s))

def list2dict(l):
    return {elem: k for k, elem in enumerate(l)}


def msdsl_ast_to_sympy(ast):
    """
    Convert an AST from msdsl to a sympy expression.
    """
    if isinstance(ast, LessThan):
        return sp.Lt(msdsl_ast_to_sympy(ast.lhs), msdsl_ast_to_sympy(ast.rhs))
    elif isinstance(ast, GreaterThan):
        return sp.Gt(msdsl_ast_to_sympy(ast.lhs), msdsl_ast_to_sympy(ast.rhs))
    elif isinstance(ast, Product):
        accum = 1  # Corrected from 0 to 1 to properly accumulate products
        for operand in ast.operands:
            accum *= msdsl_ast_to_sympy(operand)
        return accum
    elif isinstance(ast, Sum):
        accum = 0
        for operand in ast.operands:
            accum += msdsl_ast_to_sympy(operand)
        return accum
    elif isinstance(ast, EqualTo):
        return sp.Eq(msdsl_ast_to_sympy(ast.lhs), msdsl_ast_to_sympy(ast.rhs))
    elif isinstance(ast, Array):
        elements = ast.operands[:-1]
        address = msdsl_ast_to_sympy(ast.operands[-1])
        return sp.Piecewise(*[(msdsl_ast_to_sympy(elem), address if i == 1 else sp.Not(address)) for i, elem in enumerate(elements)])
    elif isinstance(ast, Constant):
        return ast.value
    elif isinstance(ast, AnalogSignal) or isinstance(ast, DigitalSignal):
        return sp.Symbol(str(ast))
    else:
        raise Exception(f"Unsupported AST node: {type(ast)}")

def main():
    # list2dict tests
    print(list2dict(['a', 'b', 'c']))

if __name__ == '__main__':
    main()

