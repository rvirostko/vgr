"""
Implementations of Print, PrintF, and MdPrint
"""

import os
import sys
from io import StringIO

from lark import Tree

from .dd_config import OFS_PATH, ORS_PATH
from .redir import print_stdout, print_stderr
from .exec_context import ExecContext
from .mathpak import poly_format, bound_ops
from .doc_help import print_md

def _extract_args(tree: Tree) -> tuple:
    if not tree.children: return 'stdout', []
    first = tree.children[0]
    if isinstance(first, Tree) and first.data in {'stderr', 'stdout', 'markdown'}:
        return first.data, tree.children[1:]
    return "stdout", tree.children

def _print_md(*args, **kwargs):
    if sys.stdout.isatty():
        buf = StringIO()
        print(*args, file=buf, **kwargs)
        print_md(buf.getvalue())
    else:
        print_stdout(*args, **kwargs)

_CHANNEL_MAP = {
    "stderr": print_stderr,
    "stdout": print_stdout,
    "markdown": _print_md,
}

@bound_ops("Print")
def execute_print(ctx: ExecContext, statement: Tree) -> None:
    """
**Print values, similar to AWK's print statement**

* Print [Output | Error | Markdown] _expression_ [, _expression_]... [;]

Default destination is `Output`. `Markdown` always goes to the current console.
If the console is redirected to a file `Markdown` output written as text.

The results of the expressions are separated by the string defined in _arg.ofs_.
Lines are ended by with the _arg.ors_ string. The defaults are space and new line and
are used if the values are set to _None_.
If there are no expressions to print only the _arg.ors_ is printed.
"""
    channel, args = _extract_args(statement)
    sep = ctx.get_var(*OFS_PATH)
    sep = ' ' if sep is None else str(sep)
    end = ctx.get_var(*ORS_PATH)
    end = os.linesep if end is None else str(end)
    _CHANNEL_MAP[channel](*[ctx.eval_expr(expr) for expr in args] if args else '', sep=sep, end=end, flush=True)

@bound_ops("Printf")
def execute_printf(ctx: ExecContext, statement: Tree) -> None:
    """
**Print formatted values, similar to AWK's printf statement**

* Printf _expression_ [, _expression_]... [;]
* Printf [Output | Error | Markdown] _expression_ [, _expression_]... [;]

If no expressions are given, nothing is printed.
Default destination is `Output`. `Markdown` always goes to the current console.
If the console is redirected to a file `Markdown` output written as text.

The first expression is resolved to a string used to format the other values.

Formatting syntax is that used in [Python's str.format()](https://docs.python.org/3/library/string.html#formatstrings)

Also see `Format()`

"""
    channel, args = _extract_args(statement)
    if args:
        format_string = ctx.eval_to_str(args[0], 'Format string', True)
        _CHANNEL_MAP[channel](poly_format(format_string, *tuple(ctx.eval_expr(expr) for expr in args[1:])), end='', flush=True)
