from typing import List, Set, Union

from msdsl.expr.expr import ModelOperator
from msdsl.expr.signals import Signal

def signal_name(s: Signal):
    return s.name

def signal_names(l: Union[List[Signal], Set[Signal]]):
    return [signal_name(elem) for elem in l]

def walk_expr(expr, cond_fun):
    retval = []

    if cond_fun(expr):
        retval.append(expr)

    if isinstance(expr, ModelOperator):
        retval = []
        for operand in expr.operands:
            retval.extend(walk_expr(operand, cond_fun))

    return retval
