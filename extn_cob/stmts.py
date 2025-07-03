"""
COBOL statements
"""

from datetime import datetime
from typing import Any
import sys

from lark import Tree, Token

from app_exceptions import VgrExitingException, VgrStatementBreak, VgrStatementContinue, VgrRuntimeError
from data_dict import DataDictionary
from dd_config import do_set, do_assignment, do_unset
from evaluate import eval_expr, bind_operations, eval_to_number, var_name_path
from mathpak import poly_add, poly_bool, poly_sub, poly_number, poly_mul, poly_div
from redir import print_stderr, print_stdout
from src_mgr import SSM
from stmt_exec import exec_if_else, exec_loop, exec_repeat, dispatch_statement
from stmt_set import execute_set
from tags import control_statement

def execute_accept_date(dd: DataDictionary, statement: Tree) -> None:
    # TODO
    do_set(dd, datetime.now().strftime('%y%m%d'), *var_name_path(statement.children[0]))

def execute_accept_yyyymmdd(dd: DataDictionary, statement: Tree) -> None:
    # TODO
    do_set(dd, datetime.now().strftime('%Y%m%d'), *var_name_path(statement.children[0]))

def execute_accept_day(dd: DataDictionary, statement: Tree) -> None:
    # TODO
    do_set(dd, datetime.now().strftime('%y%j'), *var_name_path(statement.children[0]))

def execute_accept_yyyyddd(dd: DataDictionary, statement: Tree) -> None:
    # TODO
    do_set(dd, datetime.now().strftime('%Y%j'), *var_name_path(statement.children[0]))

def execute_accept_dow(dd: DataDictionary, statement: Tree) -> None:
    # TODO
    do_set(dd, datetime.now().weekday() + 1, *var_name_path(statement.children[0]))

def execute_accept_time(dd: DataDictionary, statement: Tree) -> None:
    # TODO
    now = datetime.now()
    do_set(dd, now.strftime('%H%M%S') + f'{now.microsecond // 10000:02d}', *var_name_path(statement.children[0]))

def execute_accept_epoch(dd: DataDictionary, statement: Tree) -> None:
    # TODO
    do_set(dd, int(datetime.now().timestamp()), *var_name_path(statement.children[0]))

def execute_accept_input(dd: DataDictionary, statement: Tree) -> None:
    """
**Accept user input**

* Accept _variable_ From [Console | Stdin | Sysin | Sysinp] [;]

At end-of-file (when not interactive) or if the user hits return
without entering any information, the contents of _variable_ remains
unchanged.

There is no limit on the length of input, but input is read per-line.
"""
    line = sys.stdin.readline()
    if line: line = line.rstrip('\n')
    if line: do_set(dd, line, *var_name_path(statement.children[0]))

def execute_exit(_: DataDictionary, statement: Tree) -> None:
    """Terminate execution

* Stop Run [;]

Ends the program with an exit code of zero.
"""
    raise VgrExitingException(VgrExitingException.EXIT_SUCCESS, statement, '')

@control_statement
def execute_perform_until(dd: DataDictionary, statement: Tree) -> None:
    """Repeatedly execute a block of statements until a condition is reached.

* Perform Until _expression_
    _statement_...
  End-Perform [;]

The block of statements is executed until the expression evaluates to True.
If a Break or Next Sentence statement is encountered, looping ends regardless of the
expression's value. If a Continue statement is encountered, statements
following it are skipped, and the expression is checked again.
"""
    exec_loop(dd, statement, False)

@control_statement
def execute_perform_times(dd: DataDictionary, statement: Tree) -> None:
    """Execute a block of statements a fixed number of times.

* Perform _expression_ Times
    _statement_...
  End-Perform [;]

The block of statements is executed the given number of times.
The expression is evaluated an converted to an integer, rounding down.
For any statements to execute, the value must be greater than or equal to one.
If a Break or Next Sentence statement is encountered, looping ends regardless of the
expression's value. If a Continue statement is encountered, statements
following it are skipped, and looping continues.
"""
    exec_repeat(dd, statement)

