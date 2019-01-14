import os.path
from argparse import ArgumentParser

from msdsl.files import get_dir
from msdsl.model import AnalogModel

def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()

    parser.add_argument('-o', '--output', type=str, default=get_dir('build', 'models'))
    parser.add_argument('--dt', type=float, default=1e-6)

    args = parser.parse_args()

    out_file = os.path.join(args.output, 'filter.sv')
    print('Model will be written to: ' + out_file)

    model = AnalogModel(
        inputs=['in'],
        outputs=['out']
    )

    model.write(out_file)

if __name__ == '__main__':
    main()