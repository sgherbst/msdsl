import os.path
import json
from argparse import ArgumentParser
from math import log2, ceil

from msdsl.files import get_dir, get_full_path
from msdsl.model import MixedSignalModel
from msdsl.verilog import VerilogGenerator
from msdsl.expr import AnalogArray, DigitalInput, AnalogOutput

def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str, default=get_dir('build', 'models'))
    args = parser.parse_args()

    # load config options
    config_file_path = os.path.join(os.path.dirname(get_full_path(__file__)), 'config.json')
    config = json.load(open(config_file_path, 'r'))

    # determine format of the lookup table
    vals = config['vals']
    n_addr = int(ceil(log2(len(vals))))

    # create the model
    model = MixedSignalModel('array', DigitalInput('addr', n_addr), AnalogOutput('data'))
    model.set_this_cycle(model.data, AnalogArray(config['vals'], model.addr))

    # determine the output filename
    filename = os.path.join(args.output, 'array.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    model.compile_model(VerilogGenerator(filename))

if __name__ == '__main__':
    main()