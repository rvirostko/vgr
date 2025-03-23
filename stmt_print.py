
from typing import Any

from lark import Tree

from data_dict import DataDictionary
from dd_config import OFS_PATH, ORS_PATH
from redir import print_stdout
from evaluate import eval_expr, eval_to_str

def execute_print(dd: DataDictionary, statement: Tree) -> None:
    """Print values, similar to AWK's print statement

* PRINT [;]
* PRINT _expression_ [, _expression_]... [;]

If no expressions are given, a new line is printed (see below)

The results of the expressions are separated by the string defined in _arg.ofs_.
Lines are ended by with the _arg.ors_ string. The defaults are space and new line and
are used if the values are set to _None_.
"""
    print_stdout(*[eval_expr(dd, expr) for expr in statement.children],
                    sep=str(dd.get_var_user(*OFS_PATH) or ' '),
                    end=str(dd.get_var_user(*ORS_PATH) or '\n'))

def execute_printf(dd: DataDictionary, statement: Tree) -> None:
    """Print formatted values, similar to AWK's printf statement

* PRINTF [;]
* PRINTF _expression_ [, _expression_]... [;]

If no expressions are given, nothing is printed

The first expression is resolved to a string used to format the other values

Formatting syntax is that used in [Python's str.format()](https://docs.python.org/3/library/string.html#formatstrings)
"""
    exprs = [*statement.children]
    format_string = eval_to_str(dd, exprs.pop(0), 'Format string') if len(exprs) else ''
    print_stdout(str(format_string).format(*[eval_expr(dd, expr) for expr in exprs]), end='')

def execute_exhibit(dd: DataDictionary, statement: Tree) -> None:
    """The display the name and values of variables

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
            for key in sorted(value.keys()): exhibit_value(f'{name}.{key}', value[key])
        else:
            print_stdout(f'{name} = {repr(value)}')
    children = statement.children
    if children:
        for var_name in children:
            path = tuple(name.value for name in var_name.children)
            exhibit_value('.'.join(path), dd.get_var_user(*path))
    else:
        for key in sorted(dd.keys()): exhibit_value(key, dd.get_var(key))
