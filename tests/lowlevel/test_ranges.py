import pytest
import numpy as np
from scipy.linalg import expm
from pathlib import Path

from msdsl.templates.channel import ChannelModel, S4PModel
from msdsl.templates.saturation import SaturationModel
from msdsl.templates.lds import LDSModel, CTLEModel

THIS_DIR = Path(__file__).resolve().parent
TOP_DIR = THIS_DIR.parent.parent
S4P_FILE = TOP_DIR / 'peters_01_0605_B1_thru.s4p'


def chk_range(calc, sim, tol=0.05):
    # make sure range is an overestimate
    assert calc[0] <= sim[0]
    assert calc[1] >= sim[1]

    # make sure it is not too much of an overestimate
    assert calc[0] >= (1 + tol) * sim[0]
    assert calc[1] <= (1 + tol) * sim[1]


def test_chan_range_simple():
    t_step = [0, 1.0, 2.0, 3.0]
    v_step = [0.0, 0.9, 1.5, 1.0]

    min_val_meas, max_val_meas = ChannelModel.calc_out_range(
        t_step=t_step, v_step=v_step, in_range=[-0.5, 1], dt=1, num_terms=10)

    print(f'min_val_meas: {min_val_meas}')
    print(f'max_val_meas: {max_val_meas}')

    # expected values calculated by hand
    min_val_expt = -1.25
    max_val_expt = +1.75

    assert np.isclose(min_val_meas, min_val_expt)
    assert np.isclose(max_val_meas, max_val_expt)


def test_chan_range_realistic(dtmax=62.5e-12, num_spline=4, tdur=10e-9):
    tover = dtmax/(num_spline-1)
    num_terms = int(round(tdur/dtmax))
    m = S4PModel(
        module_name='model', s4p_file=S4P_FILE, tdur=tdur, tover=tover,
        dtmax=dtmax, num_spline=num_spline, num_terms=num_terms)

    min_val_meas = m.out_range[0]
    max_val_meas = m.out_range[1]

    print(f'min_val_meas: {min_val_meas}')
    print(f'max_val_meas: {max_val_meas}')

    # expected values calculated from a previous run
    min_val_expt = -1.0776512391893247
    max_val_expt = +1.0776512391893247

    assert np.isclose(min_val_meas, min_val_expt)
    assert np.isclose(max_val_meas, max_val_expt)


def test_sat_range():
    # construct the model
    in_range = (-0.5, 1.0)
    m = SaturationModel(-3, 'dB', module_name='model', in_range=in_range)

    # observe the output range
    min_val_meas, max_val_meas = m.out_range[0], m.out_range[1]
    print(f'min_val_meas: {min_val_meas}')
    print(f'max_val_meas: {max_val_meas}')

    # expected values calculated from a previous run
    min_val_expt = -0.45060851062653023
    max_val_expt = +0.7079457843841379

    assert np.isclose(min_val_meas, min_val_expt)
    assert np.isclose(max_val_meas, max_val_expt)


@pytest.mark.parametrize('wn,zeta,dt', [
    (1, 1, 1),
    (1, 0.75, 1),
    (1, 0.5, 1),
    (1.23, 0.678, 0.789),
    (3.45, 2.34, 0.678),
])
def test_lds_range_simple(wn, zeta, dt, num_terms=100):
    # references:
    # https://lpsa.swarthmore.edu/Representations/SysRepTransformations/DE2SS.html
    # https://www.tutorialspoint.com/control_systems/control_systems_frequency_response_analysis.htm

    # set random seed for repeatability
    np.random.seed(0)

    # define the equations of the system
    A = np.array([[0, 1], [-(wn**2), -2*zeta*wn]], dtype=float)
    B = np.array([[0], [1]], dtype=float)
    C = np.array([[wn**2, 0]], dtype=float)
    D = np.array([[0]], dtype=float)

    # calculate the ranges of states variables and the output signal
    in_range = [-0.5, 1]
    state_ranges, out_range = LDSModel.calc_ranges(
        A=A, B=B, C=C, D=D, in_range=in_range, dt=dt, num_terms=num_terms)

    for k in range(A.shape[0]):
        print(f'state_ranges[{k}]: {state_ranges[k]}')
    print(f'out_range: {out_range}')

    # run a simulation of the system
    A_tilde = expm(dt*A)
    B_tilde = np.linalg.solve(A, (A_tilde-np.eye(2)).dot(B))
    x = np.zeros((2,1), dtype=float)
    x0_arr = []
    x1_arr = []
    y_arr = []
    u = np.random.randint(0, 2, 10*num_terms)
    u = u*in_range[0] + (1-u)*in_range[1]
    for k in range(len(u)):
        x0_arr.append(x[0, 0])
        x1_arr.append(x[1, 0])
        x = A_tilde.dot(x) + B_tilde.dot(u[k])
        y_arr.append(float(C.dot(x) + D.dot(u[k])))

    x0_rng_sim = (min(x0_arr), max(x0_arr))
    x1_rng_sim = (min(x1_arr), max(x1_arr))
    y_rng_sim = (min(y_arr), max(y_arr))

    print(f'simulated x0 range: {x0_rng_sim}')
    print(f'simulated x1 range: {x1_rng_sim}')
    print(f'simulated y range: {y_rng_sim}')

    # check results
    chk_range(calc=state_ranges[0], sim=x0_rng_sim)
    chk_range(calc=state_ranges[1], sim=x1_rng_sim)
    chk_range(calc=out_range, sim=y_rng_sim)


def test_lds_range_realistic(fz=0.8e9, fp1=1.6e9, gbw=40e9, num_spline=4, dtmax=62.5e-12):
    # build model
    m = CTLEModel(fz=fz, fp1=fp1, gbw=gbw, num_spline=num_spline, dtmax=dtmax, module_name='model')

    # print results
    print(f'state_ranges[0]: {m.state_ranges[0]}')
    print(f'state_ranges[1]: {m.state_ranges[1]}')
    print(f'out_range: {m.out_range}')

    # expected values calculated from a previous run
    assert np.isclose(m.state_ranges[0][0], -0.20429672)
    assert np.isclose(m.state_ranges[0][1], 0.20429672)
    assert np.isclose(m.state_ranges[1][0], -0.20264237)
    assert np.isclose(m.state_ranges[1][1], 0.20264237)
    assert np.isclose(m.out_range[0], -2.45864457)
    assert np.isclose(m.out_range[1], 2.45864457)
