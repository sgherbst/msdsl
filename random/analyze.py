# from copy import deepcopy
# from numbers import Integral, Real, Number
#
# from msdsl.expr.format import Format, RealFormat, IntegerFormat, SignedIntegerFormat, UnsignedIntegerFormat
# from msdsl.expr.expr import RealConstant, IntegerConstant, ModelExpr, ModelOperator, Constant, BitwiseOperator, \
#                             ComparisonOperator, Concatenate, ArithmeticOperator
#
#
#
#
#
# def _set_format(expr):
#     # bottom-up type determination
#     if isinstance(expr, ModelOperator):
#         expr.operands = [_set_format(operand) for operand in expr.operands]
#
#     # promote operand types as necessary
#     if isinstance(expr, (ArithmeticOperator, ComparisonOperator)):
#         promoted_type = get_promoted_type(expr.operands)
#         expr.operands = [promote(operand, promoted_type) for operand in expr.operands]
#
#     if not isinstance(expr, ModelExpr):
#         raise Exception('Encountered object that is neither a numeric constant nor a ModelExpr: {expr}')
#
#     if isinstance(expr, ModelOperator):
#         expr.operands = [_subst_deriv(operand) for operand in expr.operands]
#         return expr
#     elif isinstance(expr, Deriv):
#         return AnalogSignal(deriv_str(expr.signal.name))
#     else:
#         return expr
#
# def set_format(expr):
#     # the deepcopy is needed because _set_format modifies expr
#     return _set_format(expr=deepcopy(expr))