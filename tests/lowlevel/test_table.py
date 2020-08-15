import pytest
from pathlib import Path
import numpy as np
from svreal import RealType
from msdsl import RealTable, SIntTable, UIntTable

BUILD_DIR = Path(__file__).resolve().parent / 'build'

@pytest.mark.parametrize('real_type', [RealType.FixedPoint, RealType.HardFloat])
def test_real_table(real_type, width=18, exp=-13):
    # write values out
    vals_out = np.random.uniform(-10.0, 10.0, 256)
    table_out = RealTable(vals_out, width=width, exp=exp, dir=BUILD_DIR,
                          real_type=real_type)
    table_out.to_file()

    # read values in
    table_in = RealTable.from_file(exp=exp, dir=BUILD_DIR, real_type=real_type)
    vals_in = table_in.vals

    # compare values
    for k, (val_out, val_in) in enumerate(zip(vals_out, vals_in)):
        if not (abs(val_out - val_in) <= 0.001):
            raise Exception(f'Data mismatch at entry {k}: {val_out} vs. {val_in}')

def test_sint_table():
    # write values out
    vals_out = np.random.randint(-128, 128, 256)
    table_out = SIntTable(vals_out, dir=BUILD_DIR)
    table_out.to_file()

    # read values in
    table_in = SIntTable.from_file(dir=BUILD_DIR)
    vals_in = table_in.vals

    # compare values
    for k, (val_out, val_in) in enumerate(zip(vals_out, vals_in)):
        if val_out != val_in:
            raise Exception(f'Data mismatch at entry {k}: {val_out} vs. {val_in}')

def test_uint_table():
    # write values out
    vals_out = np.random.randint(0, 256, 256)
    table_out = UIntTable(vals_out, dir=BUILD_DIR)
    table_out.to_file()

    # read values in
    table_in = UIntTable.from_file(dir=BUILD_DIR)
    vals_in = table_in.vals

    # compare values
    for k, (val_out, val_in) in enumerate(zip(vals_out, vals_in)):
        if val_out != val_in:
            raise Exception(f'Data mismatch at entry {k}: {val_out} vs. {val_in}')
