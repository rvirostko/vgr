"""
BASIC extension statements
"""

from lark import Tree

from ..app_exceptions import VgrStatementBreak, VgrStatementContinue, BlockType
from ..exec_context import ExecContext

from ..builtins import bound_ops

@bound_ops("Exit Block")
def execute_exit_for(_: ExecContext, statement: Tree) -> None:
    """
**Exits the current block of statements**

* Exit [For | While]

BASIC variants of `Break`.

The type following `Exit` must match the innermost loop.
If not, a runtime error is generated.

Also see `Break`
"""
    raise VgrStatementBreak(statement, BlockType.FOR_LOOP)

# Doc merged with For
def execute_exit_while(_: ExecContext, statement: Tree) -> None:
    raise VgrStatementBreak(statement, BlockType.WHILE_LOOP)

@bound_ops("Continue Block")
def execute_continue_for(_: ExecContext, statement: Tree) -> None:
    """
**Cause the current loop to to start again**

* Continue [For | While]

BASIC variants of `Continue`.

The type following `Continue` must match the innermost loop.
If not, a runtime error is generated.

Also see `Continue`
"""
    raise VgrStatementContinue(statement, BlockType.FOR_LOOP)

# Doc merged with For
def execute_continue_while(_: ExecContext, statement: Tree) -> None:
    raise VgrStatementContinue(statement, BlockType.WHILE_LOOP)
