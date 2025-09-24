"""
Implementations of Print, PrintF, and MdPrint
"""

import os
import sys
from io import StringIO

from lark import Tree

from dd_config import OFS_PATH, ORS_PATH
from redir import print_stdout, print_stderr
from exec_context import ExecContext
from mathpak import poly_format, bound_ops
from doc_help import print_md

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

* Print _expression_ [, _expression_]... [;]
* Print [Output | Error | Markdown] _expression_ [, _expression_]... [;]

If no expressions are given, a new line is printed (see below).
Default destination is `Output`. `Markdown` always goes to the current console.

The results of the expressions are separated by the string defined in _arg.ofs_.
Lines are ended by with the _arg.ors_ string. The defaults are space and new line and
are used if the values are set to _None_.
If there are no expressions to print only the _arg.ors_ is printed.
"""
    channel, args = _extract_args(statement)
    if args:
        sep = ctx.get_var(*OFS_PATH)
        sep = ' ' if sep is None else str(sep)
        end = ctx.get_var(*ORS_PATH)
        end = os.linesep if end is None else str(end)
        _CHANNEL_MAP[channel](*[ctx.eval_expr(expr) for expr in args], sep=sep, end=end, flush=True)

@bound_ops("Printf")
def execute_printf(ctx: ExecContext, statement: Tree) -> None:
    """
**Print formatted values, similar to AWK's printf statement**

* Printf _expression_ [, _expression_]... [;]
* Printf [Output | Error | Markdown] _expression_ [, _expression_]... [;]

If no expressions are given, nothing is printed.
Default destination is `Output`. `Markdown` always goes to the current console.

The first expression is resolved to a string used to format the other values.

Formatting syntax is that used in [Python's str.format()](https://docs.python.org/3/library/string.html#formatstrings)

## Formatting Cheat Sheet

### Basic usage
```
Printf "Hello, {}", "world"     # "Hello, world"
Printf "{0} + {0} = {1}", 2, 4) # "2 + 2 = 4"
```

### Number formatting
```
Printf "{:d}", 42       # "42" (decimal)
Printf "{:b}", 42       # "101010" (binary)
Printf "{:x}", 42       # "2a" (hex, lowercase)
Printf "{:X}", 42       # "2A" (hex, uppercase)
Printf "{:o}", 42       # "52" (octal)
Printf "{:e}", 3.14     # "3.140000e+00" (scientific)
Printf "{:.2f}", 3.1415 # "3.14" (fixed-point, 2 decimals)
```

### Alignment & width
Printf "{:<10}", "hi"   # "hi        " (left align)
Printf "{:>10}", "hi"   # "        hi" (right align)
Printf "{:^10}", "hi"   # "    hi    " (center)
Printf "{:*^10}", "hi"  # "***hi*****" (custom fill)

### Signs & numbers
Printf "{:+d}", 42      # "+42"
Printf "{:+d}", -42     # "-42"
Printf "{: d}", 42      # " 42" (space for positive)
Printf "{:,}", 1234567  # "1,234,567" (thousands sep)
Printf "{:_}", 1234567  # "1_234_567" (underscore sep)

### Accessing elements
Set person To {"name": "Alice", "age": 25}
Printf "{0[name]} is {0[age]}", person # "Alice is 25"
Set p = {"x": 1, "y": 2}
Printf "({0.x}, {0.y})", p  # "(1, 2)"

## Reuse and nesting
Printf "{0} {0!r} {0!s}", "hi" # "hi 'hi' hi" (raw vs str formatting)
Printf "{0:.{1}f}", 3.14159, 2 # "3.14" (precision via argument)

"""
    channel, args = _extract_args(statement)
    if args:
        format_string = ctx.eval_to_str(args[0], 'Format string', True)
        _CHANNEL_MAP[channel](poly_format(format_string, *tuple(ctx.eval_expr(expr) for expr in args[1:])), end='', flush=True)
