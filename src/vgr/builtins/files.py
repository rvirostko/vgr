"""
Functions for working with files and directories
"""

from pathlib import Path
from re import Pattern
from typing import Any
import fnmatch
import glob
import os
import re

from .common import apply_vargs
from .type import poly_type
from .registry import builtin

@builtin("GetCurrentDirectory")
def get_current_directory(*_args) -> str:
    """
**Return the name of the current directory**

* GetCurrentDirectory()
"""
    # NB: args ignored
    return expand_filename(os.getcwd())

@builtin("ExpandPath")
def poly_expand_path(*args) -> Any:
    """
**Expands the path to an absolute system path**

* *path.ExpandPath()
* ExpandPath(*path*)

Note that this functions does *not* check for the directory
or file name portion's existance.

```vgr
ExpandPath(None) → None
ExpandPath("") → <current directory>
ExpandPath("samples") → "<current directory>/samples"
ExpandPath("samples/sse.vgr") → "<current directory>/samples/sse.vgr"
```

Also see `GetCurrentDirectory()`
"""
    def _expand(path) -> Any:
        if path is None: return None
        if isinstance(path, list): return list(_expand(path1) for path1 in path)
        path = _stringify(path)
        if isinstance(path, str): return expand_filename(verify_relative_path(path or "."))
        raise ValueError(f'ExpandPath on {poly_type(path)!r} not supported')
    return apply_vargs(args, _expand)

@builtin("DirectoryName")
def poly_dir_name(*args) -> Any:
    """
**Returns the directory part of a path**

* *path*.DirectoryName()
* DirectoryName(*path*)

Extracts and returns the parent directory name from the path.
If *path* does not contain a directory component, the current
directory is returned.

Note that this functions does *not* check for the directory
or file name portion's existance.

```vgr
DirectoryName(None) → None
DirectoryName("") → <current directory>
DirectoryName("samples") → <current directory>
DirectoryName("samples/sse.vgr") → "<current directory>/samples"
```

Also see `BaseName()`, `PathExists()`, and `GetCurrentDirectory()
"""
    def _dir_name(path):
        if path is None: return None
        if isinstance(path, list): return list(_dir_name(path1) for path1 in path)
        path = _stringify(path)
        if isinstance(path, str):
            return os.path.dirname(expand_filename(verify_relative_path(path or ".")))
        raise ValueError(f'DirectoryName on {poly_type(path)!r} not supported')
    return apply_vargs(args, _dir_name)

@builtin("BaseName")
def poly_base_name(*args) -> Any:
    """
**Returns the final component of a path**

* *path*.Basename()
* Basename(*path*)

Extracts and returns the file name portion from the path.

Note that this functions does *not* check for the directory
or file name portion's existance.

```vgr
BaseName("") → ""
BaseName("samples") → "samples"
BaseName("samples/sse.vgr") → "sse.vgr"

BaseName(None) → None
BaseName("") → ""
BaseName("samples") → "samples"
BaseName("samples/sse.vgr") → "sse.vgr"

```

Also see `DirectoryName()`, `PathExists()`, and `GetCurrentDirectory()`
"""
    def _base_name(path):
        if path is None: return None
        if isinstance(path, list): return list(_base_name(path1) for path1 in path)
        path = _stringify(path)
        if isinstance(path, str): return os.path.basename(verify_relative_path(path))
        raise ValueError(f'BaseName on {poly_type(path)!r} not supported')
    return apply_vargs(args, _base_name)

@builtin("PathExists")
def poly_path_exists(*args) -> Any:
    """
**Returns True if path refers to an existing file or directory**

* *path*.PathExists()
* PathExists(*path*)

```vgr
PathExists(None) → None
PathExists("") → True
PathExists(".") → True
PathExists("samples") → True
PathExists("samples/sse.vgr") → True
PathExists("samples/not-a-file") → False
```

Also see `IsFile()` and `IsDirectory()`
"""
    def _path_exists(path):
        if path is None: return None
        if isinstance(path, list): return list(_path_exists(path1) for path1 in path)
        path = _stringify(path)
        if isinstance(path, str):
            if len(path) == 0: path = get_current_directory()
            return os.path.exists(verify_relative_path(path or "."))
        raise ValueError(f'PathExists on {poly_type(path)!r} not supported')
    return apply_vargs(args, _path_exists)

@builtin("IsFile")
def poly_is_file(*args) -> Any:
    """
**Checks to see if a file exists and that it is a regular file**

* IsFile()
* *path*.IsFile()
* IsFile(*path*)

```vgr
IsFile(None) → None
IsFile("") → False
IsFile("samples") → False
IsFile("samples/sse.vgr") → True
IsFile("samples/not-a-file") → False
```
"""
    def _is_file(path):
        if path is None: return None
        if isinstance(path, list): return list(_is_file(path1) for path1 in path)
        path = _stringify(path)
        if isinstance(path, str):
            return os.path.isfile(verify_relative_path(path or "."))
        raise ValueError(f'IsFile on {poly_type(path)!r} not supported')
    return apply_vargs(args, _is_file)

