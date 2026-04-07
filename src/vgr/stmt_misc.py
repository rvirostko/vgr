"""
Other statements: SLEEP
"""

import time

from lark import Tree

from .builtins import (
    bound_ops,
    poly_plural,
)
from .exec_context import ExecContext

@bound_ops("Sleep")
def execute_sleep(ctx: ExecContext, statement: Tree) -> None:
    """
**Sleep for a given number of seconds**

* Sleep [For] *expression* [Second | Seconds] [;]

Sleep time is a number. Strings are converted to number if possible
Floating point values are allowed, e.g. .01 to delay for ten milliseconds.
`None`, negative, and zero values are ignored.

The maximum sleep time is 300 seconds or five minutes.

```vgr
Verbose
Verbose = True
Sleep None
Sleep skipped

Sleep Zero
Sleep skipped

Sleep 2
Sleeping for 2 seconds

Sleep 2.75
Sleeping for 2.75 seconds

Sleep For .01 Seconds
Sleeping for 10 ms

Sleep For 1/3 Seconds
Sleeping for 333.333 ms
```

"""
    def fmt(x: float) -> str:
        if x.is_integer(): return str(int(x))
        return f"{x:.3f}".rstrip("0").rstrip(".")
    n = ctx.eval_to_number(statement.children[0], 'Sleep time', True)
    if n is not None:
        n = min(max(n, 0), 300)
        if n > 0:
            if ctx.verbose:
                if n >= 1:
                    ctx.print_verbose('Sleeping for', fmt(n), poly_plural(n, 'seconds', 'second'))
                else:
                    ctx.print_verbose('Sleeping for', fmt(n * 1000), 'ms')
            time.sleep(n)
            return
    ctx.print_verbose('Sleep skipped')
