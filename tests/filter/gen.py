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
    parser.add_argument('--dt', type=float, default=1e-6)
    parser.add_argument('--tau', type=float, default=3e-6)

    args = parser.parse_args()

    # create the model
    model = AnalogModel(inputs=['in'], outputs=['out'], dt=args.dt)
    model.signals['out'] = {'in': args.dt/args.tau, 'out':  1-args.dt/args.tau}

    # determine the output filename
    filename = os.path.join(args.output, 'filter.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    model.run_generator(VerilogGenerator(filename))

if __name__ == '__main__':
    main()