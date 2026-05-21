"""
Implementations of Print, PrintF, and MdPrint
"""

from io import StringIO
import os
import sys

from lark import Tree

from .app_exceptions import VgrRuntimeError
from .builtins import (
    bound_ops,
    poly_bool,
    poly_format,
    poly_str,
)
from .dd_config import OFS_PATH, ORS_PATH
from .doc_help import md_println
from .exec_context import ExecContext
from .redir import print_stdout, print_stderr

def _print_md(*args, **kwargs):
    if sys.stdout.isatty():
        print(*args,
              file=(buf := StringIO()),
              sep=kwargs.get('sep', ' '),
              end=kwargs.get('end', os.linesep),
              flush=True)
        if (s := buf.getvalue()): md_println(s)
    else:
        print_stdout(*args, **kwargs)

_CHANNEL_MAP = {
    'stderr':   print_stderr,
    'stdout':   print_stdout,
    'markdown': _print_md,
}

@bound_ops("Print")
def execute_print(ctx: ExecContext, statement: Tree) -> None:
    """
**Print a series of values**

* Print *expression* [, *expression*]&hellip; [*options*&hellip;]
* Print *expression* [, *expression*]&hellip; To [Output | Error] [*options*&hellip;]
* Print *expression* [, *expression*]&hellip; As Markdown [*options*&hellip;]

Default destination is `Output`. `Markdown` always goes to the current console.
If the console is redirected to a file `Markdown` output is written as text.

The results of the expressions are separated by the string defined in *env.OFS*.
Lines are ended by with the *env.ORS* string. The defaults are `Space` and `Newline` and
are used if the environment values are set to `None`.

Even if the expressions evaluate to an empty string or `None`, the *env.ORS* is printed.

***Options***

* OFS [Is] *expression* : override the *env.OFS* default value
* ORS [Is] *expression* : override the *env.ORS* default value
* Field Separator [Is] *expression* : long form of `OFS`
* Record Separator [Is] *expression* : long form of `ORS`
* Flush [Is *expression*] : flush output immediately.
  Flushing output is the default.
  Without an argument, flushing is set to `True`
* No-Flush [Is *expression*] : negation of `Flush`.
  Whithout an argument, flushing is set to `False`.

```vgr
Print None, True, False, 1, 1.0, [2, 4, 8], {"a": "alpha", "b": "beta"}
 → "None True False 1 1.0 [2, 4, 8] {'a': 'alpha', 'b': 'beta'}"

Print "alpha"
Print "alpha" To Output
Print "*beta*" As Markdown

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
    def _get_sep(name: list, default: str):
        exists, _true_name, value = ctx.var_exists(*name)
        return value if exists and value is not None else default
    def _to_str(v) -> str:
        return '' if v is None else poly_str(v)
    values = []
    channel = 'stdout'
    ofs = _get_sep(OFS_PATH, ' ')
    ors = _get_sep(ORS_PATH, os.linesep)
    flush = True
    for child in statement.children:
        if isinstance(child, Tree):
            name = child.data
            if name in ['stdout','stderr', 'markdown']:
                channel = child.data
            elif name in ['flush', 'no_flush']:
                flush = _get_flush(ctx, child)
            elif name == 'ors':
                ors = ctx.eval_expr(child.children[0])
            elif name == 'ofs':
                ofs = ctx.eval_expr(child.children[0])
            else:
                values.append(ctx.eval_expr(child))
        else: # it is a Token, likely a const
            values.append(ctx.eval_expr(child))
    _CHANNEL_MAP[channel](*values, # NB: don't use poly_str() here!
                          sep=_to_str(ofs),
                          end=_to_str(ors),
                          flush=True if flush is None else flush)

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
    values = []
    channel = 'stdout'
    flush = True
    format_string_exp = statement.children[0]
    format_string = ctx.eval_to_str(format_string_exp, 'Format string', True)
    for child in statement.children[1:]:
        if isinstance(child, Tree):
            name = child.data
            if name in ['stdout','stderr', 'markdown']:
                channel = child.data
            elif name in ['flush', 'no_flush']:
                flush = _get_flush(ctx, child)
            else:
                values.append(ctx.eval_expr(child))
        else: # it is a Token, likely a const
            values.append(ctx.eval_expr(child))
    value = None
    try:
        value = poly_format('' if format_string is None else format_string, *values)
    except (ValueError, TypeError) as e:
        raise VgrRuntimeError(format_string_exp, e) from e
    _CHANNEL_MAP[channel](value,
                          sep='', end='',
                          flush=True if flush is None else flush)

def _get_flush(ctx: ExecContext, child: True) -> bool:
    name:str = child.data
    value = ctx.eval_to_bool(child.children[0],
                             name.replace('_', ' ').title(),
                             True) if child.children else True
    if value is None: return None
    return value if name == 'flush' else not value
