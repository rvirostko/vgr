"""
Functions for working with file and dir names.
"""

import os
from typing import Any

from .type import poly_type

def dir_name(path: Any=None) -> Any:
    """
**Returns the directory part of a path**

If path is empty "." is returned, matching UNIX behavior.

```vgr
**TODO**
```
"""
    if path is None: return None
    if isinstance(path, list): return list(dir_name(path1) for path1 in path)
    if not isinstance(path, str): raise ValueError(f'DirName on {poly_type(path)!r} not possible')
    return os.path.dirname(verify_relative_path(path)) or '.'

def base_name(path: Any=None) -> Any:
    """
**Returns the final component of a path**

```vgr
**TODO**
```
"""
    if path is None: return None
    if isinstance(path, list): return list(base_name(path1) for path1 in path)
    if not isinstance(path, str): raise ValueError(f'BaseName on {poly_type(path)!r} not possible')
    return os.path.basename(verify_relative_path(path))

def file_exists(path: Any=None) -> Any:
    """
**Does a path exist**

```vgr
**TODO**
```
"""
    if path is None: return None
    if isinstance(path, list): return list(file_exists(path1) for path1 in path)
    if not isinstance(path, str): raise ValueError(f'FileExists on {poly_type(path)!r} not possible')
    return os.path.exists(verify_relative_path(path))

def is_file(path: Any=None) -> Any:
    """
**Checks to see if a file exists and is it a regular file**

```vgr
**TODO**
```
"""
    if path is None: return None
    if isinstance(path, list): return list(is_file(path1) for path1 in path)
    if not isinstance(path, str): raise ValueError(f'IsFile on {poly_type(path)!r} not possible')
    return os.path.isfile(verify_relative_path(path))

def is_dir(path: Any=None) -> Any:
    """
**Checks to see if a path exist and is it a directory**

```vgr
**TODO**
```
"""
    if path is None: return None
    if isinstance(path, list): return list(is_dir(path1) for path1 in path)
    if not isinstance(path, str): raise ValueError(f'IsDirectory on {poly_type(path)!r} not possible')
    return os.path.isdir(verify_relative_path(path))

def remove_file(path: Any=None) -> Any:
    """
**Removes a file, returning status**

Either returns `True` if the file was removed or a string error message

```vgr
**TODO**
```
"""
    if path is None: return (False, None)
    if isinstance(path, list): return list(remove_file(path1) for path1 in path)
    if not isinstance(path, str): raise ValueError(f'RemoveFile on {poly_type(path)!r} not possible')
    try:
        os.remove(verify_relative_path(path))
        return (True, None)
    except OSError as e:
        return (False, str(e))

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

def expand_filename(filename: str) -> str:
    """
    Returns the full path, absolute with user expansion et al.
    """
    return os.path.realpath(os.path.abspath(os.path.expanduser(filename)))

# TODO future
# File listing os.listdir(path)
# Delete a directory os.rmdir(path) (empty only) shutil.rmtree(path) (recursive)
# Rename/move file or dir shutil.move(src, dst)
# Copy file shutil.copy(src, dst)
# Copy directory shutil.copytree(src, dst)
