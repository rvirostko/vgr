"""
BASIC extension statements
"""

import math

from lark import Tree

from ..app_exceptions import VgrStatementBreak, VgrStatementContinue
from ..evaluate import get_writable_var_path
from ..exec_context import ExecContext
from ..stmt_exec import bind_operations, exec_loop, LOOP_META_PATH, set_loop_meta
from ..stmt_set import execute_set
from ..tags import control_statement

from ..mathpak import bound_ops

@control_statement
@bound_ops("Do While")
def execute_do_while(ctx: ExecContext, statement: Tree) -> None:
    """A BASIC-style Do-While Loop

* Do While *expression*\\
  &emsp;&emsp;_statement_&hellip;\\
  Loop [;]

As long as the expression evaluates to `True`, the block of statements is
repeatedly executed.
If a `Break` is encountered, looping ends regardless of the
expression's value. If a `Continue` is encountered, statements
following it are skipped, and the expression is checked again.

```vgr
**TODO**
```

"""
    exec_loop(ctx, statement, True)

@control_statement
@bound_ops("Do Until")
def execute_do_until(ctx: ExecContext, statement: Tree) -> None:
    """A BASIC-style Do-Until Loop

* Do Until *expression*\\
  &emsp;&emsp;_statement_&hellip;\\
  Loop [;]

The block of statements is executed until the expression evaluates to `True`.
If a `Break` is encountered, looping ends regardless of the
expression's value. If a `Continue` is encountered, statements
following it are skipped, and the expression is checked again.

```vgr
**TODO**
```

"""
    exec_loop(ctx, statement, False)

@control_statement
@bound_ops("For Next")
def execute_for_next(ctx: ExecContext, statement: Tree) -> None:
    """
**A BASIC-style For-Next Loop**

* For *variable* = *expression* To *expression* [:]\\
  &emsp;&emsp;*statement*&hellip;\\
  Next [;]
* For *variable* = *expression* To *expression* By *expression* [:]\\
  &emsp;&emsp;*statement*&hellip;\\
  Next [;]

The block of statements is executed until the limit is exceeded.
If `Break` is encountered, looping ends regardless of the
limit's value. If `Continue` is encountered, statements
following it are skipped and looping proceeds.

Statements have access to the *$loop* variable, including *index*, *length*, _first_, and _last_.

```vgr
For x = 2.0 To 4.0 By .5
    Print x, $loop
Next

2.0 {'index': 0, 'first': True, 'last': False, 'length': 5}
2.5 {'index': 1, 'first': False, 'last': False, 'length': 5}
3.0 {'index': 2, 'first': False, 'last': False, 'length': 5}
3.5 {'index': 3, 'first': False, 'last': False, 'length': 5}
4.0 {'index': 4, 'first': False, 'last': True, 'length': 5}
```
"""
    # Echo the control portion, not the statements
    ctx.echo_source(statement, statement.children[-1])
    cindex = 0
    var_path = get_writable_var_path(ctx, statement.children[cindex])
    cindex += 1
    value = ctx.eval_to_number(bind_operations(statement.children[cindex]), 'For-Next start')
    cindex += 1
    end = ctx.eval_to_number(bind_operations(statement.children[cindex]), 'For-Next end')
    cindex += 1
    inc = 1
    if statement.data == 'basic_for_next':
        inc = -1 if value > end else 1
    else:
        # This statement has a "by" clause
        inc = ctx.eval_to_number(bind_operations(statement.children[cindex]), 'For-Next increment')
        if inc == 0: raise ValueError('For-Next increment must be non-zero')
        cindex += 1
    if (end - value) * inc < 0:
        # NB: if end and value are the same, we don't care about the sign
        raise ValueError('Sign of For-Next increment results in infinite loop')
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
            except VgrStatementBreak:
                return
            except VgrStatementContinue:
                pass
            value += inc
            i += 1
    finally:
        ctx.dd.pop_frame()

@bound_ops("Exit Block")
def execute_exit(_: ExecContext, statement: Tree) -> None:
    """
**Exits the current block of statements**

* Exit Do [;]
* Exit For [;]
* Exit While [;]

BASIC variants of `Break`.

Note that the scope portion of the statement is not respected; the current
block is exited without regards to type.

```vgr
**TODO**
```

"""
    raise VgrStatementBreak(statement)

@bound_ops("Continue Block")
def execute_continue(_: ExecContext, statement: Tree) -> None:
    """
**Cause the current loop to to start again**

* Continue Do [;]
* Continue For [;]
* Continue While [;]

BASIC variants of `Continue`.

Note that the scope portion of the statement is not respected; the current
block is restarted without regards to type.

```vgr
**TODO**
```

"""
    raise VgrStatementContinue(statement)

@bound_ops("Let")
def execute_let(ctx: ExecContext, statement: Tree) -> None:
    """
**Assign a value to a variable**

* Let *variable* = *expression* [;]

BASIC equivalent of `Set`

```vgr
Let X = 5
Let Y = 7
Let RESULT = X * Y
Print RESULT
```

Also see `Set`
"""
    execute_set(ctx, statement)

@control_statement # prevents echoing itself
@bound_ops("Troff")
def execute_troff(ctx: ExecContext, _: Tree) -> None:
    """
**Turn off Tracing Mode**

* Troff [;]

BASIC equivalent of `Echo False`

```vgr
**TODO**
```

Also see `Echo`
"""
    ctx.echo = False
    ctx.print_verbose('Trace Off')

@control_statement # prevents echoing itself
@bound_ops("Tron")
def execute_tron(ctx: ExecContext, _: Tree) -> None:
    """
**Turn on Tracing Mode**

* Tron [;]

BASIC equivalent of `Echo True`

```vgr
**TODO**
```

Also see `Echo`
"""
    ctx.echo = True
    ctx.print_verbose('Trace On')
