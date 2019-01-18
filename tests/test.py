from argparse import ArgumentParser

import shutil
import os
import os.path
import json

from msdsl.files import get_full_path, get_dir, get_file
from msdsl.util import call_python
from msdsl.vivado import simulate

def main():
    # parse command line arguments
    parser = ArgumentParser()

    parser.add_argument('-i', '--input', type=str, default=None)
    parser.add_argument('-o', '--output', type=str, default=None)
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--float', action='store_true')

    args = parser.parse_args()

    # get defaults
    if args.input is None:
        args.input = get_dir('tests', 'hello')
    if args.output is None:
        args.output = get_dir('build')

    # expand path of input and output directories
    args.input = get_full_path(args.input)

    # get the configuration options of the input
    config_file_path = os.path.join(args.input, 'config.json')
    if os.path.isfile(config_file_path):
        config = json.load(open(config_file_path, 'r'))
    else:
        config = {}

    ###############
    # model generation
    ###############

    # figure out where the model files should go
    model_dir = os.path.join(args.output, 'models')

    # remove old models directory (if it exists), then make a new one
    shutil.rmtree(model_dir, ignore_errors=True)
    os.makedirs(model_dir, exist_ok=True)

    # run generator if it exists
    gen = os.path.join(args.input, 'gen.py')
    if os.path.isfile(gen):
        call_python([gen, '-o', model_dir])

    ###############
    # simulation
    ###############

    # change directory to output
    os.chdir(args.output)

    # find SVREAL library
    SVREAL_INSTALL_PATH = os.environ.get('SVREAL_INSTALL_PATH', None)
    if SVREAL_INSTALL_PATH is None:
        raise ValueError('The environment variable SVREAL_INSTALL_PATH must be defined.')
    SVREAL_INSTALL_PATH = get_full_path(SVREAL_INSTALL_PATH)

    # compute paths to SVREAL directories
    svreal_include_dir = os.path.join(SVREAL_INSTALL_PATH, 'include')
    svreal_src_dir = os.path.join(SVREAL_INSTALL_PATH, 'src')

    # compute paths to component directories
    component_include_dir = get_dir('components', 'include')
    component_src_dir = get_dir('components', 'src')

    # compute definitions

    defines = []

    if args.float:
        defines.append("FLOAT_REAL")
    if args.debug:
        defines.append("DEBUG_REAL")
    if 'dt' in config:
        defines.append(f'DT={config["dt"]}')

    # determine the simulation duration

    if 'dt' in config and 'tstop' in config:
        n_cycles = config['tstop']/config['dt']
    else:
        n_cycles = 10

    # run the compiler
    simulate(src_files=[get_file('tests', 'test.sv'), os.path.join(args.input, 'tb.sv')],
             src_dirs=[svreal_src_dir, component_src_dir, model_dir],
             inc_dirs=[svreal_include_dir, component_include_dir],
             defines=defines,
             runtime=n_cycles*1e-9
    )

    ###############
    # post-processing
    ###############

    post = os.path.join(args.input, 'post.py')
    if os.path.isfile(post):
        call_python([post, '-o', args.output])

if __name__ == "__main__":
    main()
