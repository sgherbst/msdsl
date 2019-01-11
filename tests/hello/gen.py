from argparse import ArgumentParser

def main():
    # parse command line arguments
    parser = ArgumentParser()

    parser.add_argument('-o', '--output', type=str)

    args = parser.parse_args()

    print('Running model generator...')
    print('Model(s) will be placed in: ' + args.output)

if __name__ == '__main__':
    main()