import os.path
from argparse import ArgumentParser

from msdsl.files import get_dir
from msdsl.model import AnalogModel

TAU = 3e-6

def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()

    parser.add_argument('-o', '--output', type=str, default=get_dir('build', 'models'))
    parser.add_argument('--dt', type=float, default=1e-6)

    args = parser.parse_args()

    # create the model
    model = AnalogModel(inputs=['in'], outputs=['out'])
    model.signals['out'] = {'in': args.dt/TAU, 'out':  1-args.dt/TAU}

    # determine the output filename
    filename = os.path.join(args.output, 'filter.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    model.generate(dt=args.dt, filename=filename)

if __name__ == '__main__':
    main()