import numpy as np
from pathlib import Path
from math import floor
from scipy.interpolate import interp1d
from scipy.signal import lfilter
from scipy.signal import cont2discrete
from msdsl.interp.interp import calc_interp_w
from msdsl.interp.lds import SplineLDS
from msdsl.interp.nonlin import calc_tanh_vsat, tanhsat
from msdsl.interp.ctle import calc_ctle_abcd, calc_ctle_num_den
from msdsl.interp.interp import calc_piecewise_poly, eval_piecewise_poly

THIS_DIR = Path(__file__).resolve().parent
TOP_DIR = THIS_DIR.parent
DATA_FILE = TOP_DIR / 'channel_resp_mar11.csv'

def interp_emu_res(tvec, vvec, dtmax, tsim, order, npts):
    # hold the previous stop index
    stop_idx = -1
    # calculate spacing between "hidden" timesteps
    th = dtmax/(npts-1)
    # build up partial results
    results = []
    for k in range(len(tvec)):
        # find start index
        start_idx = stop_idx+1
        # find stop index
        if k == len(tvec)-1:
            stop_idx = len(tsim)-1
        else:
            stop_idx = np.searchsorted(tsim, tvec[k+1], side='left')
        # find vector of times for interpolation
        t_interp = tsim[start_idx:(stop_idx+1)] - tvec[k]
        # calculate piecewise polynomial representation
        U = calc_piecewise_poly(vvec[k], order=order)
        results.append(eval_piecewise_poly(t_interp, th, U))
    # return array of the results
    return np.concatenate(results)

npts = 4
order = 3
gbw = 40e9
dtmax = 62.5e-12
dt_nom = 10e-12

ctle1_fz, ctle1_fp = 0.8e9, 1.6e9
ctle2_fz, ctle2_fp = 3.5e9, 7.0e9
ctle3_fz, ctle3_fp = 5.0e9, 10.0e9

nl_dB = -1
nl_veval = 1.0

def run_simulation(t_resp, v_resp):
    # find timestep of oversampled data
    tover = np.median(np.diff(t_resp))
    assert np.all(np.isclose(np.diff(t_resp), tover))
    print(f'tover: {tover*1e12:0.3f} ps')

    # CLTE1
    nd1 = calc_ctle_num_den(fz=ctle1_fz*dtmax, fp1=ctle1_fp*dtmax, gbw=gbw*dtmax)
    b1, a1, _ = cont2discrete(nd1, dt=tover/dtmax)
    ctle1_out = lfilter(b1[0], a1, v_resp)

    # NL1
    nl_vsat = calc_tanh_vsat(nl_dB, 'dB', veval=nl_veval)
    nl_func = lambda v: tanhsat(v, nl_vsat)
    nl1_out = nl_func(ctle1_out)

    # CTLE2
    nd2 = calc_ctle_num_den(fz=ctle2_fz*dtmax, fp1=ctle2_fp*dtmax, gbw=gbw*dtmax)
    b2, a2, _ = cont2discrete(nd2, dt=tover/dtmax)
    ctle2_out = lfilter(b2[0], a2, nl1_out)

    # NL2
    nl2_out = nl_func(ctle2_out)

    # CTLE3
    nd3 = calc_ctle_num_den(fz=ctle3_fz*dtmax, fp1=ctle3_fp*dtmax, gbw=gbw*dtmax)
    b3, a3, _ = cont2discrete(nd3, dt=tover/dtmax)
    ctle3_out = lfilter(b3[0], a3, nl2_out)

    # NL3
    nl3_out = nl_func(ctle3_out)

    return {'ctle1_out': ctle1_out, 'nl1_out': nl1_out, 'ctle2_out': ctle2_out, 'nl2_out': nl2_out,
            'ctle3_out': ctle3_out, 'nl3_out': nl3_out}


