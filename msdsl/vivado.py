import shutil
import os
from glob import glob
from math import ceil

from msdsl.util import call
from msdsl.files import get_dir

def find_vivado_command(cmd):
    VIVADO_INSTALL_PATH = os.environ.get('VIVADO_INSTALL_PATH', None)

    if VIVADO_INSTALL_PATH is not None:
        path = shutil.which(cmd, path=os.path.join(VIVADO_INSTALL_PATH, 'bin'))
        if path is not None:
            return path
    else:
        return shutil.which(cmd)

def fix_path(path: str):
    return path.replace('\\', '/')

def get_sim_dir(top_dir=None, project_name='test', project_dir_name='test'):
    if top_dir is None:
        top_dir = get_dir('build')

    return os.path.join(top_dir, project_dir_name, f'{project_name}.sim', 'sim_1', 'behav', 'xsim')

def simulate(src_files=None, src_dirs=None, inc_files=None, inc_dirs=None, defines=None, runtime=10e-9,
             top_module_name='test', tcl_script_name='test.tcl', project_name='test', project_dir_name='test'):

    # set defaults
    if src_files is None:
        src_files = []
    if src_dirs is None:
        src_dirs = []
    if inc_files is None:
        inc_files = []
    if inc_dirs is None:
        inc_dirs = []
    if defines is None:
        defines = []

    # build a list of all source files and a list of just the header files
    all_files = []
    header_files = []

    # handle source files
    for src_dir in src_dirs:
        src_files += glob(os.path.join(src_dir, '*.sv'))

    all_files.extend(src_files)

    # handle header files
    for inc_dir in inc_dirs:
        inc_files += glob(os.path.join(inc_dir, '*.sv'))

    all_files.extend(inc_files)
    header_files.extend(inc_files)

    # fix paths (changing backslash to forward slash)
    all_files = [fix_path(path) for path in all_files]
    header_files = [fix_path(path) for path in header_files]

    # delete the project directory if it already exists
    shutil.rmtree(project_dir_name, ignore_errors=True)

    # write the simulation TCL file
    with open(tcl_script_name, 'w') as f:
        # create a new project
        f.write(f'create_project {project_name} {project_dir_name}\n\n')

        # add all source files to the project (including header files)
        f.write(f'add_files -norecurse {{{" ".join(all_files)}}}\n\n')

        # specify which files are header files
        for header_file in header_files:
            f.write(f'set_property file_type {{Verilog Header}} [get_files  {header_file}]\n')
        f.write('\n')

        # define the top module
        f.write(f'set_property top {top_module_name} [get_filesets sim_1]\n')

        # set define variables
        for define in defines:
            f.write(f'set_property verilog_define {define} [get_filesets sim_1]\n')
        f.write('\n')

        # launch the simulation
        t = int(ceil(runtime*1e9))
        f.write(f'set_property -name {{xsim.simulate.runtime}} -value {{{t}ns}} -objects [get_filesets sim_1]\n')
        f.write('launch_simulation\n')

    # build simulation command
    cmd = [find_vivado_command('vivado'), '-mode', 'batch', '-source', tcl_script_name, '-nolog', '-nojournal']
    call(cmd)