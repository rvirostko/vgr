#! /usr/bin/env python3

import os

def verify_relative_path(filename: str) -> str:
    full_path = os.path.realpath(filename)
    cwd = os.path.realpath(os.getcwd())
    if os.path.commonpath([cwd, full_path]) != cwd: raise OSError(f'File {full_path} not relative to {cwd}')
    return filename

def prepare_path(filename):
    full_path = os.path.realpath(filename)
    # Exclude last component, the file name
    dir_path = os.path.dirname(full_path)
    os.makedirs(dir_path, exist_ok=True)
    return filename

