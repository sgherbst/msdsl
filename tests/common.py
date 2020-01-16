from pathlib import Path
from shutil import which

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
