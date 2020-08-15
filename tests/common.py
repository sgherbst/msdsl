from pathlib import Path
from shutil import which

import fault
from msdsl import get_msdsl_header
from svreal import *

TEST_DIR = Path(__file__).resolve().parent

def get_file(path):
    return Path(TEST_DIR, path)

def get_dir(path):
    # alias for get_file
    return get_file(path)

def get_files(*args):
    return [get_file(path) for path in args]

def get_dirs(*args):
    # alias for get_files
    return get_files(*args)

def pytest_sim_params(metafunc, simulators=None):
    if simulators is None:
        simulators = ['vcs', 'vivado', 'ncsim', 'iverilog']

    # parameterize with the simulators available
    if 'simulator' in metafunc.fixturenames:
        targets = []
        for simulator in simulators:
            if which(simulator):
                targets.append(simulator)

        metafunc.parametrize('simulator', targets)

def pytest_real_type_params(metafunc, real_types=None):
    if real_types is None:
        real_types = [RealType.FixedPoint, RealType.FloatReal, RealType.HardFloat]

    if 'real_type' in metafunc.fixturenames:
        metafunc.parametrize('real_type', real_types)

class MsdslTester(fault.Tester):
    def __init__(self, circuit, clock=None, expect_strict_default=True, debug_mode=True):
        super().__init__(circuit=circuit, clock=clock,
                         expect_strict_default=expect_strict_default)
        self.debug_mode = debug_mode

    def compile_and_run(self, target='system-verilog', ext_srcs=None,
                        inc_dirs=None, ext_model_file=True, tmp_dir=None,
                        disp_type=None, real_type=RealType.FixedPoint,
                        defines=None, **kwargs):
        # set defaults
        if ext_srcs is None:
            ext_srcs = []
        if inc_dirs is None:
            inc_dirs = []
        if tmp_dir is None:
            tmp_dir = not self.debug_mode
        if disp_type is None:
            disp_type = 'on_error' if (not self.debug_mode) else 'realtime'
        if defines is None:
            defines = {}

        # add to ext_srcs
        if real_type == RealType.HardFloat:
            ext_srcs = get_hard_float_sources() + ext_srcs

        # add to inc_dirs
        inc_dirs = [get_svreal_header().parent, get_msdsl_header().parent] + inc_dirs
        if real_type == RealType.HardFloat:
            inc_dirs = get_hard_float_inc_dirs() + inc_dirs

        # add defines as needed for the real number type
        defines = defines.copy()
        if real_type == RealType.FixedPoint:
            pass
        elif real_type == RealType.FloatReal:
            defines['FLOAT_REAL'] = None
        elif real_type == RealType.HardFloat:
            defines['HARD_FLOAT'] = None

        # call the command
        super().compile_and_run(
            target='system-verilog',
            ext_srcs=ext_srcs,
            inc_dirs=inc_dirs,
            defines=defines,
            ext_model_file=ext_model_file,
            tmp_dir=tmp_dir,
            disp_type=disp_type,
            **kwargs
        )
