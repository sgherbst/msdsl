from argparse import ArgumentParser

import shutil
import os
import os.path
from math import ceil

from msdsl.files import get_full_path, get_dir, get_file
from msdsl.util import call_python
from msdsl.vivado import xvlog, xelab, xsim

def main():
    # parse command line arguments
    parser = ArgumentParser()

    parser.add_argument('-i', '--input', type=str, default=get_dir('tests', 'hello'))
    parser.add_argument('-o', '--output', type=str, default=get_dir('build'))
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--float', action='store_true')

    args = parser.parse_args()

    # expand path of input directory
    args.input = get_full_path(args.input)

    # make the model output directory
    model_dir = os.path.join(args.output, 'models')
    os.makedirs(model_dir, exist_ok=True)

    # copy files
    shutil.copyfile(os.path.join(args.input, 'tb.sv'), os.path.join(args.output, 'tb.sv'))
    shutil.copyfile(os.path.join(args.input, 'sim.tcl'), os.path.join(args.output, 'sim.tcl'))
    shutil.copyfile(get_file('tests', 'test.sv'), os.path.join(args.output, 'test.sv'))

    ###############
    # model generation
    ###############

    gen = os.path.join(args.input, 'gen.py')
    if os.path.isfile(gen):
        call_python([gen, '-o', model_dir])

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

    # run the compiler
    xvlog(src_files=[os.path.join(args.output, 'test.sv'),
                     os.path.join(args.output, 'tb.sv')],
          lib_dirs=[svreal_src_dir, model_dir],
          inc_dirs=[svreal_include_dir],
          defines=defines
    )

    ###############
    # elaborate
    ###############

    xelab('test')

    ###############
    # elaborate
    ###############

    xsim()

    ###############
    # post-processing
    ###############

    post = os.path.join(args.input, 'post.py')
    if os.path.isfile(post):
        call_python([post, '-o', args.output])

if __name__ == "__main__":
    main()
