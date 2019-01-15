import os.path
import json
from argparse import ArgumentParser

from msdsl.files import get_dir, get_full_path
from msdsl.model import AnalogModel
from msdsl.verilog import VerilogGenerator

def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str, default=get_dir('build', 'models'))
    args = parser.parse_args()

    # load config options
    config_file_path = os.path.join(os.path.dirname(get_full_path(__file__)), 'config.json')
    config = json.load(open(config_file_path, 'r'))

    # create the model
    model = AnalogModel(name='filter', inputs=['v_in'], outputs=['v_out'], dt=config['dt'])
    model.set_tf('v_out', 'v_in', (config['num'], config['den']))

    # determine the output filename
    filename = os.path.join(args.output, 'filter.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    model.run_generator(VerilogGenerator(filename))

if __name__ == '__main__':
    main()