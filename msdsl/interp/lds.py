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


# calculates the A_tilde matrix
def calc_lds_a_tilde(A, t):
    return expm(t*A)


# calculates the B_tilde matrix
def calc_lds_b_tilde(A, B, W, t):
    # extract number of points and order from the shape of W
    npts = W.shape[0]
    order = W.shape[1] - 1

    # calculate timestep between interpolation points
    th = 1/(npts-1)

    # calculate f_tilde
    f_tilde = []
    for j in range(npts):
        f_tilde.append([])
        for k in range(order+1):
            f_tilde_jk = calc_lds_g(A=A, B=B, th=th, j=j, k=k, t=t)
            f_tilde[-1].append(f_tilde_jk)

    # calculate b_tilde
    b_tilde = []
    for i in range(npts):
        b_tilde_i = np.zeros_like(B)
        for j in range(npts):
            for k in range(order + 1):
                b_tilde_i += W[j, k, i] * f_tilde[j][k]
        b_tilde.append(b_tilde_i)

    # return b_tilde
    return b_tilde


# calculates C_tilde matrix
def calc_lds_c_tilde(A, C, npts):
    # build up matrix
    c_tilde = [None] * npts
    dtvec = np.linspace(0, 1, npts)
    for p in range(npts):
        c_tilde[p] = C.dot(expm(dtvec[p] * A))

    # return matrix
    return c_tilde


# calculates the D_tilde matrix
def calc_lds_d_tilde(A, B, C, D, W):
    # extract number of points and order from the shape of W
    npts = W.shape[0]
    order = W.shape[1] - 1

    # calculate timestep between interpolation points
    th = 1/(npts-1)

    # build up matrix
    d_tilde = np.zeros((npts, npts), dtype=float)
    for p in range(npts):
        for i in range(npts):
            d_tilde[p, i] += D * W[p, 0, i]
            for j in range(p):
                for k in range(order + 1):
                    d_tilde[p, i] += W[j, k, i] * calc_lds_f(A, B, C, th, p, j, k)

    # return matrix
    return d_tilde


# consumes and produces splines for LDS behavior
class SplineLDS:
    def __init__(self, A, B, C, D, W):
        # save settings
        self.A = A
        self.B = B
        self.C = C
        self.D = D
        self.W = W

        # precompute matrices that can be precomputed
        self.C_tilde = calc_lds_c_tilde(A=self.A, C=self.C, npts=self.npts)
        self.D_tilde = calc_lds_d_tilde(A=self.A, B=self.B, C=self.C, D=self.D, W=self.W)

    def A_tilde(self, t):
        return calc_lds_a_tilde(A=self.A, t=t)

    def B_tilde(self, t):
        return calc_lds_b_tilde(A=self.A, B=self.B, W=self.W, t=t)

    @property
    def npts(self):
        return self.W.shape[0]

    @property
    def order(self):
        return self.W.shape[1] - 1
