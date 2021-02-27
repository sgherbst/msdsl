import numpy as np
import scipy.optimize


def v2db(x):
    return 20*np.log10(x)


def db2v(x):
    return 10**(-x/20)


def tanhsat(v, vsat):
    return vsat * np.tanh(v / np.abs(vsat))


def calc_tanh_vsat(compr, units=None, veval=1.0):
    # calculate attenuation
    if units is not None:
        if units in {'dB'}:
            compr = db2v(compr)
        else:
            raise Exception(f'Unknown units: {units}')

    # solve nonlinear equation for vsat
    func = lambda vsat: tanhsat(veval, vsat) - compr
    root = scipy.optimize.fsolve(func, veval)  # second argument is the initial guess
    vsat = np.abs(root[0])

    # return vsat
    return vsat
