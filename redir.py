#! /usr/bin/env python3

from io import IOBase

from lark import Tree

from evaluate import eval_filename_expr
from output import IORedirector, prepare_path
from data_dict import DataDictionary
from app_exceptions import ExitingException

_REDIR = IORedirector()

def stdout() -> IOBase:
    return _REDIR.stdout()

def print_stdout(*args, **kwargs) -> None:
    """Same as print() except that it can redirect to an output file"""
    print(*args, file=_REDIR.stdout(), **kwargs)

def print_stderr(*args, **kwargs) -> None:
    """Same as print() except that it can redirect to an output file"""
    print(*args, file=_REDIR.stderr(), **kwargs)

def print_debug(dd: DataDictionary, /, *args, **kwargs) -> None:
    """If debug is on print to stderr"""
    if dd.is_debug(): print_stderr(*args, **kwargs)

def print_verbose(dd: DataDictionary, /, *args, **kwargs) -> None:
    """If verbose is on print to stderr"""
    if dd.is_verbose(): print_stderr(*args, **kwargs)

def execute_open(dd: DataDictionary, statement: Tree) -> None:
    """Send command output or error output to a file

* OPEN [OUTPUT | ERROR] [FILE] _expression_ [OVERWRITE] [;]
* OPEN [OUTPUT | ERROR] [FILE] _expression_ NO OVERWRITE [;]
* OPEN [OUTPUT | ERROR] [FILE] _expression_ [EXTEND | APPEND] [;]

The _expression_ is resolved to a string as the file to be opened

If output is being sent to another file, it is closed first.

When EXTEND or APPEND is used, output is added to the end of an existing file.
When NO OVERWRITE is used, the command will fail if the file already exists.
Otherwise, if OVERWRITE is used of no mode is given and the file already exists, its contents are truncated.

All redirection is closed at program termination.

See CLOSE
"""
    stream = _eval_stream_name(statement.children[0])
    filename = eval_filename_expr(dd, statement.children[1])
    mode = 'w'
    if len(statement.children) > 2: mode = statement.children[2].data.lower()
    if mode not in ('a', 'w', 'x'): raise ValueError(f'Unknown mode {mode}') # SNO
    try:
        getattr(_REDIR, stream)(prepare_path(filename), mode=mode)
        print_verbose(dd, stream, "redirected to", filename)
    except Exception as e:
        raise ExitingException(ExitingException.EXIT_FAILED, statement, str(e)) from e

def execute_close(dd: DataDictionary, statement: Tree) -> None:
    """Close the output or error file

* CLOSE OUTPUT [FILE] [;]
* CLOSE ERROR [FILE] [;]

Once closed, command output and errors resumes their default destinations.

All redirection is closed at program termination.
"""
    stream = _eval_stream_name(statement.children[0])
    getattr(_REDIR, stream)(None)
    print_verbose(dd, stream, "closed")

def _eval_stream_name(node: Tree) -> str:
    """The node's data (name) is the stream name"""
    stream = node.data.lower()
    if stream in ('stderr', 'stdout'): return stream
    raise ValueError(f'Unknown stream {stream}') # SNO
