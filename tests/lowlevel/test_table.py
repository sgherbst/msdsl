from pathlib import Path
import numpy as np
from msdsl.expr.table import RealTable

BUILD_DIR = Path(__file__).resolve().parent / 'build'

def test_table():
    # write values out
    real_vals_out = np.exp(-np.arange(256) / 100)
    table_out = RealTable(real_vals_out, dir=BUILD_DIR)
    table_out.to_file()

    # read values in
    table_in = RealTable.from_file(dir=BUILD_DIR)
    real_vals_in = table_in.real_vals

    # compare values
    for k, (val_out, val_in) in enumerate(zip(real_vals_out, real_vals_in)):
        if not (abs(val_out - val_in) <= 0.001):
            raise Exception(f'Data mismatch at entry {k}: {val_out} vs. {val_in}')