"""
Contains the implementation of OPEN and CLOSE and utility
methods for output.
Handles the stdout/stderr redirection used by statements.
"""

from io import IOBase
import textwrap

from lark import Tree

from evaluate import eval_filename_expr
from output import IORedirector, prepare_path
from data_dict import DataDictionary
from app_exceptions import ExitingException

_REDIRECTOR = IORedirector()

def stdout() -> IOBase:
    return _REDIRECTOR.stdout()

def stderr() -> IOBase:
    return _REDIRECTOR.stderr()

def print_stdout(*args, **kwargs) -> None:
    """Same as print() except that it can redirect to an output file"""
    print(*args, file=_REDIRECTOR.stdout(), **kwargs)

def print_stderr(*args, **kwargs) -> None:
    """Same as print() except that it can redirect to an output file"""
    print(*args, file=_REDIRECTOR.stderr(), **kwargs)

def shorten(s: str, width: int=64) -> str:
    """
    Limits output that can appear in debug/verbose content.
    Should be used with repr(...) when you don't know the object size.
    """
    return textwrap.shorten(s, width=width, placeholder="\u2026")

def execute_open(dd: DataDictionary, statement: Tree) -> None:
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

See *Close*
"""
    stream = _eval_stream_name(statement.children[0])
    filename = eval_filename_expr(dd, statement.children[1])
    mode = 'w'
    if len(statement.children) > 2: mode = statement.children[2].data.lower()
    if mode not in ('a', 'w', 'x'): raise ValueError(f'Unknown mode {mode}') # SNO
    try:
        getattr(_REDIRECTOR, stream)(prepare_path(filename), mode=mode)
        if dd.verbose: print_stderr(stream, "redirected to", filename)
    except Exception as e:
        raise ExitingException(ExitingException.EXIT_FAILED, statement, str(e)) from e

def execute_close(dd: DataDictionary, statement: Tree) -> None:
    """
**Close output to a file**

* Close Output [File] [;]
* Close Error [File] [;]

Once closed, command output and errors resumes their default destinations.

All redirection is closed at program termination.

See *Open*
"""
    stream = _eval_stream_name(statement.children[0])
    getattr(_REDIRECTOR, stream)(None)
    if dd.verbose: print_stderr(stream, "closed")

def _eval_stream_name(node: Tree) -> str:
    """The node's data (name) is the stream name"""
    stream = node.data.lower()
    if stream in ('stderr', 'stdout'): return stream
    raise ValueError(f'Unknown stream {stream}') # SNO
