"""
Implementations of Print, PrintF, and MdPrint
"""

from io import StringIO
import os
import sys

from lark import Tree

from .app_exceptions import VgrRuntimeError
from .builtins import poly_format, bound_ops
from .dd_config import OFS_PATH, ORS_PATH
from .doc_help import print_md
from .exec_context import ExecContext
from .redir import print_stdout, print_stderr

def _extract_args(tree: Tree) -> tuple:
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

* Print *expression* [, *expression*]&hellip;
* Print [On | To] [Output | Error] *expression* [, *expression*]&hellip;
* Print [As] Markdown *expression* [, *expression*]&hellip;

Default destination is `Output`. `Markdown` always goes to the current console.
If the console is redirected to a file `Markdown` output is written as text.

The results of the expressions are separated by the string defined in *env.OFS*.
Lines are ended by with the *env.ORS* string. The defaults are `Space` and `Newline` and
are used if the values are set to `None`.

Even if the expressions evaluate to an empty string, the *env.ORS* is printed.

```vgr
Print None, True, False, 1, 1.0, [2, 4, 8], {"a": "alpha", "b": "beta"}
 → "None True False 1 1.0 [2, 4, 8] {'a': 'alpha', 'b': 'beta'}"

Print "alpha"
Print Output "alpha"
Print To Output "alpha"
Print On Output "alpha"

Print Markdown "*beta*"
Print As Markdown "*beta*"

Exhibit env.OFS, env.ORS
env.OFS = " "
env.ORS = "\\n"
Print "alpha", "beta", "gamma" → "alpha beta gamma"

Set env.OFS = " | "
Set env.ORS = " |" + Newline
Exhibit env.OFS, env.ORS
env.OFS = " | "
env.ORS = " |\\n"
Print "alpha", "beta", "gamma" → "alpha | beta | gamma |\\n"
```

Also see `Printf`, `Open`, and `Close`
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

* Printf *expression* [, *expression*]&hellip;
* Printf [On | To] [Output | Error] *expression* [, *expression*]&hellip;
* Printf [As] Markdown *expression* [, *expression*]&hellip;

Default destination is `Output`. `Markdown` always goes to the current console.
If the console is redirected to a file `Markdown` output written as text.

By default, no `Newline` is printed at the end of the statement. If you require
a `Newline` include a *\\n* in your format string.

The first expression is resolved to a string and used to format the other values.
The formatting syntax is that used by `Format()`.

```vgr
# Empty format string
Printf "" → ""
Printf None, 1, 2 → "None"

# Basic formatted output (no newline unless explicitly included)
Printf "Hello {}", "world" → "Hello world"
Printf "Hello {}\\n", "world" → "Hello world\\n"
Printf "Value: {}\\n", 42 → "Value: 42\\n"
Printf "Float: {:.2f}\\n", 3.14159 → "Float: 3.14\\n"

# Indexed fields
Printf "{} {} {}\\n", "alpha", "beta", "gamma" → "alpha beta gamma\\n"
Printf "{1} then {0}\\n", "second", "first" → "first then second\\n"
# Dictionary property formatting
Set alice_info To {"name": "Alice", "height": 10}
Printf "{0[name]} is {0[height]} feet tall\\n", alice_info → "Alice is 10 feet tall\\n"

# Extra args ignored
Printf "{1} then {0}\\n", "second", "first", "ignored" → "first then second\\n"
# Mising args are None
Printf "{1}, {0}, then {2}\\n", "second", "first" → "first, second, then None\\n"

# Explicit destinations
Printf On Output "Out: {}\\n", "value"
Printf To Error "Error: {} ({})\\n", "failure", 1
Printf As Markdown "# {}\\n", "Header"
```

Also see `Print`, `Format()`, in addition to `Open` and `Close`
"""
    channel, args = _extract_args(statement)
    format_string = ctx.eval_to_str(args[0], 'Format string', True)
    try:
        _CHANNEL_MAP[channel](poly_format(format_string, *list(ctx.eval_expr(expr) for expr in args[1:])), end='', flush=True)
    except (ValueError, TypeError) as e:
        raise VgrRuntimeError(args[0], e) from e
