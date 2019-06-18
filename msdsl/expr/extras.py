from typing import Union, List
from numbers import Number, Integral
from msdsl.expr.expr import ModelExpr, concatenate, BitwiseAnd, array

def all_between(x: List[ModelExpr], lo: Union[Number, ModelExpr], hi: Union[Number, ModelExpr]) -> ModelExpr:
    """
    Limit checking. Check if a list of ModelExpr objects provided in *x* is larger than *lo* and smaller than *hi*.

    :param x:   List of ModelExpr that are to be checked
    :param lo:  Lower limit
    :param hi:  Upper limit
    :return:    boolean, 1 if x is within limits, 0 otherwise
    """
    return BitwiseAnd([between(elem, lo, hi) for elem in x])

def between(x: ModelExpr, lo: Union[Number, ModelExpr], hi: Union[Number, ModelExpr]) -> ModelExpr:
    """
    Limit checking. Check if a ModelExpr object provided in *x* is larger than *lo* and smaller than *hi*.

    :param x:   ModelExpr that is to be checked
    :param lo:  Lower limit
    :param hi:  Upper limit
    :return:    boolean, 1 if x is within limits, 0 otherwise
    """
    return (lo <= x) & (x <= hi)

def replicate(x: ModelExpr, n: Integral):
    return concatenate([x]*n)

def if_(condition, then, else_):
    """
    Conditional statement. Condition *condition* is evaluated and if result is true, action *then* is executed, otherwise
    action *else_*.

    :param condition:   Conditional expression that is to be evaluated
    :param then:        Action to be executed for True case
    :param else_:       Action to be executed for False case
    :return:            Boolean
    """
    return array([else_, then], condition)