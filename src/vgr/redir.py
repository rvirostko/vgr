"""
Contains the implementation of OPEN and CLOSE and utility
methods for output.
Handles the stdout/stderr redirection used by statements.
"""

from io import IOBase
import re

from lark import Tree

from .app_exceptions import VgrRuntimeError
from .exec_context import ExecContext
from .mathpak import bound_ops
from .output import IORedirector, prepare_path

_REDIRECTOR = IORedirector()

def stdout() -> IOBase:
    return _REDIRECTOR.stdout()

def stderr() -> IOBase:
    return _REDIRECTOR.stderr()

def _p_xform(*args):
    """Little hack to override this special case data type"""
    return (a.pattern if isinstance(a, re.Pattern) else a for a in args)

def print_stdout(*args, **kwargs) -> None:
    """Same as print() except that it can redirect to an output file"""
    print(*_p_xform(*args), file=_REDIRECTOR.stdout(), **kwargs)

def print_stderr(*args, **kwargs) -> None:
    """Same as print() except that it can redirect to an output file"""
    print(*_p_xform(*args), file=_REDIRECTOR.stderr(), **kwargs)

@bound_ops("Open")
def execute_open(ctx: ExecContext, statement: Tree) -> None:
    """
**Send output to a file**

* Open [Output | Error] [File] _expression_ [Overwrite] [;]
* Open [Output | Error] [File] _expression_ No Overwrite [;]
* Open [Output | Error] [File] _expression_ [Extend | Append] [;]

The _expression_ is resolved to a string as the file to be opened.

If output is already being sent to another file, it is closed first.

When *Extend* or *Append* is used, output is added to the end of an existing file.
When *No Overwrite* is used, the command will fail if the file already exists.
Otherwise, if *Overwrite* is used or no mode is given the contents of existing files are truncated.

All redirection is closed at program termination.

Also see `Close`
"""
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
        getattr(_REDIRECTOR, stream)(prepare_path(filename), mode=mode)
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

Also see `Open`
"""
    stream = _eval_stream_name(statement.children[0])
    getattr(_REDIRECTOR, stream)(None)
    ctx.print_verbose(stream, "closed")

def close_all_redirects() -> None:
    _REDIRECTOR.end_redirects()

def _eval_stream_name(node: Tree) -> str:
    """The node's data (name) is the stream name"""
    stream = node.data.lower()
    if stream in ('stderr', 'stdout', 'stdin'): return stream
    raise ValueError(f'Unknown stream {stream}') # SNO
