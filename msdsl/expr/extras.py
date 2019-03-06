from typing import Union, List
from numbers import Number, Integral
from msdsl.expr.expr import ModelExpr, concatenate, BitwiseAnd

def all_between(x: List[ModelExpr], lo: Union[Number, ModelExpr], hi: Union[Number, ModelExpr]) -> ModelExpr:
    return BitwiseAnd([between(elem, lo, hi) for elem in x])

def between(x: ModelExpr, lo: Union[Number, ModelExpr], hi: Union[Number, ModelExpr]) -> ModelExpr:
    return (lo <= x) & (x <= hi)

def replicate(x: ModelExpr, n: Integral):
    return concatenate([x]*n)