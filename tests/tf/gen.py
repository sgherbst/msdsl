import os.path
from argparse import ArgumentParser

from msdsl.files import get_dir
from msdsl.model import AnalogModel
from msdsl.verilog import VerilogGenerator

def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()

    parser.add_argument('-o', '--output', type=str, default=get_dir('build', 'models'))
    parser.add_argument('--dt', type=float, default=0.1e-6)
    parser.add_argument('--omega', type=float, default=1e6)
    parser.add_argument('--zeta', type=float, default=0.4)

    args = parser.parse_args()

    # create the transfer function
    num = [args.omega**2]
    den = [1, 2*args.zeta*args.omega, args.omega**2]

    # create the model
    model = AnalogModel(name='filter', inputs=['v_in'], outputs=['v_out'], dt=args.dt)
    model.set_tf('v_out', 'v_in', (num, den))

    # determine the output filename
    filename = os.path.join(args.output, 'filter.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    model.run_generator(VerilogGenerator(filename))

if __name__ == '__main__':
    main()