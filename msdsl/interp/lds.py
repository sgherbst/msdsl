import numpy as np
from math import factorial
from scipy.linalg import expm

# returns the indefinite integral(e^(xM)*x^k)
# intended to be used in calculating definited integrals
# see: https://en.wikipedia.org/wiki/List_of_integrals_of_exponential_functions#Integrals_of_polynomials
def calc_expm_indef_integral(x, M, k):
    retval = np.zeros(M.shape, dtype=float)
    for i in range(0, k+1):
        mat = np.linalg.matrix_power(M, -k+i-1)
        coeff = ((-1)**(k-i))*(factorial(k)/factorial(i))
        retval += coeff*mat*(x**i)
    retval = retval.dot(expm(x*M))
    return retval


# returns the definite integral(e^{xM}*x^k) from x0 to x1
def calc_expm_integral(M, k, x0, x1):
    return (calc_expm_indef_integral(x=x1, M=M, k=k) -
            calc_expm_indef_integral(x=x0, M=M, k=k))


# returns definite integral:
# c*e^((p*th-tau)*A)*b*((tau-j*th)/th)^k
# from j*th to (j+1)*th
def calc_lds_f(A, B, C, th, p, j, k):
    return th * C.dot(expm((p-j)*th*A)).dot(calc_expm_integral(-th*A, k, 0, 1).dot(B))


# returns definite integral:
# e^((t-tau)*A)*b*((tau-j*th)/th)^k
# over the intersection of [0, t] and [j*th, (j+1)*th]
# (was previously called f_tilde)
def calc_lds_g(A, B, th, j, k, t):
    if t < (j*th):
        return np.zeros_like(B)
    else:
        ub = min(1, (t/th)-j)
        return th*expm((t-(j*th))*A).dot(calc_expm_integral(-th*A, k, 0, ub).dot(B))
