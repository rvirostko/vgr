"""
BASIC extension statements
"""

from typing import Any
import math

from lark import Tree

from ..app_exceptions import VgrRuntimeError, VgrStatementBreak, VgrStatementContinue, BlockType
from ..evaluate import get_writable_var_path
from ..exec_context import ExecContext
from ..stmt_exec import bind_operations, exec_loop, LOOP_META_PATH, set_loop_meta
from ..tags import control_statement

from ..builtins import bound_ops

@control_statement
@bound_ops("Do While")
def execute_do_while(ctx: ExecContext, statement: Tree) -> None:
    """A BASIC-style Do-While Loop

* Do While *expression*\\
  &emsp;&emsp;*statement*&hellip;\\
  Loop

As long as the expression evaluates to `True`, the block of statements is
repeatedly executed.
If a `Break` is encountered, looping ends regardless of the
expression's value. If a `Continue` is encountered, statements
following it are skipped, and the expression is checked again.

```vgr
words = ["apple", "banana", "cherry", None]
index = 0
Do While words.Item(index)
    # NB: $loop is available, but only index and first values
    word = words.Item(index)
    reversed_word = Reverse(word)
    Print "Original:", word, "\\nReversed:", reversed_word
    index += 1
Loop
```

Also see `Do Until`, `Continue`, and `Break`
"""
    # Allow Exit/Continue Do and Exit/Continue While in addition to the default Break/Continue
    exec_loop(ctx, statement, True, (BlockType.DO_LOOP, BlockType.WHILE_LOOP))

@control_statement
@bound_ops("Do Until")
def execute_do_until(ctx: ExecContext, statement: Tree) -> None:
    """A BASIC-style Do-Until Loop

* Do Until *expression*\\
  &emsp;&emsp;*statement*&hellip;\\
  Loop

The block of statements is executed until the expression evaluates to `True`.
If a `Break` is encountered, looping ends regardless of the
expression's value. If a `Continue` is encountered, statements
following it are skipped, and the expression is checked again.

```vgr
# Collect characters from input until a vowel is found
input_str = "bcdfghjklmnpqrustvwxyz"
collected = ""
index = 0
Do Until Lower(SubStr(input_str, index)) Is In "aeiou"
    # NB: $loop is available, but only index and first values
    collected += SubStr(input_str, index)
    index += 1
Loop
Print "Input:", Repr(input_str), "\\nBefore vowel:", Repr(collected)
```

Also see `Do While`, `Continue`, and `Break`
"""
    # Allow Exit/Continue Do in addition to the default Break/Continue
    exec_loop(ctx, statement, False, BlockType.DO_LOOP)


@bound_ops("Exit Block")
def execute_exit_do(_: ExecContext, statement: Tree) -> None:
    """
**Exits the current block of statements**

* Exit [Do | For | While]

BASIC variants of `Break`.

The type following `Exit` must match the innermost loop.
If not, a runtime error is generated.

Also see `Break`
"""
    raise VgrStatementBreak(statement, BlockType.DO_LOOP)

# Doc merged with Do
def execute_exit_for(_: ExecContext, statement: Tree) -> None:
    raise VgrStatementBreak(statement, BlockType.FOR_LOOP)

# Doc merged with Do
def execute_exit_while(_: ExecContext, statement: Tree) -> None:
    raise VgrStatementBreak(statement, BlockType.WHILE_LOOP)

@bound_ops("Continue Block")
def execute_continue_do(_: ExecContext, statement: Tree) -> None:
    """
**Cause the current loop to to start again**

* Continue [Do | For | While]

BASIC variants of `Continue`.

The type following `Continue` must match the innermost loop.
If not, a runtime error is generated.

Also see `Continue`
"""
    raise VgrStatementContinue(statement, BlockType.DO_LOOP)

# Doc merged with Do
def execute_continue_for(_: ExecContext, statement: Tree) -> None:
    raise VgrStatementContinue(statement, BlockType.FOR_LOOP)

# Doc merged with Do
def execute_continue_while(_: ExecContext, statement: Tree) -> None:
    raise VgrStatementContinue(statement, BlockType.WHILE_LOOP)