@control_statement
def execute_perform_varying(dd: DataDictionary, statement: Tree) -> None:
    """Execute a block of statements while increasing or decreasing a variable's value.

* Perform Varying _variable_ From _expression_ By _expressions_ Until _expression_
    _statement_...
  End-Perform [;]
* Perform With Test Before Varying _variable_ From _expression_ By _expressions_ Until _expression_
    _statement_...
  End-Perform [;]
* Perform With Test After Varying _variable_ From _expression_ By _expressions_ Until _expression_
    _statement_...
  End-Perform [;]

If a Break or Next Sentence statement is encountered, looping ends regardless of the
expression's value. If a Continue statement is encountered, statements
following it are skipped, and looping continues.
If not specified, the test expression is performed before the block of statements.
"""
    # Echo the control portion, not the statements
    if dd.echo:
        print_stderr(SSM.source_for(statement, statement.children[-1]))
    ba_ind = statement.children[0]
    if isinstance(ba_ind, Tree) and ba_ind.data in ('test_before', 'test_after'):
        test_before = ba_ind.data == 'test_before'
        cindex = 1
    else:
        test_before = True
        cindex = 0
    path = var_name_path(statement.children[cindex])
    cindex += 1
    value = eval_to_number(dd, bind_operations(statement.children[cindex]), 'Perform Varying start value')
    cindex += 1
    inc = eval_to_number(dd, bind_operations(statement.children[cindex]), 'Perform Varying increment')
    if inc == 0: raise ValueError('Perform Varying requires a non-zero increment')
    cindex += 1
    predicate = bind_operations(statement.children[cindex])
    cindex += 1
    try:
        while True:
            do_set(dd, value, *path)
            if test_before and poly_bool(eval_expr(dd, predicate)): return
            try:
                for s in statement.children[cindex:]: dispatch_statement(dd, s)
            except VgrStatementBreak:
                return
            except VgrStatementContinue:
                pass
            value += inc
            if not test_before and poly_bool(eval_expr(dd, predicate)): return
    finally:
        do_unset(dd, *path)

def execute_compute(dd: DataDictionary, statement: Tree) -> None:
    """Assign a value to a variable.

* Compute _variable_ = _expression_ [;]
"""
    execute_set(dd, statement)

def execute_next_sentence(_: DataDictionary, statement: Tree) -> None:
    """Exits the current block of statements.

* Next Sentence [;]

Can be used with conditional and looping statements
"""
    raise VgrStatementBreak(statement)

@control_statement
def execute_if(dd: DataDictionary, statement: Tree) -> None:
    """Conditionally execute a block of statements.

* If _expression_
    _statement_...
  End-If [;]
* If _expression_
    _statement_...
  Else
    _statement_...
  End-If [;]

If the expression evaluates to True the first block of statements is executed.
If it evaluates to False, the second block of statements, if provided, is executed.
"""
    exec_if_else(dd, statement, True)

def execute_inc(dd: DataDictionary, statement: Tree) -> None:
    """Increment a counter by an amount

* Set _variable_ Up By _expression_ [;]

If the variable does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar opertion.
"""
    path = var_name_path(statement.children[0])
    x = poly_number(dd.get_var_user(*path)) or 0
    y = poly_number(eval_expr(dd, statement.children[1])) or 0
    do_set(dd, poly_add(x, y), *path)

def execute_dec(dd: DataDictionary, statement: Tree) -> None:
    """Deccrement a counter by an amount

* Set _variable_ Down By _expression_ [;]

If the variable does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar opertion.
"""
    path = var_name_path(statement.children[0])
    x = poly_number(dd.get_var_user(*path)) or 0
    y = poly_number(eval_expr(dd, statement.children[1])) or 0
    do_set(dd, poly_sub(x, y), *path)

