"""
Utilities for dealing with file names and paths
"""

import os

def verify_relative_path(filename: str) -> str:
    """
    The filename must be relative to the current directory.
    Returns filename unchanged.
    """
    full_path = expand_filename(filename)
    cwd = expand_filename(os.getcwd())
    if os.path.commonpath([cwd, full_path]) != cwd:
        raise OSError(f'File {full_path} not relative to {cwd}')
    return filename

def prepare_path(filename: str) -> str:
    """
    Creates the directory structure required for the filename.
    Only works with paths relative to the CWD
    """
    full_path = expand_filename(verify_relative_path(filename))
    # Exclude last component, the file name
    dir_path = os.path.dirname(full_path)
    os.makedirs(dir_path, exist_ok=True)
    return filename

def expand_filename(filename: str) -> str:
    """
    Returns the full path, absolute with user expansion et al.
    """
    return os.path.realpath(os.path.abspath(os.path.expanduser(filename)))
