import numpy as np
import scipy.signal


def calc_ctle_abcd(fz, fp1, fp2=None, gbw=None):
    num, den = calc_ctle_num_den(fz=fz, fp1=fp1, fp2=fp2, gbw=gbw)
    return scipy.signal.tf2ss(num, den)


def calc_ctle_num_den(fz, fp1, fp2=None, gbw=None):
    # calculate fp2 if needed
    if fp2 is None:
        if gbw is not None:
            fp2 = gbw/(fp1/fz)
        else:
            raise Exception('Must specify fp2 or gbw.')

    # compute angular frequencies
    wz = 2*np.pi * fz
    wp1 = 2*np.pi * fp1
    wp2 = 2*np.pi * fp2

    # calculate numerator and denominator
    num = (1/wz, 1)
    den = (1/wp1 * 1/wp2, 1/wp1 + 1/wp2, 1)

    # return numerator and denominator
    return num, den