def execute_move_to(dd: DataDictionary, statement: Tree) -> None:
    """Assign a value to a variable.

* Move _expression_ To _variable_ [;]
* Move Corresponding _expression_ To _variable_ [;]
* Move Corr _expression_ To _variable_ [;]

The first form is equivalent to a SET operation.
The second form works with dictionaries, copying attribute from the
evaluated _expression_ to _variable_. If the variable does not exist,
is None or not a dictionary, a regular move is performed.
If _expression_ does not resolve to a dictionary, the corresponding
request is ignored and a regular move is performed.
"""
    corresponding = False
    start = 0
    fc = statement.children[0]
    if isinstance(fc, Token) and fc.value == 'corr':
        corresponding = True
        start = 1
    expr = statement.children[start]
    src = eval_expr(dd, expr)
    path = var_name_path(statement.children[start + 1])
    dest = dd.get_var_user(*path) if corresponding else None
    if isinstance(src, dict) and isinstance(dest, dict):
        # Should end up here if corresponding was specified,
        # what we are moving is a dictionary, and the
        # destination existed and is also a dictionary
        dest.update({k: src[k] for k in src if k in dest.keys()})
        # This isn't strictly needed as we've done a modification in place
        # However, it does print out something in verbose, so we execute
        # for that side effect
        do_set(dd, dest, *path)
    else:
        # Either no corresponding, or either the src/dest is not a dict
        # This is like a "regular" set
        do_assignment(dd, expr, src, path)

def execute_add_to(dd: DataDictionary, statement: Tree) -> None:
    """ Add one or more values to a variable

* Add _expression_... To _variable_ [End-Add] [;]

If the variable does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar opertion.
"""
    path = tuple(name.value for name in statement.children[-1].children)
    x = poly_number(dd.get_var_user(*path)) or 0
    args = tuple(poly_number(eval_expr(dd, expr)) or 0 for expr in statement.children[:-1])
    do_set(dd, poly_add(x, *args), *path)

def execute_add_giving(dd: DataDictionary, statement: Tree) -> None:
    """ Add two or more values and assign to a variable

* Add _expression_... To _expression_ Giving __variable_ [End-Add] [;]

If the variable does not exist, it is created.
This is fundamentally an arithmetic, scalar opertion.
"""
    path = tuple(name.value for name in statement.children[-1].children)
    args = tuple(poly_number(eval_expr(dd, expr)) or 0 for expr in statement.children[:-1])
    do_set(dd, poly_add(*args), *path)

def execute_sub_from(dd: DataDictionary, statement: Tree) -> None:
    """ Subtract one or more values from a variable

* Subtract _expression_... From _variable_ [;]

If the variable does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar opertion.
"""
    path = tuple(name.value for name in statement.children[-1].children)
    x = poly_number(dd.get_var_user(*path)) or 0
    args = tuple(poly_number(eval_expr(dd, expr)) or 0 for expr in statement.children[:-1])
    do_set(dd, poly_sub(x, *args), *path)

def execute_sub_giving(dd: DataDictionary, statement: Tree) -> None:
    """ Subtract two or more values and assign to a variable

* Subtract _expression_... From _expression_ Giving _variable_ [;]

If the variable does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar opertion.
"""
    path = tuple(name.value for name in statement.children[-1].children)
    args = tuple(poly_number(eval_expr(dd, expr)) or 0 for expr in statement.children[:-1])
    do_set(dd, poly_sub(args[-1], *args[:-1]), *path)

def execute_mul_by(dd: DataDictionary, statement: Tree) -> None:
    """ Multiply one number by another

* Multiply _expression_ By _variable_ [;]
* Multiply _expression_ By _expression_ Giving _variable_ [;]

In the first form, the variable is multiplied by the results of the expression.
In the second, the result of the multiplication is placed into the variable.

In either case, if the variable does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar opertion.
"""
    path = tuple(name.value for name in statement.children[-1].children)
    args = tuple(poly_number(eval_expr(dd, expr)) or 0 for expr in statement.children[:-1])
    if len(args) == 1:
        value = poly_mul(poly_number(dd.get_var_user(*path)) or 0, args[0])
    else:
        value = poly_mul(args[0], args[1])
    do_set(dd, value, *path)

