import os.path
import matplotlib.pyplot as plt
import numpy as np
import scipy.signal
import json
from argparse import ArgumentParser

from msdsl.files import get_dir, get_full_path

def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str, default=get_dir('build'))
    args = parser.parse_args()

    # load config options
    config_file_path = os.path.join(os.path.dirname(get_full_path(__file__)), 'config.json')
    config = json.load(open(config_file_path, 'r'))

    # load data
    output = os.path.join(args.output, 'output.txt')
    y_emu = [float(line.strip()) for line in open(output, 'r').readlines()]
    t_emu = config['dt']*np.arange(len(y_emu))

    # create comparison data
    t_cpu, y_cpu = scipy.signal.step((-1/config['tau'], 1/config['tau'], 1, 0))

    # plot data
    plt.plot(t_emu*1e6, y_emu)
    plt.plot(t_cpu*1e6, y_cpu)
    plt.legend(['emu', 'cpu'])
    plt.xlabel('time (us)')
    plt.show()

if __name__ == '__main__':
    main()