"""
Functions for working with file and dir names.
"""

import os
from typing import Any

from .common import type_str

def dir_name(path: Any) -> Any:
    """
**Returns the directory part of a path**

If path is empty "." is used, matching UNIX behavior.
"""
    if path is None: return None
    if isinstance(path, (list, tuple)): return type(path)(dir_name(path1) for path1 in path)
    if not isinstance(path, str): raise ValueError(f'DirName on {type_str(path)} not possible')
    return os.path.dirname(path) or '.'

def base_name(path: Any) -> Any:
    """
**Returns the final component of a path**

"""
    if path is None: return None
    if isinstance(path, (list, tuple)): return type(path)(base_name(path1) for path1 in path)
    if not isinstance(path, str): raise ValueError(f'BaseName on {type_str(path)} not possible')
    return os.path.basename(path)

def file_exists(path: Any) -> Any:
    """
**Returns _True_ if path exists**
"""
    if path is None: return None
    if isinstance(path, (list, tuple)): return type(path)(file_exists(path1) for path1 in path)
    if not isinstance(path, str): raise ValueError(f'FileExists on {type_str(path)} not possible')
    return os.path.exists(path)

def is_file(path: Any) -> Any:
    """
**Returns _True_ if path exists and is a regular file**
"""
    if path is None: return None
    if isinstance(path, (list, tuple)): return type(path)(is_file(path1) for path1 in path)
    if not isinstance(path, str): raise ValueError(f'IsFile on {type_str(path)} not possible')
    return os.path.isfile(path)

def is_dir(path: Any) -> Any:
    """
**Returns _True_ if path exists and is a directory**
"""
    if path is None: return None
    if isinstance(path, (list, tuple)): return type(path)(is_dir(path1) for path1 in path)
    if not isinstance(path, str): raise ValueError(f'IsDirectory on {type_str(path)} not possible')
    return os.path.isdir(path)

# TODO future
# File listing os.listdir(path)
# Delete a file os.remove(path)
# Delete a directory os.rmdir(path) (empty only) shutil.rmtree(path) (recursive)
# Rename/move file or dir shutil.move(src, dst)
# Copy file shutil.copy(src, dst)
# Copy directory shutil.copytree(src, dst)
