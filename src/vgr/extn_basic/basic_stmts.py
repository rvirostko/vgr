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

@control_statement
@bound_ops("For Next")
def execute_for_next(ctx: ExecContext, statement: Tree) -> None:
    """
**A BASIC-style For-Next Loop**

* For *variable* = *expression* To *expression* [:]\\
  &emsp;&emsp;*statement*&hellip;\\
  Next
* For *variable* = *expression* To *expression* Step *expression* [:]\\
  &emsp;&emsp;*statement*&hellip;\\
  Next

The block of statements is executed until the limit is exceeded.
If `Break` is encountered, looping ends regardless of the
limit's value. If `Continue` is encountered, statements
following it are skipped and looping proceeds.

Statements have access to the *$loop* variable, including *index*, *length*, *first*, and *last*.

```vgr
For x = 2.0 To 4.0 Step .5
    Print x, $loop
Next

2.0 {'index': 0, 'first': True, 'last': False, 'length': 5}
2.5 {'index': 1, 'first': False, 'last': False, 'length': 5}
3.0 {'index': 2, 'first': False, 'last': False, 'length': 5}
3.5 {'index': 3, 'first': False, 'last': False, 'length': 5}
4.0 {'index': 4, 'first': False, 'last': True, 'length': 5}
```

Also see `Perform Varying` and `For-Each`.
"""
    def _err(value: Any, name: str) -> str: return ValueError(f"Can't use {str(value).title()} for {name}")
    def _nbr(expr: Tree, name: str) -> Any:
        value = ctx.eval_to_number(bind_operations(expr), name, True)
        if value is None or math.isinf(value) or math.isnan(value):
            raise VgrRuntimeError(expr, _err(value, name))
        return value
    # Echo the control portion, not the statements
    ctx.echo_source(statement, statement.children[-1])
    cindex = 0
    var_path = get_writable_var_path(ctx, statement.children[cindex])
    cindex += 1
    value = _nbr(statement.children[cindex], 'For-Next start')
    cindex += 1
    end = _nbr(statement.children[cindex], 'For-Next end')
    cindex += 1
    inc = 1
    if statement.data == 'basic_for_next_by':
        # This statement has a "step" clause
        name = 'For-Next increment'
        step_expr = statement.children[cindex]
        inc = _nbr(step_expr, name)
        if inc == 0: raise VgrRuntimeError(step_expr, _err(inc, name))
        cindex += 1
    try:
        meta = { }
        ctx.dd.push_frame([(var_path, None), (LOOP_META_PATH, meta)])
        # NB: if start/end are the same, the loop executes once,
        #     which is typical for Basic implementations
        length = int(max(0, math.floor((end - value) / inc) + 1))
        i = 0
        while (inc > 0 and value <= end) or (inc < 0 and value >= end):
            set_loop_meta(meta, i, length)
            ctx.set_var(value, *var_path)
            try:
                ctx.dispatch_statements(statement.children[cindex:])
            except VgrStatementBreak as e:
                # Can be either a Break or Exit For
                e.validate_for_block(BlockType.FOR_LOOP)
                return
            except VgrStatementContinue as e:
                # Can be either a Continue or Continue For
                e.validate_for_block(BlockType.FOR_LOOP)
            value += inc
            i += 1
    finally:
        ctx.dd.pop_frame()

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
