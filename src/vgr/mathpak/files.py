"""
Functions for working with file and dir names.
"""

import os
from typing import Any

from .common import type_str
from ..output import verify_relative_path

def dir_name(path: Any) -> Any:
    """
**Returns the directory part of a path**

If path is empty "." is used, matching UNIX behavior.
"""
    if path is None: return None
    if isinstance(path, (list, tuple)): return type(path)(dir_name(path1) for path1 in path)
    if not isinstance(path, str): raise ValueError(f'DirName on {type_str(path)} not possible')
    return os.path.dirname(verify_relative_path(path)) or '.'

def base_name(path: Any) -> Any:
    """
**Returns the final component of a path**

"""
    if path is None: return None
    if isinstance(path, (list, tuple)): return type(path)(base_name(path1) for path1 in path)
    if not isinstance(path, str): raise ValueError(f'BaseName on {type_str(path)} not possible')
    return os.path.basename(verify_relative_path(path))

def file_exists(path: Any) -> Any:
    """
**Returns _True_ if path exists**
"""
    if path is None: return None
    if isinstance(path, (list, tuple)): return type(path)(file_exists(path1) for path1 in path)
    if not isinstance(path, str): raise ValueError(f'FileExists on {type_str(path)} not possible')
    return os.path.exists(verify_relative_path(path))

def is_file(path: Any) -> Any:
    """
**Returns _True_ if path exists and is a regular file**
"""
    if path is None: return None
    if isinstance(path, (list, tuple)): return type(path)(is_file(path1) for path1 in path)
    if not isinstance(path, str): raise ValueError(f'IsFile on {type_str(path)} not possible')
    return os.path.isfile(verify_relative_path(path))

def is_dir(path: Any) -> Any:
    """
**Returns _True_ if path exists and is a directory**
"""
    if path is None: return None
    if isinstance(path, (list, tuple)): return type(path)(is_dir(path1) for path1 in path)
    if not isinstance(path, str): raise ValueError(f'IsDirectory on {type_str(path)} not possible')
    return os.path.isdir(verify_relative_path(path))

def remove_file(path: Any) -> Any:
    """
**Removes a file, returning _True_ if the file was removed or a string error message**
"""
    if path is None: return (False, None)
    if isinstance(path, (list, tuple)): return type(path)(remove_file(path1) for path1 in path)
    if not isinstance(path, str): raise ValueError(f'RemoveFile on {type_str(path)} not possible')
    try:
        os.remove(verify_relative_path(path))
        return (True, None)
    except OSError as e:
        return (False, str(e))

# TODO future
# File listing os.listdir(path)
# Delete a directory os.rmdir(path) (empty only) shutil.rmtree(path) (recursive)
# Rename/move file or dir shutil.move(src, dst)
# Copy file shutil.copy(src, dst)
# Copy directory shutil.copytree(src, dst)
