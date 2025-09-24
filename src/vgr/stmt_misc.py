"""
Other statements: SLEEP
"""

import time

from lark import Tree

from .exec_context import ExecContext
from .mathpak import bound_ops

@bound_ops("Sleep")
def execute_sleep(ctx: ExecContext, statement: Tree) -> None:
    """
**Sleep for a given number of seconds**

* Sleep [For] _expression_ [Second | Seconds] [;]

Values may be floating point, e.g. .01 to delay for ten milliseconds.
Negative and zero values are ignored. Maximum sleep time is five minutes.
"""
    n = ctx.eval_to_number(statement.children[0], 'Sleep time')
    n = min(max(n, 0), 300)
    if n > 0:
        ctx.print_verbose('Sleeping for', n, 'seconds')
        time.sleep(n)
    else:
        ctx.print_verbose('Sleep skipped')
