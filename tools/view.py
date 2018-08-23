import argparse
import matplotlib.pyplot as plt
import numpy as np

def main():
    parser = argparse.ArgumentParser(description='Generate C++ code from mixed-signal intermediate representation.')
    parser.add_argument('-i', '--input', type=str, help='Input CSV file.', default='out.csv')

    args = parser.parse_args()

    data = np.genfromtxt(args.input, delimiter=',', skip_header=1, names=['v_out'])
    plt.plot(data['v_out'])
    plt.show()

if __name__ == '__main__':
    main()