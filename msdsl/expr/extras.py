from typing import Union, List
from numbers import Number, Integral
from msdsl.expr.expr import ModelExpr, concatenate, BitwiseAnd, array, LessThan, GreaterThan, Product, Sum, EqualTo, Array, Constant
from msdsl.expr.signals import AnalogSignal, DigitalSignal

import sympy as sp

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