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