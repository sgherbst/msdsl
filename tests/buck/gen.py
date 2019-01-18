import os.path
import json
from argparse import ArgumentParser

from msdsl.files import get_dir, get_full_path
from msdsl.model import MixedSignalModel
from msdsl.verilog import VerilogGenerator
from msdsl.expr import AnalogInput, DigitalInput, AnalogOutput, Concatenate

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
    model = MixedSignalModel('buck', DigitalInput('gate'), AnalogInput('v_in'), AnalogOutput('v_out'),
                             AnalogOutput('i_mag'), dt=config['dt'])

    # inductor dynamics
    model.set_dynamics_cases(model.i_mag, [
        ('equals', 0),
        ('diff_eq', -model.v_out/config['ind']),
        ('diff_eq', (model.v_in-model.v_out)/config['ind']),
        ('diff_eq', (model.v_in-model.v_out)/config['ind'])
    ], Concatenate([model.gate, model.i_mag > 0]))

    # capacitor dynamics
    model.set_deriv(model.v_out, (model.i_mag-model.v_out/config['res'])/config['cap'])

    # determine the output filename
    filename = os.path.join(args.output, 'buck.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    model.compile_model(VerilogGenerator(filename))

if __name__ == '__main__':
    main()