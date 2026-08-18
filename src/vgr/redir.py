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
from .encoding import parse_encoding
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

* Open [Output | Error | Input] [File] *file_name* [options]&hellip;

The *file_name* argument is a string for the file to be opened.

If another file is already open, it is closed first.
All opened files are closed at program termination.

**Options**

* `Append` or `Extend` : output is added to the end of an existing file.
  Used with `Output` and `Error`.
* `Overwrite` : overwrite existing files, which is the default.
  Used with `Output` and `Error`.
* `No Overwrite` : operation fails if the file already exists.
  Used with `Output` and `Error`.
* `Read` : can only be used with `Input`.
  This is the default mode for `Input`.
* `Encoding [Is] expr` : Set the encoding for the file.
  The default is *UTF-8*.

**Stream Aliases**

* `stdout` for `Output`
* `stderr` for `Error`
* `stdin` for `Input`

> **Windows Note**\\
> If you hard code paths, please use the slash as a universal
> directory separator. Since the backslash is an escape character, if you use
> it in a string, you will either need to double it or use a *raw string*.

```vgr
Open Output File "out.txt" Append
    # added to end of file
    Print "Hello, World"
    # does not appear in file
    Print Error "-No errors-"
Close Output File
```

> **Note**\\
> The indention of statements inside an `Open` and `Close`
> is a convention, not a requirement.

Also see `Close`, `Print`, and `Printf`.
"""
    stream = _eval_stream_name(statement.children[0])
    filename = ctx.eval_filename_expr(statement.children[1])
    mode = None
    encoding = None
    for child in statement.children[2:]:
        name = child.data.lower()
        if name in ('a', 'w', 'x'):
            if stream == 'stdin': raise VgrRuntimeError(child, ValueError('Invalid input mode'))
            mode = name
        elif name in ('r'):
            if stream != 'stdin': raise VgrRuntimeError(child, ValueError('Invalid output mode'))
        elif name == 'encoding':
            encoding = parse_encoding(ctx, child)
        else:
            # SNO
            raise VgrRuntimeError(child, ValueError(f'Option {name!r} not handled')) # pragma no cover
    mode = mode or ('r' if stream == 'stdin' else 'w')
    encoding = encoding or 'utf-8'
    try:
        _REDIRECTOR.get_stream(stream).redirect_to(
            prepare_path(filename, mode),
            mode=mode,
            encoding=encoding,
            errors='backslashreplace' if ctx.debug else 'replace')
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

* Close [Output | Error | Input] [File]

Once closed, the stream resumes it default.

If not already open, the command is ignored.
All opened files are closed at program termination.

```vgr
Open Output File "out.txt" Append
    # added to end of file
    Print "Hello, World"
Close Output File
# does not appear in file
Print "Hello, Again"
```

> **Note**\\
> The indention of statements inside an `Open` and `Close`
> is a convention, not a requirement.

Also see `Open` and `Reset`
"""
    stream = _eval_stream_name(statement.children[0])
    _REDIRECTOR.get_stream(stream).end_redirect()
    ctx.print_verbose(stream, "closed")

def close_all_redirects() -> None:
    _REDIRECTOR.end_redirects()

def prepare_path(filename: str, mode: str='r') -> str:
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
    # SNO
    raise VgrRuntimeError(node, ValueError('Unknown stream name')) # pragma no cover
