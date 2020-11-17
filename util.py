import os

def asset_name_from_path(path):
    return os.path.basename(path)

def get_file_extension(path):
    _, ext = os.path.splitext(path)
    return ext.upper()
