import os.path
import json
from argparse import ArgumentParser

from msdsl.files import get_dir, get_full_path
from msdsl.model import MixedSignalModel
from msdsl.verilog import VerilogGenerator
from msdsl.expr import AnalogInput, DigitalInput, AnalogOutput

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
    tau = config['tau']
    dt = config['dt']

    # create the model
    model = MixedSignalModel('filter', DigitalInput('ctrl'), AnalogInput('v_in'), AnalogOutput('v_out'), dt=dt)
    model.set_dynamics_cases(model.v_out, [
        ('diff_eq', -model.v_out/tau),
        ('diff_eq', (model.v_in-model.v_out)/tau)
    ], model.ctrl)

    # determine the output filename
    filename = os.path.join(args.output, 'filter.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    model.compile_model(VerilogGenerator(filename))

if __name__ == '__main__':
    main()