@builtin("IsDirectory")
def poly_is_dir(*args) -> Any:
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
    def _is_dir(path):
        if path is None: return None
        if isinstance(path, list): return list(_is_dir(path1) for path1 in path)
        path = _stringify(path)
        if isinstance(path, str): return os.path.isdir(verify_relative_path(path or '.'))
        raise ValueError(f'IsDirectory on {poly_type(path)!r} not supported')
    return apply_vargs(args, _is_dir)

@builtin("RemoveFile")
def poly_remove_file(*args) -> Any:
    """
**Removes a file, returning status**

* *path*.RemoveFile()
* RemoveFile(*path*)

Removes individual files, but not directories.

Returns a list containing two elements:

* *result*.FirstItem() - Boolean, reflecting the operations success
* *result*.LastItem() - String, description of the error on failure
  otherwise `None`

```vgr
RemoveFile("exists.txt") → [True, None]
RemoveFile("not-exists.txt") → [False, "[Errno 2] No such file or directory: 'not-exists.txt'"]
RemoveFile("a_dir") → [False, "[Errno 1] Operation not permitted: 'a_dir'"]
```
"""
    def _remove_file(path):
        if path is None: return None
        if isinstance(path, list): return list(_remove_file(path1) for path1 in path)
        path = _stringify(path)
        if isinstance(path, str):
            try:
                os.remove(verify_relative_path(path or "."))
                return [True, None]
            except OSError as e:
                return [False, str(e)]
        raise ValueError(f'RemoveFile on {poly_type(path)!r} not supported')
    return apply_vargs(args, _remove_file)

@builtin("GetFileInfo")
def poly_get_file_info(*args) -> Any:
    """
**Retrieve information about one or more files**

* *path*.GetFileInfo()
* GetFileInfo(*path*&hellip;)

Returns one or more, depending upon argument provided,
with information about the requested files.
All file paths *must* be relative to the current directory.

The contents the information varies depending upon the contents of the
`found`, `error`, and `type` attributes.

When the file exists-

```vgr
{
    "found":         True,
    "path":          "/path/to/file.txt",
    "name":          "file.txt",
    "suffix":        ".txt",
    "type":          "file",
    "size":          12345,
    "modified":      1754500000,
    "created":       1754400000,
    "is_readable":   True,
    "is_writable":   False,
    "is_executable": False,
    "owner":         "user",
    "group":         "staff"
}
```

When `type` is `directory`, the `is_executable` attribute is replaced by
`is_searchable` and `size` is omitted.
The availability of creation and modification times, along with `owner` and `group`,
will vary by operating environments.

When the file does not exist-

```vgr
{
    "found":  False,
    "path":   "/path/to/file.txt",
    "suffix": ".txt",
    "name":   "file.txt",
}
```

When an error has occurred-

```vgr
{
    "path":    "/path/to/file.txt",
    "name":    "file.txt",
    "suffix":  ".txt",
    "error":   "PermissionError",
    "message": "Permission denied",
}
```

"""
    def _get_file_info(path: str) -> dict:
        if path is None: return None
        if isinstance(path, list): return list(_get_file_info(path1) for path1 in path)
        path = _stringify(path)
        if not isinstance(path, str):
            raise ValueError(f'GetFileInfo on {poly_type(path)!r} not supported')
        path: Path = Path(verify_relative_path(path)).resolve()
        info = {
            "path": str(path),
            "name": path.name,
        }
        suffixes = path.suffixes
        if len(suffixes) == 1:
            info["suffix"] = suffixes[0]
        elif len(suffixes) > 1:
            info["suffixes"] = suffixes
        try:
            if not path.exists():
                info["found"] = False
                return info
            # Windows will likely raise NotImplemented (except WSL and Cygwin)
            # Posix systems can raise KeyError for deleted group/user
            # OsError for permission issues (maybe)
            try: info["owner"] = path.owner()
            except (NotImplementedError, KeyError, OSError): pass
            try: info["group"] = path.group()
            except (NotImplementedError, KeyError, OSError): pass
            stat = path.stat()
            info.update({
                "found":        True,
                "type":         "directory" if path.is_dir() else "file",
                "modified":     int(stat.st_mtime),
                "created":      int(stat.st_birthtime) if hasattr(stat, "st_birthtime") else int(stat.st_ctime) if os.name == "nt" else None,
                "is_readable":  os.access(path, os.R_OK),
                "is_writable":  os.access(path, os.W_OK),
                "is_searchable" if path.is_dir() else "is_executable": os.access(path, os.X_OK)
            })
            if path.is_file(): info["size"] = stat.st_size
            return info
        except Exception as e:
            info.update({
                "error": type(e).__name__,
                "message": str(e),
            })
            return info
    return apply_vargs(args, _get_file_info)

