# unused optimized code

# def times(terms: List[ModelExpr]):
#     # consolidate products
#     new_terms = []
#     for term in terms:
#         if isinstance(term, Times):
#             new_terms.extend(term.terms)
#         else:
#             new_terms.append(term)
#     terms = new_terms
#
#     # consolidate constants
#     other_terms = []
#     const_product = 1
#     for term in terms:
#         if isinstance(term, Constant):
#             const_product *= term.value
#         else:
#             other_terms.append(term)
#     terms = other_terms
#
#     if const_product == 0:
#         return Constant(0)
#     elif const_product != 1:
#         terms.append(Constant(const_product))
#
#     # when two items are multiplied together and one is a constant, make sure the constant comes first (to
#     # simplify subsequent processing)
#     if len(terms)==2 and isinstance(terms[0], Constant):
#         return const_times(terms[0], terms[1])
#     elif len(terms)==2 and isinstance(terms[1], Constant):
#         return const_times(terms[1], terms[0])
#     else:
#         return Times(terms)

# def plus(terms: List[ModelExpr]):
#     # consolidate sums
#     new_terms = []
#     for term in terms:
#         if isinstance(term, Plus):
#             new_terms.extend(term.terms)
#         else:
#             new_terms.append(term)
#     terms = new_terms
#
#     # consolidate constants
#     other_terms = []
#     const_sum = 0
#     for term in terms:
#         if isinstance(term, Constant):
#             const_sum += term.value
#         else:
#             other_terms.append(term)
#     terms = other_terms
#
#     if const_sum != 0:
#         terms.append(Constant(const_sum))
#
#     # group terms
#     other_terms = []
#     coeff_dict = {}
#
#     for term in terms:
#         if isinstance(term, Signal):
#             name = term.name
#             coeff = 1
#         elif isinstance(term, ConstTimes) and isinstance(term.expr, Signal):
#             name = term.expr.name
#             coeff = term.coeff.value
#         else:
#             other_terms.append(term)
#             continue
#
#         if name not in coeff_dict:
#             coeff_dict[name] = 0
#         coeff_dict[name] += coeff
#
#     terms = other_terms
#
#     for name, coeff in coeff_dict.items():
#         terms.append(coeff*Signal(name))
#
#     return Plus(terms)