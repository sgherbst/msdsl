from numbers import Number

import numpy as np
import scipy.linalg

class LDS:
    def __init__(self, A=None, B=None, C=None, D=None):
        # save settings
        self.A = A
        self.B = B
        self.C = C
        self.D = D

    def discretize(self, dt: Number):
        # discretize A
        if self.A is not None:
            A_tilde = scipy.linalg.expm(dt * self.A)
        else:
            A_tilde = None

        # discretize B
        if self.A is not None and self.B is not None:
            I = np.eye(*self.A.shape) # identity matrix with shape of A
            B_tilde = np.linalg.solve(self.A, (A_tilde - I).dot(self.B))
        else:
            B_tilde = None

        # discretize C
        if self.C is not None:
            C_tilde = self.C.copy()
        else:
            C_tilde = None

        # discretize D
        if self.D is not None:
            D_tilde = self.D.copy()
        else:
            D_tilde = None

        # return result
        return LDS(A=A_tilde, B=B_tilde, C=C_tilde, D=D_tilde)

    # overloaded methods

    def __str__(self):
        # build up list of lines
        retval = ['*** Linear Dynamical System ***']
        for k, (name, mat) in enumerate([('A', self.A), ('B', self.B), ('C', self.C), ('D', self.D)]):
            retval.append('')
            retval.append(f'{name} matrix')
            retval.append(str(mat))

        # add newlines
        retval = '\n'.join(retval)

        # return result
        return retval

class LdsCollection:
    def __init__(self):
        self.A = None
        self.B = None
        self.C = None
        self.D = None

    def append(self, lds: LDS):
        # Add extra dimension to each array
        A = lds.A[:, :, np.newaxis] if lds.A is not None else None
        B = lds.B[:, :, np.newaxis] if lds.B is not None else None
        C = lds.C[:, :, np.newaxis] if lds.C is not None else None
        D = lds.D[:, :, np.newaxis] if lds.D is not None else None

        # Update each array
        self.A = np.concatenate((self.A, A), axis=2) if self.A is not None else A
        self.B = np.concatenate((self.B, B), axis=2) if self.B is not None else B
        self.C = np.concatenate((self.C, C), axis=2) if self.C is not None else C
        self.D = np.concatenate((self.D, D), axis=2) if self.D is not None else D
