import shutil
import os
from glob import glob

from msdsl.util import call

def find_vivado_command(cmd):
    VIVADO_INSTALL_PATH = os.environ.get('VIVADO_INSTALL_PATH', None)

    if VIVADO_INSTALL_PATH is not None:
        path = shutil.which(cmd, path=os.path.join(VIVADO_INSTALL_PATH, 'bin'))
        if path is not None:
            return path
    else:
        return shutil.which(cmd)

def xvlog(src_files=None, lib_dirs=None, inc_dirs=None, defines=None):
    # set defaults
    if src_files is None:
        src_files = []
    if lib_dirs is None:
        lib_dirs = []
    if inc_dirs is None:
        inc_dirs = []
    if defines is None:
        defines = []

    # build simulation command
    cmd = []

    cmd.append(find_vivado_command('xvlog'))

    cmd.extend(src_files)

    for lib_dir in lib_dirs:
        cmd.extend(glob(os.path.join(lib_dir, '*.sv')))
        cmd.extend(['-L', lib_dir])

    for inc_dir in inc_dirs:
        cmd.extend(['-i', inc_dir])

    cmd.extend(['-sourcelibext', 'sv'])
    cmd.append('-sv')

    for define in defines:
        cmd.extend(['-d', define])

    call(cmd)

def xelab(top_module_name, snapshot='snapshot'):
    cmd = [find_vivado_command('xelab'),
           top_module_name,
           '-debug', 'typical',
           '-s', snapshot]

    call(cmd)

def xsim(snapshot='snapshot', gui=False):
    cmd = [find_vivado_command('xsim'),
           snapshot,
           '-R']

    if gui:
        cmd.append('-gui')

    call(cmd)

