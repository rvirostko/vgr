"""
COBOL statements
"""

from typing import Any

from lark import Tree

from ..evaluate import do_set, get_writable_var_path, _var_name_path
from ..exec_context import ExecContext
from ..builtins import (
    bound_ops,
    poly_repr,
)
from ..redir import print_stdout

@bound_ops("Move")
def execute_move_to(ctx: ExecContext, statement: Tree) -> None:
    """
**Assign a value to a variable**

* Move *expression* To *variable*
* Move Corresponding *expression* To *variable*
* Move Corr *expression* To *variable*

The first form is equivalent to `Set`.
The second and third forms work with dictionaries, copying attribute from the
evaluated *expression* to *variable*. If *variable* does not exist,
is `None` or not a dictionary, a regular move is performed.
If *expression* does not resolve to a dictionary, the corresponding
request is ignored and a regular move is performed.

```vgr
Move 5 To a
Move a + 2 To b
Exhibit a b
a = 5
b = 7

Move {"x": 1, "y": 2, "z": 3} To a
Move {"w": 5, "x": 10} To b
Move Corresponding b To a
Exhibit a
a.x = 10
a.y = 2
a.z = 3
```

Also see `Set` and `Add()` for combining dictionaries
"""
    corresponding = False
    start = 0
    fc = statement.children[0]
    if isinstance(fc, Tree) and fc.data == 'cobol_move_corr':
        corresponding = True
        start = 1
    src_value = ctx.eval_expr(statement.children[start])
    var_path = get_writable_var_path(ctx, statement.children[start + 1])
    dest_value = ctx.get_var(*var_path) if corresponding else None
    if isinstance(src_value, dict) and isinstance(dest_value, dict):
        # Should end up here if corresponding was specified,
        # what we are moving is a dictionary, and the
        # destination existed and is also a dictionary
        dest_value.update({k: src_value[k] for k in src_value if k in dest_value.keys()})
        # This isn't strictly needed as we've done a modification in place
        # However, it does print out something in verbose, so we execute
        # for that side effect
        do_set(ctx, dest_value, *var_path)
    else:
        # Either not corresponding move or the src/dest are not a dicts
        # Just a "regular" set
        do_set(ctx, src_value, *var_path)

@bound_ops("Exhibit")
def execute_exhibit(ctx: ExecContext, statement: Tree) -> None:
    """
**Display the names and values of variables**

* Exhibit *
* Exhibit *variable*&hellip;

`Exhibit` is not typically used in scripts, but is useful for debugging
and for working in the REPL.

The values are displayed on individual lines. If a variable has sub-values, each
portion is displayed on its own line.

With a single argument of *\\** all variables are displayed.

Unlike `Print` et al, the values display are the _representation_ of the data, not
its printable value. This lets you diferentiate between an integer and a string as
well as seeing control characters.

```vgr
Exhibit math.pi math.e
math.pi = 3.141592653589793
math.e = 2.718281828459045

Print math.float
{'max': 1.7976931348623157e+308, 'min': 2.2250738585072014e-308}
Exhibit math.float
math.float.max = 1.7976931348623157e+308
math.float.min = 2.2250738585072014e-308

Exhibit string.whitespace
string.whitespace = ' \\t\\n\\r\\x0b\\x0c'
```

Also see `Print`, `Printf`, and `Repr()`
"""
    def _exhibit_value(name: str, value: Any) -> None:
        if hasattr(value, 'keys') and callable(value.keys):
            keys = value.keys()
            if len(keys):
                for key in sorted(keys):
                    pkey = str(key)
                    _exhibit_value(name + '.' + pkey if len(name) > 0 else pkey, value[key])
            else:
                print_stdout(name, '= -empty-')
        else:
            print_stdout(name, '=', poly_repr(value))
    children = statement.children
    if children:
        for var_name in children:
            var_path = _var_name_path(var_name)
            exists, true_name, value = ctx.var_exists(*var_path)
            if exists:
                _exhibit_value(true_name, value)
            else:
                print_stdout(true_name, '= -not set-')
    else:
        # No arguments dumps the entire dictionary
        for key in sorted(ctx.dd.keys()):
            _exhibit_value(key, ctx.get_var(key))
