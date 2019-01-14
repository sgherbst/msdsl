import subprocess
import sys

from msdsl.files import get_full_path

def call(cmd):
    ret = subprocess.call(cmd, stdout=sys.stdout, stderr=sys.stdout)

    if ret != 0:
        raise RuntimeError('Command exited with non-zero code.')

def call_python(cmd):
    # get path to python executable
    python = sys.executable
    if python is None:
        raise ValueError('Python path empty.')
    python = get_full_path(python)

    # prepend python executable to command
    cmd = [python] + cmd

    # call python
    call(cmd)

##############################################
# chunks function from https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]
##############################################