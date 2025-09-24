"""
BASIC extension statements
"""

from lark import Tree

from app_exceptions import VgrStatementBreak, VgrStatementContinue
from evaluate import get_writable_var_path
from exec_context import ExecContext
from stmt_exec import bind_operations, exec_loop
from stmt_set import execute_set
from tags import control_statement

from mathpak import bound_ops

@control_statement
@bound_ops("Do-While")
def execute_do_while(ctx: ExecContext, statement: Tree) -> None:
    """A BASIC-style Do-While Loop

* Do While _expression_
    _statement_...
  Loop [;]

As long as the expression evaluates to True, the block of statements is
repeatedly executed.
If a Break statement is encountered, looping ends regardless of the
expression's value. If a Continue statement is encountered, statements
following it are skipped, and the expression is checked again."""
    exec_loop(ctx, statement, True)

@control_statement
@bound_ops("Do-Until")
def execute_do_until(ctx: ExecContext, statement: Tree) -> None:
    """A BASIC-style Do-Until Loop

* Do Until _expression_
    _statement_...
  Loop [;]

The block of statements is executed until the expression evaluates to True.
If a Break statement is encountered, looping ends regardless of the
expression's value. If a Continue statement is encountered, statements
following it are skipped, and the expression is checked again.
"""
    exec_loop(ctx, statement, False)

@control_statement
@bound_ops("For-Next")
def execute_for_next(ctx: ExecContext, statement: Tree) -> None:
    """
**A BASIC-style For-Next Loop**

* For _variable_ = _expressions_ To _expression_ [:]
    _statement_...
  Next [;]
* For _variable_ = _expressions_ To _expression_ By _expression_ [:]
    _statement_...
  Next [;]

The block of statements is executed until the limit is exceeded.
If a _Break_ statement is encountered, looping ends regardless of the
limit's value. If a _Continue_ statement is encountered, statements
following it are skipped and looping proceeds.
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
        ctx.dd.push_frame([(var_path, None)])
        # NB: if start/end are the same, the loop executes once,
        #     which is typical for Basic implementations
        while (inc > 0 and value <= end) or (inc < 0 and value >= end):
            ctx.set_var(value, *var_path)
            try:
                ctx.dispatch_statements(statement.children[cindex:])
            except VgrStatementBreak:
                return
            except VgrStatementContinue:
                pass
            value += inc
    finally:
        ctx.dd.pop_frame()

@bound_ops("Exit-Block")
def execute_exit(_: ExecContext, statement: Tree) -> None:
    """
**Exits the current block of statements**

* Exit Do [;]
* Exit For [;]
* Exit While [;]

BASIC variants of _Break_.
Note that the scope portion of the command not respected; the _current_
block is exited without regards to type.
"""
    raise VgrStatementBreak(statement)

@bound_ops("Continue-Block")
def execute_continue(_: ExecContext, statement: Tree) -> None:
    """
**Causes the current loop to to start again**

* Continue Do [;]
* Continue For [;]
* Continue While [;]

BASIC variants of _Continue_.
Note that the scope portion of the command not respected; the _current_
block is restarted without regards to type.
"""
    raise VgrStatementContinue(statement)

@bound_ops("Let")
def execute_let(ctx: ExecContext, statement: Tree) -> None:
    """
**Assign a value to a variable**

* Let _variable_ = _expression_ [;]

BASIC equivalent of _Set_
"""
    execute_set(ctx, statement)

@control_statement # prevents echoing itself
@bound_ops("Troff")
def execute_troff(ctx: ExecContext, _: Tree) -> None:
    """
**Turn off Tracing Mode**

* Troff [;]

BASIC equivalent of _Echo False_
"""
    ctx.echo = False
    ctx.print_verbose('Trace Off')

@control_statement # prevents echoing itself
@bound_ops("Tron")
def execute_tron(ctx: ExecContext, _: Tree) -> None:
    """
**Turn on Tracing Mode**

* Tron [;]

BASIC equivalent of _Echo True_
"""
    ctx.echo = True
    ctx.print_verbose('Trace On')
