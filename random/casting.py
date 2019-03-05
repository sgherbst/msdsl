#
# def num2expr(value: Number, value_type: ExprType):
#     if value_type is ExprType.REAL:
#         return AnalogConstant(value)
#     elif value_type is ExprType.SIGNED_INTEGER:
#         return DigitalConstant(value)
#     else:
#         raise NotImplementedError
#
# def get_value_type(operands):
#     # find
#     expr_type_value = -1
#     for operand in operands:
#         if isinstance(operand, ModelExpr):
#             expr_type_value = max(operand.expr_type.value, expr_type_value)
#
#     # get a list of the operands that are ModelExpr
#     model_expr_list = [model_expr for model_expr in operands if isinstance(model_expr, ModelExpr)]
#
#     # consider all cases
#     if len(model_expr_list) == 0:
#         return None
#     elif all(model_expr.expr_type is ExprType.REAL for model_expr in model_expr_list):
#         return ExprType.REAL
#     elif all(model_expr.expr_type is ExprType.SIGNED_INTEGER for model_expr in model_expr_list):
#         return ExprType.SIGNED_INTEGER
#     else:
#         return None
#
# def cast_numbers(operands, value_type):
#     return [operand if isinstance(operand, ModelExpr) else num2expr(operand, value_type) for operand in operands]