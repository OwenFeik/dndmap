import os

DEBUG = True

def asset_name_from_path(path):
    name, _ = os.path.splitext(os.path.basename(path))
    return name

def get_file_extension(path):
    _, ext = os.path.splitext(path)
    return ext[1:].upper()

def abs_path(path):
    return os.path.abspath(path)
