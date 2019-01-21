import os.path
import numpy as np
from argparse import ArgumentParser

from msdsl.files import get_dir, get_vivado_sim_dir

def main():
    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str, default=get_dir('build'))
    args = parser.parse_args()

    # load data
    data = np.loadtxt(os.path.join(get_vivado_sim_dir(args.output), 'data.txt'))

    # plot data
    print(list(data))

if __name__ == '__main__':
    main()