from typing import Union

from numbers import Number

from msdsl.expr.svreal import RangeExpr, RangeOf, RangeMax, RangeSum, RangeProduct, WidthOf, WidthExpr, ExponentExpr, \
    ExponentOf, RangeOperator, ParamRange
from msdsl.generator.tree_op import tree_op

def max_op(a, b):
    if a is not None:
        if b is not None:
            return f'`MAX_MATH({a}, {b})'
        else:
            return a
    else:
        if b is not None:
            return b
        else:
            raise ValueError('Cannot compute the maximum when both arguments are None.')

def compile_range_expr(expr: Union[RangeExpr, Number]):
    if expr is None:
        return None
    elif isinstance(expr, Number):
        return str(expr)
    elif isinstance(expr, RangeOf):
        return f'`RANGE_PARAM_REAL({expr.name})'
    elif isinstance(expr, ParamRange):
        return f'`CONST_RANGE_REAL({expr.name})'

    # otherwise it must be a RangeOperator
    assert isinstance(expr, RangeOperator), 'Expected a RangeOperator here.'
    operands = [compile_range_expr(operand) for operand in expr.operands]

    if isinstance(expr, RangeSum):
        return '(' + '+'.join(operands) + ')'
    elif isinstance(expr, RangeProduct):
        return '(' + '*'.join(operands) + ')'
    elif isinstance(expr, RangeMax):
        return tree_op(operands=operands, operator=max_op)
    else:
        raise Exception('Range expression not handled: ' + expr.__class__.__name__)

def compile_width_expr(expr: Union[WidthExpr, Number]):
    if expr is None:
        return None
    elif isinstance(expr, Number):
        return str(expr)
    elif isinstance(expr, WidthOf):
        return f'`WIDTH_PARAM_REAL({expr.name})'
    else:
        raise Exception('Width expression not handled: ' + expr.__class__.__name__)

def compile_exponent_expr(expr: Union[ExponentExpr, Number]):
    if expr is None:
        return None
    elif isinstance(expr, Number):
        return str(expr)
    elif isinstance(expr, ExponentOf):
        return f'`EXPONENT_PARAM_REAL({expr.name})'
    else:
        raise Exception('Exponent expression not handled: ' + expr.__class__.__name__)

def main():
    from msdsl.expr.svreal import range_max
    a = RangeOf('a')
    b = RangeOf('b')
    c = RangeOf('c')
    d = RangeOf('d')

    print(compile_range_expr((a+b+1)*4*2+5+7))
    print(compile_range_expr(range_max([a, b, c, d])))

if __name__ == '__main__':
    main()