def run_emulation(t_resp, v_resp):
    # build interpolator for data
    my_interp = interp1d(t_resp, v_resp)
    svec = np.linspace(0, 1, npts)

    # find state-space representation of the CTLEs
    A1, B1, C1, D1 = calc_ctle_abcd(fz=ctle1_fz*dtmax, fp1=ctle1_fp*dtmax, gbw=gbw*dtmax)
    A2, B2, C2, D2 = calc_ctle_abcd(fz=ctle2_fz*dtmax, fp1=ctle2_fp*dtmax, gbw=gbw*dtmax)
    A3, B3, C3, D3 = calc_ctle_abcd(fz=ctle3_fz*dtmax, fp1=ctle3_fp*dtmax, gbw=gbw*dtmax)

    # define nonlinearity
    nl_vsat = calc_tanh_vsat(nl_dB, 'dB', veval=nl_veval)
    nl_func = lambda v: tanhsat(v, nl_vsat)

    # define interpolation
    W = calc_interp_w(npts=npts, order=order)

    # define CTLE objects
    ctle1 = SplineLDS(A=A1, B=B1, C=C1, D=D1, W=W)
    ctle2 = SplineLDS(A=A2, B=B2, C=C2, D=D2, W=W)
    ctle3 = SplineLDS(A=A3, B=B3, C=C3, D=D3, W=W)

    # initialize states
    x1 = np.zeros((A1.shape[0],), dtype=float)
    x2 = np.zeros((A2.shape[0],), dtype=float)
    x3 = np.zeros((A3.shape[0],), dtype=float)

    # initialize results
    results = {'ctle1_out': [], 'nl1_out': [], 'ctle2_out': [], 'nl2_out': [],
              'ctle3_out': [], 'nl3_out': []}

    # initialize times
    t = 0
    num_dt = floor((t_resp[-1]-dtmax)/dt_nom)
    dtlist = [dt_nom/dtmax]*num_dt
    tlist = []
    for dt in dtlist:
        # update time list
        tlist.append(t)

        # CTLE1
        x1, out = ctle1.calc_update(xo=x1, inpt=my_interp(t+svec*dtmax), dt=dt)
        results['ctle1_out'].append(out)
        # NL1
        out = nl_func(out)
        results['nl1_out'].append(out)

        # CTLE2
        x2, out = ctle2.calc_update(xo=x2, inpt=out, dt=dt)
        results['ctle2_out'].append(out)
        # NL2
        out = nl_func(out)
        results['nl2_out'].append(out)

        # CTLE3
        x3, out = ctle3.calc_update(xo=x3, inpt=out, dt=dt)
        results['ctle3_out'].append(out)
        # NL3
        out = nl_func(out)
        results['nl3_out'].append(out)

        t += dt*dtmax

    # make timesteps a NumPy array
    tlist = np.array(tlist, dtype=float)

    # determine over what range the output should be interpolated
    idx0 = np.where(t_resp >= tlist[0])[0][0]
    idx1 = np.where(t_resp >= tlist[-1])[0][0]
    t_interp = t_resp[idx0:(idx1+1)]

    # interpolate the results
    results = {k: interp_emu_res(tlist, v, dtmax, t_interp, order, npts) for k, v in results.items()}

    # return results
    return results, (idx0, idx1)

def main():
    # read in data
    my_data = np.genfromtxt(DATA_FILE, delimiter=',', skip_header=1)
    t_resp = my_data[:, 1] - my_data[0, 1]
    v_resp = my_data[:, 2]

    sim_results = run_simulation(t_resp=t_resp, v_resp=v_resp)
    emu_results, (idx0, idx1) = run_emulation(t_resp=t_resp, v_resp=v_resp)

    signal = 'nl3_out'

    import matplotlib.pyplot as plt
    plt.plot(t_resp, sim_results[signal])
    plt.plot(t_resp[idx0:(idx1+1)], emu_results[signal])
    plt.show()

    # calculate error
    rms_err = np.sqrt(np.mean((sim_results[signal][idx0:(idx1+1)]-emu_results[signal])**2))
    print('rms_err:', rms_err)

if __name__ == '__main__':
    main()