def execute_div_into(dd: DataDictionary, statement: Tree) -> None:
    """ Divide one number by another

* Divide _expression_ Into _variable_ [;]
* Divide _expression_ Into _expression_ Giving _variable_ [;]

In the first form, the variable is divided by the results of the expression.
In the second, the result of the division is placed into the variable.

In either case, if the variable does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar opertion.
"""
    path = tuple(name.value for name in statement.children[-1].children)
    args = tuple(poly_number(eval_expr(dd, expr)) or 0 for expr in statement.children[:-1])
    if len(args) == 1:
        value = poly_div(poly_number(dd.get_var_user(*path)) or 0, args[0])
    else:
        value = poly_div(args[1], args[0])
    do_set(dd, value, *path)

def execute_div_by(dd: DataDictionary, statement: Tree) -> None:
    """ Divide one number by another and assigning the result to a variable

* Divide _expression_ By _expression_ Giving _variable_ [;]

The result of the division is placed into the variable.

If the variable does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar opertion.
"""
    path = tuple(name.value for name in statement.children[-1].children)
    args = tuple(poly_number(eval_expr(dd, expr)) or 0 for expr in statement.children[:-1])
    do_set(dd, poly_div(*args), *path)

def execute_exhibit(dd: DataDictionary, statement: Tree) -> None:
    """Display the name and values of variables

* Exhibit _variable_ [, _variable_]... [;]

The values are displayed on individual lines. If a variable has sub variables, each
portion is displayed on its own line.

Without arguments, all variables are displayed

Unlike PRINT and PRINTF, the values display are the _representation_ of the data, not
its printable value. This lets you diferentiate between an integer and a string, and
see control characters.
"""
    def exhibit_value(name: str, value: Any) -> None:
        if isinstance(value, dict):
            if value:
                for key in sorted(value.keys()):
                    exhibit_value(name + '.' + key, value[key])
            else:
                print_stdout(name, '= -empty-')
        else:
            print_stdout(name, '=', repr(dd.value_for(value)))
    children = statement.children
    if children:
        for var_name in children:
            path = tuple(name.value for name in var_name.children)
            name = '.'.join(path)
            exists, value = dd.exists(*path)
            if exists:
                exhibit_value(name, value)
            else:
                print_stdout(name, '= -not set-')
    else:
        # No arguments dumps the entire dictionary
        for key in sorted(dd.keys()):
            exhibit_value(key, dd.get_var(key))

def execute_display_on(dd: DataDictionary, statement: Tree) -> None:
    """Print values to either the output (stdout) or error (stderr) streams.

* Display _expression_... [;]
* Display _expression_... On Output [;]
* Display _expression_... On Error [;]

The default is to print to the output stream.
While similar to Print, Display does not use _arg.ofs_ or _arg.ors_, with no separator
between items and ending with a newline.
"""
    dest_stdout = True
    args = tuple()
    if statement.children:
        last_child = statement.children[-1]
        if isinstance(last_child, Tree) and last_child.data in ('stdout', 'stderr', 'stdin'):
            if last_child.data == 'stdin':
                raise VgrRuntimeError(last_child, ValueError(f'Cannot send output to {last_child.data}'))
            dest_stdout = last_child.data == 'stdout'
            args = tuple(eval_expr(dd, expr) for expr in statement.children[:-1])
        else:
            args = tuple(eval_expr(dd, expr) for expr in statement.children)
    if dest_stdout:
        print_stdout(*args, sep='')
    else:
        print_stderr(*args, sep='')
