import numpy as np
from msdsl.interp.nonlin import v2db, db2v, tanhsat, calc_tanh_vsat


def test_dB():
    assert np.isclose(v2db(0.1), -20)
    assert np.isclose(v2db(1), 0)
    assert np.isclose(v2db(10), +20)

    assert np.isclose(db2v(-20), 0.1)
    assert np.isclose(db2v(0), 1)
    assert np.isclose(db2v(+20), 10)


def test_sat():
    assert np.isclose(tanhsat(0.5, 1.23), 0.47416536379)
    assert np.isclose(tanhsat(0.76, 1.23), 0.67607509587)
    assert np.isclose(tanhsat(1.0, 1.23), 0.82563301112)
    assert np.isclose(tanhsat(2.3, 1.23), 1.17291170563)


def test_vsat_finder():
    vsat = calc_tanh_vsat(0.9, veval=0.6)
    assert np.isclose(tanhsat(0.6, vsat), 0.54)

    vsat = calc_tanh_vsat(-1, 'dB', veval=0.8)
    assert np.isclose(tanhsat(0.8, vsat), 0.7130007505)
