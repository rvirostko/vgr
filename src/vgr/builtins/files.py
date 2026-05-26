"""
Functions for working with file and dir names.
"""

from re import Pattern
from typing import Any
import os

from .type import poly_type

def get_cwd() -> str:
    """
**Return the name of the current directory**

* GetCurrentDirectory()

Also see the `os.cwd` variable
"""
    return expand_filename(os.getcwd())

def dir_name(path: Any=None) -> Any:
    """
**Returns the directory part of a path**

* DirectoryName()
* *path*.DirectoryName()
* DirectoryName(*path*)

If *path* is empty or `None` "." is returned, matching UNIX behavior.

```vgr
DirectoryName("samples") → "." # samples dir exists in current dir
DirectoryName("samples/sse.vgr") → "samples"
```

Also see `BaseName()`
"""
    if path is None: return '.'
    if isinstance(path, list): return list(dir_name(path1) for path1 in path)
    path = _stringify(path)
    if isinstance(path, str): return os.path.dirname(verify_relative_path(path)) or '.'
    raise ValueError(f'DirectoryName on {poly_type(path)!r} not possible')

def base_name(path: Any=None) -> Any:
    """
**Returns the final component of a path**

* BaseName()
* *path*.Basename()
* Basename(*path*)

If *path* is empty or `None` "" is returned, matching UNIX behavior.

```vgr
BaseName("") → ""
BaseName("samples") → "samples"
BaseName("samples/sse.vgr") → "sse.vgr"
```

Also see `DirectoryName()`
"""
    if path is None: return ''
    if isinstance(path, list): return list(base_name(path1) for path1 in path)
    path = _stringify(path)
    if isinstance(path, str): return os.path.basename(verify_relative_path(path))
    raise ValueError(f'BaseName on {poly_type(path)!r} not possible')

def path_exists(path: Any=None) -> Any:
    """
**Returns True if path refers to an existing file or directory**

* PathExists()
* *path*.PathExists()
* PathExists(*path*)

```vgr
PathExists("") → True
PathExists(".") → True
PathExists("samples") → True
PathExists("samples/sse.vgr") → True
PathExists("samples/no") → False
```

Also see `IsFile()` and `IsDirectory()`
"""
    if path is None: return True # same as if "."
    if isinstance(path, list): return list(path_exists(path1) for path1 in path)
    path = _stringify(path)
    if isinstance(path, str): return os.path.exists(verify_relative_path(path or '.'))
    raise ValueError(f'PathExists on {poly_type(path)!r} not possible')

def is_file(path: Any=None) -> Any:
    """
**Checks to see if a file exists and is it a regular file**

* IsFile()
* *path*.IsFile()
* IsFile(*path*)

```vgr
IsFile("") → False
IsFile("samples") → False
IsFile("samples/sse.vgr") → True
IsFile("samples/no") → False
```
"""
    if path is None: return False # same as if "."
    if isinstance(path, list): return list(is_file(path1) for path1 in path)
    path = _stringify(path)
    if isinstance(path, str): return os.path.isfile(verify_relative_path(path) or '.')
    raise ValueError(f'IsFile on {poly_type(path)!r} not possible')

def is_dir(path: Any=None) -> Any:
    """
**Checks to see if a path exist and is it a directory**

* IsDirectory()
* *path*.IsDirectory()
* IsDirectory(*path*)

```vgr
IsDirectory("") → True
IsDirectory("samples") → True
IsDirectory("samples/sse.vgr") → False
```
"""
    if path is None: return True
    if isinstance(path, list): return list(is_dir(path1) for path1 in path)
    path = _stringify(path)
    if isinstance(path, str): return os.path.isdir(verify_relative_path(path) or '.')
    raise ValueError(f'IsDirectory on {poly_type(path)!r} not possible')

def remove_file(path: Any=None) -> Any:
    """
**Removes a file, returning status**

* *path*.RemoveFile()
* RemoveFile(*path*)

Returns a list containing two elements:

* *result*.FirstItem() - Boolean, reflecting the operations success
* *result*.LastItem() - String, description of the error on failure
  otherwise `None`

```vgr
RemoveFile("") → [False, "Missing path"]
RemoveFile("exists.txt") → [True, None]
RemoveFile("not-exists.txt") → [False, "[Errno 2] No such file or directory: 'not-exists.txt'"]
RemoveFile("a_dir") → [False, "[Errno 1] Operation not permitted: 'a_dir'"]
```
"""
    if path is None: return [False, "Missing path"]
    if isinstance(path, list): return list(remove_file(path1) for path1 in path)
    path = _stringify(path)
    if isinstance(path, str):
        if len(path) == 0: return [False, "Missing path"]
        try:
            os.remove(verify_relative_path(path))
            return [True, None]
        except OSError as e:
            return [False, str(e)]
    raise ValueError(f'RemoveFile on {poly_type(path)!r} not possible')

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

def _stringify(x) -> Any:
    """While of limited value, behavior is consistent with other ops"""
    if isinstance(x, (bool, int, float)): return str(x)
    if isinstance(x, Pattern): return x.pattern
    return x
