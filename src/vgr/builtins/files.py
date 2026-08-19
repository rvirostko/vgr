"""
Functions for working with files and directories
"""

from pathlib import Path
from re import Pattern
from typing import Any
import os

from .type import poly_type
from .registry import builtin

@builtin("GetCurrentDirectory")
def get_current_directory(*args) -> str:
    """
**Return the name of the current directory**

* GetCurrentDirectory()

Also see the `os.cwd` variable
"""
    # NB: args ignored
    return expand_filename(os.getcwd())

@builtin("DirectoryName")
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

@builtin("BaseName")
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

@builtin("PathExists")
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

@builtin("IsFile")
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

@builtin("IsDirectory")
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

@builtin("RemoveFile")
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

@builtin("GetFileInfo")
def poly_get_file_info(*args) -> Any:
    """
**Retrieve information about one or more files**

* *path*.GetFileInfo()
* GetFileInfo(*path*&hellip;)

Returns one or more, depending upon argument provided, dictionaries
with information about the requested files.
All files *must* be relative to the current directory.

The *path* arguments are expressions that, eventually, should resolve to a string.
Non-string values are ignored, while lists and dictionaries are traversed for
file paths. In the case of dictionaries, a dictionary using the keys of the
input is returned, the associated values contain the file information.


The contents the information varies depending upon the contents of the
`status` and `type` attributes.

When the file exists-

```vgr
{
    "status": "found",
    "path": "/path/to/file.txt",
    "name": "file.txt",
    "type": "file",
    "size": 12345,
    "modified": 1754500000,
    "created": 1754400000,
    "is_readable": True,
    "is_writable": False,
    "is_executable": False,
    "owner": "user",
    "group": "staff"
}
```

When `type` is `dir`, the `is_executable` attribute is replaced by
`is_searchable` and `size` is omitted.
The availability of creation and modification times, along with `owner` and `group`,
will vary upon operating systems.

When the file does not exist-

```vgr
{
    "status": "not_found",
    "path": "/path/to/file.txt",
    "name": "file.txt",
}
```

When an error has occurred-

```vgr
{
    "status": "error",
    "path": "/path/to/file.txt",
    "name": "file.txt",
    "error": "PermissionError",
    "message": "Permission denied",
}
```

"""
    def _get_owner(stat):
        owner = None
        group = None
        # TODO Need cross platform impl
        return owner, group
    def _get_file_info(path: str) -> dict:
        path: Path = Path(verify_relative_path(path)).resolve()
        info = {
            "path": str(path),
            "name": path.name,
        }
        try:
            if not path.exists():
                info["status"] = "not_found"
                return info
            stat = path.stat()
            info.update({
                "status": "found",
                "type": "dir" if path.is_dir() else "file",
                "modified": int(stat.st_mtime),
                "created": int(stat.st_birthtime) if hasattr(stat, "st_birthtime") else int(stat.st_ctime) if os.name == "nt" else None,
                "is_readable": os.access(path, os.R_OK),
                "is_writable": os.access(path, os.W_OK),
                "is_searchable" if path.is_dir() else "is_executable": os.access(path, os.X_OK)
            })
            if path.is_file(): info["size"] = stat.st_size
            owner, group = _get_owner(stat)
            if owner is not None: info["owner"] = owner
            if group is not None: info["group"] = group
            return info
        except Exception as e:
            info.update({
                "status": "error",
                "error": type(e).__name__,
                "message": str(e),
            })
            return info
    def _dict_unwrap(v, r):
        return r[0] if isinstance(v, str) and (isinstance(r, list) and len(r) == 1) else r
    def _process(value):
        if isinstance(value, str): return [_get_file_info(value)]
        if isinstance(value, list):
            result = []
            for item in value: result.extend(_process(item))
            return result
        if isinstance(value, dict):
            return [{ k: _dict_unwrap(v, _process(v)) for k, v in value.items() if isinstance(v, (str, list, dict)) }]
        return []
    if not args: return None
    results = []
    for arg in args: results.extend(_process(arg))
    # remove superflous array wrapper if they asked for one and got one
    return results[0] if len(args) == 1 and len(results) == 1 else results

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
