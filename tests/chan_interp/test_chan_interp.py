# general imports
import pytest
from pathlib import Path
import numpy as np
from scipy.interpolate import interp1d

# AHA imports
import magma as m

# msdsl imports
from ..common import *
from msdsl import VerilogGenerator
from msdsl.templates.channel import ChannelModel
from msdsl.rf import s4p_to_step

THIS_DIR = Path(__file__).resolve().parent
BUILD_DIR = THIS_DIR / 'build'
TOP_DIR = THIS_DIR.parent.parent
NPTS = 4

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    pytest_real_type_params(metafunc, [RealType.FloatReal, RealType.FixedPoint])
    #pytest_real_type_params(metafunc, [RealType.FloatReal])

@pytest.mark.parametrize(
    'test_pts,chan_type,err_lim', [
        (200, 'exp', 5e-3),
        (200, 's4p', 5e-3)
    ]
)
def test_chan_interp(simulator, real_type, test_pts, err_lim, chan_type,
                     ui=62.5e-12, ui_var=0.25, func_numel=512):
    # make sure test is repeatable
    np.random.seed(0)

    # generate step response data
    if chan_type in {'exp'}:
        t_dur=1e-9
        t_step = np.linspace(0, t_dur, func_numel)
        v_step = 1.0-np.exp(-0.5*t_step/ui)
    elif chan_type in {'s4p'}:
        # get high-resolution step response
        t_orig, v_orig = s4p_to_step(TOP_DIR/'peters_01_0605_B1_thru.s4p', dt=0.1e-12, T=10e-9)
        # trim to func_numel points around the "interesting part" of the waveform
        t_step = np.linspace(2e-9, 6e-9, func_numel)
        v_step = interp1d(t_orig, v_orig)(t_step)
        t_step -= t_step[0]
        t_dur = t_step[-1]-t_step[0]
    else:
        raise Exception(f'Unknown chan_type: {chan_type}')

    # determine number of terms for the history
    num_terms = int(round(0.6*t_dur/ui))
    print(f'num_terms: {num_terms}')

    # generate model
    model = ChannelModel(
        t_step = t_step,
        v_step = v_step,
        module_name='model',
        dtmax=ui,
        num_spline=NPTS,
        num_terms=num_terms,
        func_numel=func_numel,
        build_dir=BUILD_DIR,
        clk='clk',
        rst='rst',
        real_type=real_type
    )
    model_file = model.compile_to_file(VerilogGenerator())

    # create IO dictionary
    ios = {f'out_{k}': fault.RealOut for k in range(NPTS)}

    # declare circuit
    class dut(m.Circuit):
        name = 'test_chan_interp'
        io = m.IO(
            dt=fault.RealIn,
            in_=fault.RealIn,
            clk=m.In(m.Clock),
            rst=m.BitIn,
            **ios
        )

    # create the tester
    tester = MsdslTester(dut, dut.clk)

    # convenience functions for reading/writing splines
    def get_output_spline():
        retval = []
        for k in range(NPTS):
            retval.append(tester.get_value(getattr(dut, f'out_{k}')))
        return retval

    # define input segments
    inputs = 2*(np.random.randint(0, 2, test_pts)-0.5)
    widths = np.random.uniform(1-ui_var, 1+ui_var, test_pts)*ui
    times = np.concatenate(([0], np.cumsum(widths)))

    # initialize
    tester.poke(dut.dt, 0)
    tester.poke(dut.in_, 0)
    tester.poke(dut.clk, 0)
    tester.poke(dut.rst, 1)
    tester.eval()

    # apply reset
    tester.step(2)

    # clear reset
    tester.poke(dut.rst, 0)
    tester.step(2)

    # run test
    outputs = []
    for width, in_ in zip(widths, inputs):
        tester.poke(dut.dt, width)
        tester.poke(dut.in_, in_)
        tester.eval()
        outputs.append(get_output_spline())
        tester.step(2)

    # run the simulation
    parameters = {
        'in_range': 2.5,
        'out_range': 2.5
    }
    tester.compile_and_run(
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file('chan_interp/test_chan_interp.sv')],
        parameters=parameters,
        real_type=real_type,
        #dump_waveforms=True
    )

    # convert measurements to arrays
    meas = [np.array([elem.value for elem in spline]) for spline in outputs]

    # generate expected output
    func = interp1d(t_step, v_step, bounds_error=False, fill_value=(v_step[0], v_step[-1]))
    expt = []
    svec = np.linspace(0, 1, NPTS) * ui
    for i in range(len(inputs)):
        expt.append(np.zeros((NPTS,), dtype=float))
        for j in range(i+1):
            if i==j:
                expt[-1] += inputs[j]*func(svec)
            else:
                expt[-1] += inputs[j]*(func(svec+times[i]-times[j])-func(svec+times[i]-times[j+1]))

    # calculate errors
    errs = [vm-ve for vm, ve in zip(meas, expt)]

    # check errors
    max_err = max([np.max(elem) for elem in errs])
    print(f'max_err: {max_err}')
    assert max_err < err_lim
