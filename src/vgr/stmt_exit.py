"""
Contains the implementation for the EXIT statement
"""

import logging

from lark import Tree

from .app_exceptions import (
    VgrExitingException,
    VgrStatementAssert,
    VgrStatementReturn,
)
from .builtins import (
    bound_ops,
    poly_bool,
    poly_int,
    poly_not_empty,
    poly_true,
)
from .exec_context import ExecContext
from .redir import print_stderr
from .src_mgr import SSM

_LOG = logging.getLogger(__name__)

@bound_ops("Exit")
def execute_exit(ctx: ExecContext, statement: Tree) -> None:
    """
**Exits the script setting a return code**

* Exit
* Exit *expression*

The *expression* is a numeric the code returned to the operating system.
The default return code is zero.
Note that in this specific case `True` returns zero and `False` returns one.

```vgr
Exit → 0
Exit None → 0
Exit True → 0
Exit "true" → 0
Exit False → 1
Exit "False" → 1
Exit 5 → 5
Exit -5.1 → -5
Exit " 5 " → 5
```

Also see `Assert`, `ToBoolean()`, and `ToInteger()`
"""
    def bool_return(x) -> int: return VgrExitingException.EXIT_SUCCESS if poly_true(poly_bool(x)) else VgrExitingException.EXIT_FAILED
    # If no argument provided, then "success"
    rc = VgrExitingException.EXIT_SUCCESS
    if statement.children:
        x = ctx.eval_expr(statement.children[0])
        # Generally, None or python truthiness return "success"
        # If the value can be converted to an int, for example "5" then
        # that number is returned.
        if x is not None:
            if isinstance(x, bool):
                rc = bool_return(x)
            else:
                try:
                    rc = poly_int(x)
                except ValueError:
                    rc = bool_return(x)
    msg = f'Exiting with rc = {rc}'
    _LOG.info('%s(%s): %s', SSM.current[0], statement.meta.line, msg.strip())
    raise VgrExitingException(rc, statement, msg)

@bound_ops("Assert")
def execute_assert(ctx: ExecContext, statement: Tree) -> None:
    """
**Assert that a condition is met, halting execution if it is not**

* Assert *expression*
* Assert *expression* : *expression*[, *expression*]&hellip;

The first expression is evaluated as a boolean value which must be true for execution to continue.

The optional expressions following the colon compose a a string message printed if the first expression
is not `True`. It is composed in the same manner as `Printf`, with the first one being a string containing
formatting syntax as used by `Format()`.

If no message is given the the failing expression is used as the message

Execution ends with an exit code of 1 indicating failure

Also see `Exit` and `Format()`
"""
    exprs = statement.children
    v: bool = poly_true(ctx.eval_expr(exprs[0])) if len(exprs) else False
    if not v:
        msg: str = None
        if len(exprs) > 1:
            try:
                msg = ctx.eval_to_str(exprs[1], 'Format string', True)
                if poly_not_empty(msg):
                    msg = msg.format(*[ctx.eval_expr(expr) for expr in exprs[2:]])
            except (ValueError, TypeError) as e:
                print_stderr(f'While evaluating {SSM.source_for(statement)} on line {statement.meta.line}: ', e)
        msg = str(msg) if poly_not_empty(msg) else f'{SSM.source_for(statement)} failed'
        _LOG.warning('%s(%s): %s', SSM.current[0], statement.meta.line, msg.strip())
        # Point the "error" at the expression being tested
        raise VgrStatementAssert(exprs[0], msg)

@bound_ops("Return")
def execute_return(ctx: ExecContext, statement: Tree) -> None:
    """
**Return a value from a function**

* Return
* Return *expression*

If *expression* is not provided, or if a function does not contain a `Return`,
the return values is always `None`.

```vgr
Define Function NoReturn(x):
    NOP
End-Function

Define Function Sqrt(x):
    Return x·⁵
End-Function

Assert @NoReturn(5) Is None
Assert @Sqrt(16) Is 4
```

"""
    rc = ctx.eval_expr(statement.children[0]) if statement.children else None
    raise VgrStatementReturn(rc, statement)
