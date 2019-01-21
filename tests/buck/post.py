import os.path
import matplotlib.pyplot as plt
import numpy as np
import json
from argparse import ArgumentParser

from msdsl.files import get_dir, get_full_path, get_vivado_sim_dir

def main():
    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str, default=get_dir('build'))
    args = parser.parse_args()

    # load config options
    config_file_path = os.path.join(os.path.dirname(get_full_path(__file__)), 'config.json')
    config = json.load(open(config_file_path, 'r'))

    # load data
    v_out = np.loadtxt(os.path.join(get_vivado_sim_dir(args.output), 'v_out.txt'))
    i_mag = np.loadtxt(os.path.join(get_vivado_sim_dir(args.output), 'i_mag.txt'))
    t_vec = config['dt']*np.arange(len(v_out))

    # plot v_out
    ax1 = plt.subplot(211)
    ax1.set_ylabel('v_out')
    plt.plot(t_vec*1e6, v_out)

    # plot i_mag
    ax2 = plt.subplot(212, sharex=ax1)
    ax2.set_ylabel('i_mag')
    plt.plot(t_vec*1e6, i_mag)

    # set shared x-axis label
    plt.xlabel('time (us)')

    # show plots
    plt.show()

if __name__ == '__main__':
    main()