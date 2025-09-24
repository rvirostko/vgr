"""
Contains the implementation for the EXIT statement
"""

import logging

from lark import Tree

from app_exceptions import (
    VgrExitingException,
    VgrStatementAssert,
    VgrStatementReturn,
)
from exec_context import ExecContext
from mathpak import (
    bound_ops,
    poly_int,
    poly_notempty,
    poly_true,
)
from redir import print_stderr
from src_mgr import SSM

_LOG = logging.getLogger(__name__)

@bound_ops("Exit")
def execute_exit(ctx: ExecContext, statement: Tree) -> None:
    """
**Exits the script setting a return code**

* Exit [;]
* Exit _expression_ [;]

The _expression_ is a numeric the code returned to the operating system.
The default return code is zero.
Note that in this specific case "True" returns zero and "False" returns one.
"""
    rc = VgrExitingException.EXIT_SUCCESS
    msg = 'Exiting'
    if statement.children:
        x = ctx.eval_expr(statement.children[0])
        if x is not None:
            try:
                rc = poly_int(x)
            except ValueError:
                rc = VgrExitingException.EXIT_SUCCESS if poly_true(x) else VgrExitingException.EXIT_FAILED
            msg = f'Exiting with rc = {rc}'
    _LOG.info('%s', msg)
    raise VgrExitingException(rc, statement, msg)

@bound_ops("Assert")
def execute_assert(ctx: ExecContext, statement: Tree) -> None:
    """
**Assert that a condition is met, halting execution if it is not**

* Assert _expression_ [;]
* Assert _expression_ : _expression_ [, _expression_]... [;]

The first expression is evaluated as a boolean value which must be true for execution to continue.

The optional expressions following the colon compose a a string message printed if the first expression
is not true. It is composed in the same manner as Printf, with the first one being a string containing
formatting syntax as used in [Python's str.format()](https://docs.python.org/3/library/string.html#formatstrings)

If no message is given the the failing expression is used as the message

Execution ends with an exit code of 1 indicating failure
"""
    exprs = statement.children
    v: bool = poly_true(ctx.eval_expr(exprs[0])) if len(exprs) else False
    if not v:
        msg: str = None
        if len(exprs) > 1:
            try:
                msg = ctx.eval_to_str(exprs[1], 'Format string', True)
                if poly_notempty(msg):
                    msg = msg.format(*[ctx.eval_expr(expr) for expr in exprs[2:]])
            except (ValueError, TypeError) as e:
                print_stderr(f'While evaluating {SSM.source_for(statement)} on line {statement.meta.line}: ', e)
        msg = str(msg) if poly_notempty(msg) else f'{SSM.source_for(statement)} failed'
        _LOG.warning('%s', msg)
        # Point the "error" at the expression being tested
        raise VgrStatementAssert(exprs[0], msg)

@bound_ops("Return")
def execute_return(ctx: ExecContext, statement: Tree) -> None:
    """
**Return a value from a function or exit a procedure**

* Return [;]
* Return _expression_ [;]

"""
    rc = ctx.eval_expr(statement.children[0]) if statement.children else None
    raise VgrStatementReturn(rc, statement)
