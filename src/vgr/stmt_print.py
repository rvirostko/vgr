"""
Implementations of Print, PrintF, and MdPrint
"""

from io import StringIO
import os
import re
import sys

from lark import Tree

from .builtins import poly_format, bound_ops
from .dd_config import OFS_PATH, ORS_PATH
from .doc_help import print_md
from .exec_context import ExecContext
from .redir import print_stdout, print_stderr

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

* Print [Output | Error | Markdown] *expression* [, *expression*]&hellip; [;]

Default destination is `Output`. `Markdown` always goes to the current console.
If the console is redirected to a file `Markdown` output written as text.

The results of the expressions are separated by the string defined in *env.OFS*.
Lines are ended by with the *env.ORS* string. The defaults are space and new line and
are used if the values are set to `None`.
If there are no expressions to print only the *env.ORS* is printed.

```vgr
**TODO**
```

Also see `Printf`
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

* Printf *expression* [, *expression*]&hellip; [;]
* Printf [Output | Error | Markdown] *expression* [, *expression*]&hellip; [;]

If no expressions are given, nothing is printed.
Default destination is `Output`. `Markdown` always goes to the current console.
If the console is redirected to a file `Markdown` output written as text.

The first expression is resolved to a string used to format the other values.

Formatting syntax is that used by `Format()`.

```vgr
**TODO**
```

Also see `Print`, `Format()`, in addition to `Open` and `Close`

"""
    channel, args = _extract_args(statement)
    if args:
        format_string = ctx.eval_to_str(args[0], 'Format string', True)
        _CHANNEL_MAP[channel](poly_format(format_string, *list(_p_xform(ctx.eval_expr(expr)) for expr in args[1:])), end='', flush=True)

def _p_xform(arg):
    """Little hack to override this special case data type"""
    return arg.pattern if isinstance(arg, re.Pattern) else arg
