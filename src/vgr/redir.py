"""
Contains the implementation of OPEN and CLOSE and utility
methods for output.
Handles the stdout/stderr redirection used by statements.
"""

from io import IOBase
import os
import re

from lark import Tree

from .app_exceptions import VgrRuntimeError
from .builtins import bound_ops, verify_relative_path, expand_filename
from .exec_context import ExecContext
from .output import IORedirector

_REDIRECTOR = IORedirector()

def stdin() -> IOBase: return _REDIRECTOR.stdin().file()

def stdout() -> IOBase: return _REDIRECTOR.stdout().file()

def stderr() -> IOBase: return _REDIRECTOR.stderr().file()

def _p_xform(*args):
    """Little hack to override this special case data type"""
    return (a.pattern if isinstance(a, re.Pattern) else a for a in args)

def print_stdout(*args, **kwargs) -> None:
    """Same as print() except that it can redirect to an output file"""
    print(*_p_xform(*args), file=stdout(), **kwargs)

def print_stderr(*args, **kwargs) -> None:
    """Same as print() except that it can redirect to an output file"""
    print(*_p_xform(*args), file=stderr(), **kwargs)

@bound_ops("Open")
def execute_open(ctx: ExecContext, statement: Tree) -> None:
    """
**Send output to a file**

* Open [Output | Error] [File] *file_name* [Overwrite] [;]
* Open [Output | Error] [File] *file_name* No Overwrite [;]
* Open [Output | Error] [File] *file_name* [Extend | Append] [;]

The *file_name* argument is a string for the file to be opened.

If output is already being sent to another file, it is closed first.

When `Extend` or `Append` is used, output is added to the end of an existing file.
When `No Overwrite` is used, the open fails if the file already exists.
Otherwise, if `Overwrite` is used or no option is given the contents of existing files are truncated.

All redirection is closed at program termination.

> **Windows Note**\\
> If you hard code paths, please use the slash as a universal
> directory separator. Since the backslash is an escape character, if you use
> it in a string, you will either need to double it or use a *raw string*.

```vgr
**TODO**
```

Also see `Close`, `Print`, and `Printf`.
"""
    encoding = None # TODO we should be able to support encoding clause
    stream = _eval_stream_name(statement.children[0])
    filename = ctx.eval_filename_expr(statement.children[1])
    if stream == 'stdin':
        mode = statement.children[2].data.lower() if len(statement.children) > 2 else 'r'
        if mode not in ('r'):
            raise VgrRuntimeError(statement.children[2], ValueError('Invalid input mode'))
    else:
        mode = statement.children[2].data.lower() if len(statement.children) > 2 else 'w'
        if mode not in ('a', 'w', 'x'):
            raise VgrRuntimeError(statement.children[2], ValueError('Invalid output mode'))
    try:
        _REDIRECTOR.get_stream(stream).redirect_to(prepare_path(filename, mode), mode=mode, encoding=encoding or 'utf-8')
        ctx.print_verbose(stream, "redirected to", filename)
    except OSError as e:
        # likely has something to do with the file, so point there
        raise VgrRuntimeError(statement.children[1], e) from e
    except Exception as e:
        raise VgrRuntimeError(statement, e) from e

@bound_ops("Close")
def execute_close(ctx: ExecContext, statement: Tree) -> None:
    """
**Close output to a file**

* Close Output [File] [;]
* Close Error [File] [;]

Once closed, command output and errors resumes their default destinations.

All redirection is closed at program termination.

```vgr
**TODO**
```

Also see `Open`
"""
    stream = _eval_stream_name(statement.children[0])
    _REDIRECTOR.get_stream(stream).end_redirect()
    ctx.print_verbose(stream, "closed")

def close_all_redirects() -> None:
    _REDIRECTOR.end_redirects()

def prepare_path(filename: str, mode: str) -> str:
    """
    Creates the directory structure required for the filename.
    Only works with paths relative to the CWD
    """
    full_path = expand_filename(verify_relative_path(filename))
    # Exclude last component, the file name
    if mode != 'r':
        dir_path = os.path.dirname(full_path)
        os.makedirs(dir_path, exist_ok=True)
    return full_path

def _eval_stream_name(node: Tree) -> str:
    """The node's data (name) is the stream name"""
    stream = node.data.lower()
    if stream in ('stderr', 'stdout', 'stdin'): return stream
    raise VgrRuntimeError(node, ValueError('Unknown stream name')) # SNO
