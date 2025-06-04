"""
BASIC extension statements
"""

from lark import Tree

from app_exceptions import StatementBreak, StatementContinue
from data_dict import DataDictionary
from redir import print_stderr
from stmt_exec import bind_operations, dispatch_statement, exec_loop
from stmt_set import execute_set
from tags import control_statement
from src_mgr import SSM
from dd_config import dd_path, do_set, do_unset
from evaluate import eval_to_number

@control_statement
def execute_do_while(dd: DataDictionary, statement: Tree) -> None:
    """A BASIC-style Do-While Loop

* Do While _expression_
    _statement_...
  Loop [;]

As long as the expression evaluates to True, the block of statements is
repeatedly executed.
If a Break statement is encountered, looping ends regardless of the
expression's value. If a Continue statement is encountered, statements
following it are skipped, and the expression is checked again."""
    exec_loop(dd, statement, True)

@control_statement
def execute_do_until(dd: DataDictionary, statement: Tree) -> None:
    """A BASIC-style Do-Until Loop

* Do Until _expression_
    _statement_...
  Loop [;]

The block of statements is executed until the expression evaluates to True.
If a Break statement is encountered, looping ends regardless of the
expression's value. If a Continue statement is encountered, statements
following it are skipped, and the expression is checked again.
"""
    exec_loop(dd, statement, False)

@control_statement
def execute_for_next(dd: DataDictionary, statement: Tree) -> None:
    """
**A BASIC-style For-Next Loop**

* For _varabile_ = _expressions_ To _expression_ [:]
    _statement_...
  Next [;]
* For _varabile_ = _expressions_ To _expression_ By _expression_ [:]
    _statement_...
  Next [;]

The block of statements is executed until the limit is exceeded.
If a _Break_ statement is encountered, looping ends regardless of the
limit's value. If a _Continue_ statement is encountered, statements
following it are skipped and looping proceeds.
"""
    # Echo the control portion, not the statements
    if dd.echo:
        print_stderr(SSM.source_for(statement, statement.children[-1]))
    cindex = 0
    path = dd_path(statement.children[cindex])
    cindex += 1
    value = eval_to_number(dd, bind_operations(statement.children[cindex]), 'For-Next start')
    cindex += 1
    end = eval_to_number(dd, bind_operations(statement.children[cindex]), 'For-Next end')
    cindex += 1
    inc = 1
    if statement.data == 'basic_for_next':
        inc = -1 if value > end else 1
    else:
        # This statement has a "by" clause
        inc = eval_to_number(dd, bind_operations(statement.children[cindex]), 'For-Next increment')
        if inc == 0: raise ValueError('For-Next increment must be non-zero')
        cindex += 1
    if (end - value) * inc < 0:
        # NB: if end and value are the same, we don't care about the sign
        raise ValueError('Sign of For-Next increment results in infinite loop')
    try:
        # NB: if start/end are the same, the loop executes once,
        #     which is typical for Basic implementations
        while (inc > 0 and value <= end) or (inc < 0 and value >= end):
            do_set(dd, value, *path)
            try:
                for s in statement.children[cindex:]: dispatch_statement(dd, s)
            except StatementBreak:
                return
            except StatementContinue:
                pass
            value += inc
    finally:
        do_unset(dd, *path)

def execute_exit(_: DataDictionary, __: Tree) -> None:
    """
**Exits the current block of statements**

* Exit Do [;]
* Exit For [;]
* Exit While [;]

BASIC variants of _Break_.
Note that the scope portion of the command not respected; the _current_
block is exited without regards to type.
"""
    raise StatementBreak()

def execute_continue(_: DataDictionary, __: Tree) -> None:
    """
**Causes the current loop to to start again**

* Continue Do [;]
* Continue For [;]
* Continue While [;]

BASIC variants of _Continue_.
Note that the scope portion of the command not respected; the _current_
block is restarted without regards to type.
"""
    raise StatementContinue()

def execute_let(dd: DataDictionary, statement: Tree) -> None:
    """
**Assign a value to a variable**

* Let _variable_ = _expression_ [;]

BASIC equivalent of _Set_
"""
    execute_set(dd, statement)

def execute_troff(dd: DataDictionary, _: Tree) -> None:
    """
**Turn off Tracing Mode**

* Troff [;]

BASIC equivalent of _Echo False_
"""
    dd.echo = False
    if dd.verbose: print_stderr('Trace Off')

def execute_tron(dd: DataDictionary, _: Tree) -> None:
    """
**Turn on Tracing Mode**

* Tron [;]

BASIC equivalent of _Echo True_
"""
    dd.echo = True
    if dd.verbose: print_stderr('Trace On')
