"""
Implementations of PRINT and PRINTF
"""

import os

from lark import Tree

from data_dict import DataDictionary
from dd_config import OFS_PATH, ORS_PATH
from redir import print_stdout, print_stderr, stdout
from evaluate import eval_expr, eval_to_str
from mathpak import poly_format

def execute_print(dd: DataDictionary, statement: Tree) -> None:
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
    sep = dd.get_var_user(*OFS_PATH)
    sep = ' ' if sep is None else str(sep)
    end = dd.get_var_user(*ORS_PATH)
    end = os.linesep if end is None else str(end)
    print_stdout(*[eval_expr(dd, expr) for expr in statement.children], sep=sep, end=end)
    stdout().flush()

def execute_printf(dd: DataDictionary, statement: Tree) -> None:
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
    format_string = eval_to_str(dd, statement.children[0], 'Format string', True)
    value = poly_format(format_string, *tuple(eval_expr(dd, expr) for expr in statement.children[1:]))
    if value:
        print_stdout(value, end='')
        stdout().flush()
    else:
        if dd.verbose: print_stderr('Nothing to print')
