"""
Implementations of PRINT and PRINTF
"""

import os

from lark import Tree

from dd_config import OFS_PATH, ORS_PATH
from redir import print_stdout, stdout
from exec_context import ExecContext
from mathpak import poly_format, bound_ops

@bound_ops("Print")
def execute_print(ctx: ExecContext, statement: Tree) -> None:
    """
**Print values, similar to AWK's print statement**

* Print ;
* Print _expression_ [, _expression_]... [;]

If no expressions are given, a new line is printed (see below)

The results of the expressions are separated by the string defined in _arg.ofs_.
Lines are ended by with the _arg.ors_ string. The defaults are space and new line and
are used if the values are set to _None_.
Note that a semi-colon is _required_ if there are no expressions to print.
In this case, only the _arg.orgs_ is printed.
"""
    sep = ctx.get_var_user(*OFS_PATH)
    sep = ' ' if sep is None else str(sep)
    end = ctx.get_var_user(*ORS_PATH)
    end = os.linesep if end is None else str(end)
    print_stdout(*[ctx.eval_expr(expr) for expr in statement.children], sep=sep, end=end)
    stdout().flush()

@bound_ops("Printf")
def execute_printf(ctx: ExecContext, statement: Tree) -> None:
    """
**Print formatted values, similar to AWK's printf statement**

* Printf ;
* Printf _expression_ [, _expression_]... [;]

If no expressions are given, nothing is printed, but any pending output is flushed.
Note that the semi-colon is required in this case.

The first expression is resolved to a string used to format the other values.

Formatting syntax is that used in [Python's str.format()](https://docs.python.org/3/library/string.html#formatstrings)
"""
    if len(statement.children) < 1: return
    format_string = ctx.eval_to_str(statement.children[0], 'Format string', True)
    value = poly_format(format_string, *tuple(ctx.eval_expr(expr) for expr in statement.children[1:]))
    if value:
        print_stdout(value, end='')
        stdout().flush()
    else:
        ctx.print_verbose('Nothing to print')
