
from typing import Any

from lark import Tree

from app_exceptions import ExitingException
from data_dict import DataDictionary
from evaluate import eval_expr, eval_to_str
from mathpak import poly_bool, poly_int
from redir import print_stderr
from src_mgr import SSM

def execute_exit(dd: DataDictionary, statement: Tree) -> None:
    """Terminate execution

* EXIT [;]
* EXIT _expression_ [;]

The _expression_ is a numeric the code returned to the shell.
The default return code is zero.
Note that in this specific case "True" returns zero and "False" returns one.
"""
    rc: int = ExitingException.EXIT_SUCCESS
    if statement.children:
        x: Any = eval_expr(dd, statement.children[0])
        if x is not None:
            try:
                rc = poly_int(x)
            except ValueError:
                rc = ExitingException.EXIT_SUCCESS if poly_bool(x) else ExitingException.EXIT_FAILED
    raise ExitingException(rc, statement, '')

def execute_assert(dd: DataDictionary, statement: Tree) -> None:
    """Assert that a condition is met, terminating execution if it is not

* ASSERT _expression_ [;]
* ASSERT _expression_ : _expression_ [, _expression]... [;]

The first expression is evaluated as a boolean value which must be true for execution to continue.

The optional expressions following the colon compose a a string message printed if the first expression
is not true. It is composed in the same manner as Printf, with the first one being a string containing
formatting syntax as used in [Python's str.format()](https://docs.python.org/3/library/string.html#formatstrings)

If no message is given the the failing expression is used as the message

Execution ends with an exit code of 1 indicating failure
"""
    exprs = [*statement.children]
    v: bool = poly_bool(eval_expr(dd, exprs.pop(0))) if len(exprs) else False
    if not v:
        msg: str = None
        if len(exprs) > 0:
            try:
                msg = eval_to_str(dd, exprs.pop(0), 'Format string')
                if msg is not None: msg = msg.format(*[eval_expr(dd, expr) for expr in exprs])
            except (ValueError, TypeError) as e:
                print_stderr(f'While evaluating {SSM.source_for(statement)} on line {statement.meta.line}: ', e)
                msg = None
        raise ExitingException(ExitingException.EXIT_FAILED, statement,
                               str(msg) if msg is not None else f'{SSM.source_for(statement)} failed')

