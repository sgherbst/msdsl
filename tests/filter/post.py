import os.path
import matplotlib.pyplot as plt
import numpy as np
import scipy.signal
from argparse import ArgumentParser

from msdsl.files import get_dir

def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()

    parser.add_argument('-o', '--output', type=str, default=get_dir('build'))
    parser.add_argument('--dt', type=float, default=0.1e-6)
    parser.add_argument('--tau', type=float, default=1e-6)

    args = parser.parse_args()

    # load data
    output = os.path.join(args.output, 'output.txt')
    y_emu = [float(line.strip()) for line in open(output, 'r').readlines()]
    t_emu = args.dt*np.arange(len(y_emu))

    # create comparison data
    t_cpu, y_cpu = scipy.signal.step(([1], [args.tau, 1]))

    # plot data
    plt.plot(t_emu*1e6, y_emu)
    plt.plot(t_cpu*1e6, y_cpu)
    plt.legend(['emu', 'cpu'])
    plt.xlabel('time (us)')
    plt.show()

if __name__ == '__main__':
    main()