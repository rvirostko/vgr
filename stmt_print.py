"""
Implementations of PRINT, PRINTF, EXHIBIT, and DISPLAY
"""

from typing import Any

from lark import Tree

from data_dict import DataDictionary
from dd_config import OFS_PATH, ORS_PATH, LINESEP_PATH
from redir import print_stdout, print_stderr
from evaluate import eval_expr, eval_to_str
from mathpak import poly_format

def execute_print(dd: DataDictionary, statement: Tree) -> None:
    """Print values, similar to AWK's print statement

* PRINT [;]
* PRINT _expression_ [, _expression_]... [;]

If no expressions are given, a new line is printed (see below)

The results of the expressions are separated by the string defined in _arg.ofs_.
Lines are ended by with the _arg.ors_ string. The defaults are space and new line and
are used if the values are set to _None_.
"""
    sep = str(dd.get_var_user(*OFS_PATH))
    sep = ' ' if sep is None else sep
    end = str(dd.get_var_user(*ORS_PATH))
    end = dd.get_var_user(*LINESEP_PATH) if end is None else end
    print_stdout(*[eval_expr(dd, expr) for expr in statement.children], sep=sep, end=end)

def execute_printf(dd: DataDictionary, statement: Tree) -> None:
    """Print formatted values, similar to AWK's printf statement

* PRINTF [;]
* PRINTF _expression_ [, _expression_]... [;]

If no expressions are given, nothing is printed

The first expression is resolved to a string used to format the other values

Formatting syntax is that used in [Python's str.format()](https://docs.python.org/3/library/string.html#formatstrings)
"""
    if len(statement.children) < 1: return
    format_string = eval_to_str(dd, statement.children[0], 'Format string', True)
    value = poly_format(format_string, *tuple(eval_expr(dd, expr) for expr in statement.children[1:]))
    if value: print_stdout(value, end='')

def execute_exhibit(dd: DataDictionary, statement: Tree) -> None:
    """Display the name and values of variables

* EXHIBIT [;]
* EXHIBIT _variable_ [, _variable_]... [;]

The values are displayed on individual lines. If a variable has sub variables, each
portion is displayed on its own line.

Without arguments, all variables are displayed

Unlike PRINT and PRINTF, the values display are the _representation_ of the data, not
its printable value. This lets you diferentiate between an integer and a string, and
see control characters.
"""
    def exhibit_value(name: str, value: Any) -> None:
        if isinstance(value, dict):
            if value:
                for key in sorted(value.keys()):
                    exhibit_value(name + '.' + key, value[key])
            else:
                print_stdout(name, '= -empty-')
        else:
            print_stdout(name, '=', repr(value))
    children = statement.children
    if children:
        for var_name in children:
            ## TODO this needs to be a bit smarter: it needs to
            # diferentiate between getting a value that is None
            # and nothing being there
            path = tuple(name.value for name in var_name.children)
            exhibit_value('.'.join(path), dd.get_var_user(*path))
    else:
        for key in sorted(dd.keys()):
            exhibit_value(key, dd.get_var(key))

def execute_display_on(dd: DataDictionary, statement: Tree) -> None:
    """Print values to either the output (stdout) or error (stderr) streams.

* DISPLAY _expression_... [;]
* DISPLAY _expression_... ON OUTPUT [;]
* DISPLAY _expression_... ON ERROR [;]

The default is to print to the output stream.
While similar to PRINT, DISPLAY does not use _arg.ofs_ or _arg.ors_, always
separating values with a space and ending with a newline.
"""
    dest_stdout = True
    args = tuple()
    if statement.children:
        last_child = statement.children[-1]
        if isinstance(last_child, Tree) and last_child.data in ('stdout', 'stderr'):
            dest_stdout = last_child.data == 'stdout'
            args = tuple(eval_expr(dd, expr) for expr in statement.children[:-1])
        else:
            args = tuple(eval_expr(dd, expr) for expr in statement.children)
    end = str(dd.get_var_user(*LINESEP_PATH)) or '\n'
    if dest_stdout:
        print_stdout(*args, sep='', end=end)
    else:
        print_stderr(*args, sep='', end=end)
