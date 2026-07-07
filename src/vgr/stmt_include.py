"""The @Include and Source commands"""

from pathlib import Path
import os

from lark import Tree

from .app_exceptions import VgrRuntimeError
from .exec_context import ExecContext
from .builtins import (
    bound_ops,
    poly_repr,
    expand_filename,
)

_INCLUDED_FILES: list[str] = []
_IS_INCLUDED: list[bool] = []
_VGR_PATH: list[Path] = []

def get_includes() -> list:
    """The files that have been "@Include"d rather than "Source"d (vgr.includes)"""
    return _INCLUDED_FILES

def clear_includes() -> None:
    _INCLUDED_FILES.clear()

def _is_included(path) -> bool:
    return str(path) in _INCLUDED_FILES

def get_is_included() -> bool:
    """Files can look at vgr.included to see if they are being included vs sourced"""
    return _IS_INCLUDED[-1] if len(_IS_INCLUDED) > 0 else False

@bound_ops("@Include")
def execute_include(ctx: ExecContext, statement: Tree) -> None:
    """
**Execute statements stored in a file once per run**

* @Include [File | Files] *file_name*[, *file_name*]&hellip;

Similar to `Source` but files are only included once per run, unless
cleared by `Reset`.

If *file_name* does not include a path, the *VGR_PATH* defined
in the environment is searched for the file. If not found initially,
and the file does not contain an extension, the search is performed
again using an extension of *vgr*.

> **Windows Note**\\
> If you hard code paths, please use the slash as a universal
> directory separator. Since the backslash is an escape character, if you use
> it in a string, you will either need to double it or use a *raw string*.

```vgr
Verbose
Verbose = True
@Include None
@Include File "init.vgr"
Executing statements from "/Users/tc/VGR/init.vgr"...
@Include File "init.vgr"
Skipping "/Users/tc/VGR/init.vgr": previously included
Reset Includes
Resetting includes
@Include File "init.vgr"
Executing statements from "/Users/tc/VGR/init.vgr"...
```

Also see `Source` and `Reset`
"""
    for child in statement.children:
        try:
            do_include(ctx, _find_source(ctx, child))
        except Exception as e:
            raise VgrRuntimeError(child, e) from e

def do_include(ctx: ExecContext, path: Path) -> None:
    if path is not None:
        if _is_included(path):
            if ctx.verbose: ctx.print_verbose(f'Skipping {poly_repr(str(path))}: previously included')
        else:
            do_source(ctx, path, True)
            _INCLUDED_FILES.append(str(path))

def find_vgr_source(filename: str) -> Path:
    """
    Find a VGR source file for sourcing or including
    """
    filepath = _resolve_vgr_path(filename)
    if filepath is not None: return filepath
    # Require that it be a local reference
    full_path = expand_filename(filename)
    cwd = expand_filename(os.getcwd())
    if os.path.commonpath([cwd, full_path]) != cwd:
        raise ValueError(f'File {poly_repr(full_path)} not relative to {poly_repr(cwd)}')
    return Path(full_path)

def _find_source(ctx: ExecContext, expr: Tree) -> Path:
    """
    Internal version of find_vgr_source() that works with values
    from the parse tree.
    """
    filename = ctx.eval_to_str(expr, 'File name', True)
    return None if filename is None else find_vgr_source(filename)

@bound_ops("Source")
def execute_source(ctx: ExecContext, statement: Tree) -> None:
    """
**Execute statements stored in a file**

* Source [File | Files] *file_name*[, *file_name*]&hellip;

Each argument is evaluated to a file name. Statements in the file
are executed, inheriting the current state of all variable and
input/output redirection.

If *file_name* does not include a path, the *VGR_PATH* defined
in the environment is searched for the file. If not found initially,
and the file does not contain an extension, the search is performed
again using an extension of *vgr*.

> **Windows Note**\\
> If you hard code paths, please use the slash as a universal
> directory separator. Since the backslash is an escape character, if you use
> it in a string, you will either need to double it or use a *raw string*.

```vgr
Source None # ignored
Source File "init.vgr"
Source Files "step1.vgr", "step2.vgr"
Source "session_" + session_id

# Looks only for file in the same directory as the
# current source
Set filename To vgr.source.FirstItem().DirectoryName() + "/people.vgr"
Source filename
```

Also see `@Include`, `Reset`, and `DirectoryName()`
"""
    for child in statement.children:
        try:
            path = _find_source(ctx, child)
            if path is not None: do_source(ctx, path)
        except Exception as e:
            raise VgrRuntimeError(child, e) from e

def do_source(ctx: ExecContext, path: Path, included: bool=False) -> None:
    filename = str(path)
    if not path.exists():
        raise FileNotFoundError(0, f'File {filename!r} not found')
    if not path.is_file():
        raise IsADirectoryError(0, f'{filename!r} does not reference a file')
    if not os.access(path, os.R_OK):
        raise PermissionError(0, f'File {filename!r} not readable')
    statements = None
    if ctx.verbose: ctx.print_verbose(f'Executing statements from {poly_repr(filename)}...')
    # If we replace the errors, it probably won't parse (unless it is in a comment)
    # but this way the user can find the error line, rather than getting a
    # cryptic error from the read
    with open(path, 'r', encoding='utf-8', errors='backslashreplace') as f:
        statements = f.read()
    try:
        # Push whether the file is included or sourced
        _IS_INCLUDED.append(included)
        ctx.execute_statements(statements, str(path))
    finally:
        # Pop the indicator
        _IS_INCLUDED.pop()

def _resolve_vgr_path(filename: str) -> Path:
    """
    Using get_vgr_path(), try to find a VGR source file.
    If filename contains any path info, it must be relative to the CWD.
    Returning None means we didn't find it on the path.
    It does *NOT* mean the file doesn't exist.
    Likewise, returning a non-None value doesn't mean the item is
    a readable file, only that it exists.

    Behavior is modeled after AWKPATH:
    https://www.gnu.org/software/gawk/manual/html_node/AWKPATH-Variable.html
    """
    # If filename does not include a path component we consult the path
    if (os.sep not in filename) and (not os.altsep or os.altsep not in filename):
        search_dirs = _get_vgr_path()
        def _search(name: str):
            for d in search_dirs:
                if d.exists():
                    candidate = d / name
                    if candidate.exists(): return candidate.resolve()
            return None
        # First pass: exact name
        found = _search(filename)
        if found: return found
        # Second pass: try with extension
        if not filename.lower().endswith('.vgr'):
            found = _search(filename + '.vgr')
            if found: return found
    return None

def _get_vgr_path() -> list[Path]:
    """
    Parse VGR_PATH into a list of paths.
    If if not defined in the environment, platform specific defaults
    are choosen. The parsing is done once, so changing `env.VGR_PATH` does not
    affect this.
    """
    if len(_VGR_PATH) == 0:
        envpath = os.environ.get("VGR_PATH")
        if envpath is not None:
            entries = [(path.strip() or '.') for path in envpath.split(os.pathsep)]
        else:
            # OS-appropriate sensible defaults
            if os.name == 'posix':
                entries = ['.', str(Path.home() / '.vgr'), '/usr/local/share/vgr', '/usr/share/vgr']
            elif os.name == 'nt':
                entries = ['.', str(Path.home() / 'vgr')]
                pf = os.environ.get('PROGRAMFILES')
                if pf: entries.append(str(Path(pf) / 'vgr' / "lib"))
            else:
                entries = ['.', str(Path.home() / 'vgr')]
        for entry in entries:
            # Don't check for exist() here: user can create after start in repl
            _VGR_PATH.append(Path(expand_filename(entry)))
    return _VGR_PATH
