from argparse import ArgumentParser

import shutil
import os
import os.path

from msdsl.files import get_file, get_full_path, get_dir
from msdsl.util import call_python
from msdsl.vivado import xvlog, xelab, xsim

def main():
    # parse command line arguments
    parser = ArgumentParser()

    parser.add_argument('-i', '--input', type=str, default=get_file('tests', 'hello'))
    parser.add_argument('-o', '--output', type=str, default=None)
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--float', action='store_true')
    parser.add_argument('--dt', type=float, default=2)
    parser.add_argument('--tstop', type=float, default=10)

    args = parser.parse_args()

    # expand path of input directory
    args.input = get_full_path(args.input)

    # set the output directory if necessary
    if args.output is None:
        args.output = get_dir('build')

    # make the model output directory
    model_lib_dir = os.path.join(args.output, 'lib')
    os.makedirs(model_lib_dir, exist_ok=True)

    # copy files
    shutil.copyfile(os.path.join(args.input, 'tb.sv'), os.path.join(model_lib_dir, 'tb.sv'))
    shutil.copyfile(get_file('tests', 'test.sv'), os.path.join(args.output, 'test.sv'))

    # create models
    gen = os.path.join(args.input, 'gen.py')
    call_python([gen, '-o', args.output, '--dt', str(args.dt), '--tstop', str(args.tstop)])

    # change directory to output
    os.chdir(args.output)

    ###############
    # compile
    ###############

    # find SVREAL library
    SVREAL_INSTALL_PATH = os.environ.get('SVREAL_INSTALL_PATH', None)
    if SVREAL_INSTALL_PATH is None:
        raise ValueError('The environment variable SVREAL_INSTALL_PATH must be defined.')
    SVREAL_INSTALL_PATH = get_full_path(SVREAL_INSTALL_PATH)

    # compute paths to SVREAL directories
    svreal_include_dir = os.path.join(SVREAL_INSTALL_PATH, 'include')
    svreal_src_dir = os.path.join(SVREAL_INSTALL_PATH, 'src')

    # compute definitions
    defines = []

    if args.float:
        defines.append('FLOAT_REAL')
    if args.debug:
        defines.append('DEBUG_REAL')

    xvlog(src_files=[os.path.join(args.output, 'test.sv')],
          lib_dirs=[svreal_src_dir, model_lib_dir],
          inc_dirs=[svreal_include_dir],
          defines=defines)

    ###############
    # elaborate
    ###############

    xelab('test')

    ###############
    # elaborate
    ###############

    xsim()

if __name__ == "__main__":
    main()