@builtin("ListFiles")
def poly_list_files(*args) -> Any:
    """
**Return a list of files using a pattern match**

* ListFiles() *files in current directory*
* ListFiles(*pattern*[, *pattern*&hellip;])
* *pattern*.ListFiles()

The *pattern* follows the [Glob](https://en.wikipedia.org/wiki/Glob_\\(programming\\))
style of meta characters:

| Pattern   | Meaning                                       |
|-----------|-----------------------------------------------|
| _*_       | matches everything                            |
| _?_       | matches any single character                  |
| _**_      | match any files and zero or more directories  |
| _[abc]_   | matches any character in sequence             |
| _[a-c]_   | matches any character in the range            |
| _[!...]_  | matches any character not in equence or range |
| _~_       | expanded to the user's home directory         |
| _~name_   | expanded to the home directory of a user      |

Matching of literal character may be case sensitive depending
upon the operating environment, including the file system format.

To list files or directories that start with `.`, the pattern
*must* start with a dot.
Dot files are excluded from the results by default.

To list directories only, end the pattern with the path
separator character for the operating system: see `os.sep`

When multiple patterns are given, the results are combined
into a single list. The is not sorted, nor are duplicate
items removed.

```vgr
# All files, except dot files, in the current directory
ListFiles("*")

# Only sub directories
ListFiles("*/")

# All files in the current directory and in all subdirectories
ListFiles("**")

# All the subdirectories, but no files
ListFiles("**/")

# All JSON files in a directory
# Note: case independence not guaranteed
ListFiles("*.json")

# All JSON in the directory and all subdirectories
ListFiles("**/*.json")

# All JSON and CSV in the directory and all subdirectories
ListFiles("**/*.json", "**/*.csv")

# All files in a single subdirectory
# Note: the final "*" is required
ListFiles("reports/*")
```

Also see `EscapeGlobPattern()`
"""
    cwd: str = os.getcwd() + os.sep
    def _list_files(path: str) -> list:
        if path is None: return None
        if isinstance(path, list): return list(_list_files(path1) for path1 in path)
        path = _stringify(path)
        if isinstance(path, str):
            # NB: trailing "/" gets stripped after check/expansion
            #     so record the request now
            dirs_only: bool = path.endswith(os.sep)
            path = str(Path(verify_relative_path(path)).resolve())
            results = glob.glob(path, recursive="**" in path)
            if dirs_only:
                return [s.removeprefix(cwd).removesuffix(os.sep) for s in results if s != cwd and os.path.isdir(s)]
            return [s.removeprefix(cwd) for s in results]
        raise ValueError(f'ListFiles on {poly_type(path)!r} not supported')
    def _flatten(items) -> list:
        result = []
        for item in items:
            if item is None: continue
            if isinstance(item, list):
                result.extend(_flatten(item))
            else:
                result.append(item)
        return result
    listing = apply_vargs(("*",) if len(args) == 0 else args, _list_files)
    return None if listing is None else _flatten(listing)

@builtin("EscapeGlobPattern")
def poly_escape_glob(*args) -> Any:
    """
**Escape Glob meta characters for use in literal matching**

* EscapeGlobPattern(*pattern*[, *pattern*&hellip;])
* *pattern*.EscapeGlobPattern()

Also see `ListFiles()`
"""
    def _escape_glob(pattern: str) -> str:
        if pattern is None: return None
        if isinstance(pattern, list): return list(_escape_glob(pattern1) for pattern1 in pattern)
        pattern = _stringify(pattern)
        if isinstance(pattern, str): return glob.escape(pattern)
        raise ValueError(f'EscapeGlobPattern on {poly_type(pattern)!r} not supported')
    return apply_vargs(args, _escape_glob)

@builtin("GlobToPattern")
def poly_glob_to_pattern(*args) -> Any:
    """
**Convert a Glob pattern into a regular expression**

* GlobToPattern(*pattern*[, *pattern*&hellip;])
* *pattern*.GlobToPattern()

```vgr
GlobToPattern("file.txt") → r/(?s:file\\.txt)\\Z/
```

Also see `CompilePattern()`
"""
    def _glob_to_pattern(pattern: str) -> str:
        if pattern is None: return None
        if isinstance(pattern, list): return list(_glob_to_pattern(pattern1) for pattern1 in pattern)
        pattern = _stringify(pattern)
        if isinstance(pattern, str): return re.compile(fnmatch.translate(pattern))
        raise ValueError(f'GlobToPattern on {poly_type(path)!r} not supported')
    return apply_vargs(args, _glob_to_pattern)

def verify_relative_path(filename: str) -> str:
    """
    The filename must be relative to the current directory.
    Returns filename unchanged.
    """
    okay, _ = _check_relative_path(filename)
    if okay: return filename
    # NB: don't leak parts of the file system via error messages
    raise OSError(f'File {filename!r} not relative to current directory')

def expand_filename(filename: str) -> str:
    """
    Returns the full path, absolute with user expansion et al.
    """
    return os.path.realpath(os.path.abspath(os.path.expanduser(filename)))

def _check_relative_path(filename: str) -> tuple:
    return [os.path.commonpath([cwd := expand_filename(os.getcwd()), full_path := expand_filename(filename)]) == cwd, full_path]

def _stringify(x) -> Any:
    """While of limited value, behavior is consistent with other ops"""
    if isinstance(x, (bool, int, float)): return str(x)
    if isinstance(x, Pattern): return x.pattern
    return x
