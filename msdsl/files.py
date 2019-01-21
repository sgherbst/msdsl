import os

def get_full_path(path):
    return os.path.realpath(os.path.expanduser(path))

def top_dir():
    this_file_path = get_full_path(__file__)
    return os.path.dirname(os.path.dirname(this_file_path))

def get_file(*args):
    return os.path.join(top_dir(), *args)

def get_dir(*args, mkdir_p=True):
    path = get_file(*args)

    if mkdir_p:
        os.makedirs(path, exist_ok=True)

    return path

def get_vivado_sim_dir(top_dir=None, project_name='test', project_dir_name='test'):
    if top_dir is None:
        top_dir = get_dir('build')

    return os.path.join(top_dir, project_dir_name, f'{project_name}.sim', 'sim_1', 'behav', 'xsim')