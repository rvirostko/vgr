"""
COBOL statements
"""

from typing import Any
import sys

from lark import Tree
import pwinput

from ..app_exceptions import (
    BlockType,
    VgrRuntimeError,
    VgrStatementBreak,
    VgrStatementContinue,
)
from ..evaluate import bind_operations, do_set, get_writable_var_path, _var_name_path
from ..exec_context import ExecContext
from ..builtins import (
    bound_ops,
    poly_findstr,
    poly_repr,
    poly_str,
    poly_true,
    poly_type,
)
from ..redir import print_stderr, print_stdout
from ..stmt_exec import LOOP_META_PATH, set_loop_meta
from ..tags import control_statement

@bound_ops("Exit Perform")
def execute_exit_perform(_: ExecContext, statement: Tree) -> None:
    """
**Ends the execution of a Perform loop**

* Exit Perform

```vgr
Repeat 3 Times:
    Print "a"
    Exit Perform
    Print "b" # Never executes
End-Repeat
a
```

Also see `Break` and `Continue`
"""
    raise VgrStatementBreak(statement, BlockType.PERFORM)

@control_statement
@bound_ops("Perform Varying")
def execute_perform_varying(ctx: ExecContext, statement: Tree) -> None:
    """
**Execute a block of statements while increasing or decreasing a variable's value**

* Perform Varying *variable* From *expression* By *expression* Until *expression*\\
  &emsp;&emsp;*statement*&hellip;\\
  End-Perform
* Perform With Test [Before | After] Varying *variable* From *expression* By *expression* Until *expression*\\
  &emsp;&emsp;*statement*&hellip;\\
  End-Perform

If a `Break` is encountered, looping ends regardless of the
expression's value. If `Continue` is encountered, statements
following it are skipped and looping continues.

If not specified, the test expression is performed before the block of statements.

Statements have access to the *$loop* variable, but only *index* and _first_.

```vgr
Perform Varying counter From 0 By 1 Until counter > 5
    Print counter, ":", counter ** 2
End-Perform

0 : 0
1 : 1
2 : 4
3 : 9
4 : 16
5 : 25

Perform Varying x From 2 By 2 Until x > 10
    Print x, $loop
End-Perform

2 {'index': 0, 'first': True}
4 {'index': 1, 'first': False}
6 {'index': 2, 'first': False}
8 {'index': 3, 'first': False}
10 {'index': 4, 'first': False}
```

Also see `For Next` and `Exit Perform`
"""
    # Echo the control portion, not the statements
    ctx.echo_source(statement, statement.children[-1])
    ba_ind = statement.children[0]
    if isinstance(ba_ind, Tree) and ba_ind.data in ('test_before', 'test_after'):
        test_before = ba_ind.data == 'test_before'
        cindex = 1
    else:
        test_before = True
        cindex = 0
    var_path = get_writable_var_path(ctx, statement.children[cindex])
    cindex += 1
    value = ctx.eval_to_number(bind_operations(statement.children[cindex]), 'Perform Varying start value')
    cindex += 1
    inc = ctx.eval_to_number(bind_operations(statement.children[cindex]), 'Perform Varying increment')
    if inc == 0: raise ValueError('Perform Varying requires a non-zero increment')
    cindex += 1
    predicate = bind_operations(statement.children[cindex])
    cindex += 1
    meta = { }
    ctx.dd.push_frame([(var_path, None), (LOOP_META_PATH, meta)])
    try:
        i = 0
        while True:
            set_loop_meta(meta, i)
            ctx.set_var(value, *var_path)
            if test_before and poly_true(ctx.eval_expr(predicate)): return
            try:
                ctx.dispatch_statements(statement.children[cindex:])
            except VgrStatementBreak as e:
                e.validate_for_block(BlockType.PERFORM)
                return
            except VgrStatementContinue as e:
                e.validate_for_block(BlockType.PERFORM)
            value += inc
            if not test_before and poly_true(ctx.eval_expr(predicate)): return
            i += 1
    finally:
        ctx.dd.pop_frame()

@bound_ops("Move")
def execute_move_to(ctx: ExecContext, statement: Tree) -> None:
    """
**Assign a value to a variable**

* Move *expression* To *variable*
* Move Corresponding *expression* To *variable*
* Move Corr *expression* To *variable*

The first form is equivalent to `Set`.
The second and third forms work with dictionaries, copying attribute from the
evaluated *expression* to *variable*. If *variable* does not exist,
is `None` or not a dictionary, a regular move is performed.
If *expression* does not resolve to a dictionary, the corresponding
request is ignored and a regular move is performed.

```vgr
Move 5 To a
Move a + 2 To b
Exhibit a b
a = 5
b = 7

Move {"x": 1, "y": 2, "z": 3} To a
Move {"w": 5, "x": 10} To b
Move Corresponding b To a
Exhibit a
a.x = 10
a.y = 2
a.z = 3
```

Also see `Set` and `Add()` for combining dictionaries
"""
    corresponding = False
    start = 0
    fc = statement.children[0]
    if isinstance(fc, Tree) and fc.data == 'cobol_move_corr':
        corresponding = True
        start = 1
    src_value = ctx.eval_expr(statement.children[start])
    var_path = get_writable_var_path(ctx, statement.children[start + 1])
    dest_value = ctx.get_var(*var_path) if corresponding else None
    if isinstance(src_value, dict) and isinstance(dest_value, dict):
        # Should end up here if corresponding was specified,
        # what we are moving is a dictionary, and the
        # destination existed and is also a dictionary
        dest_value.update({k: src_value[k] for k in src_value if k in dest_value.keys()})
        # This isn't strictly needed as we've done a modification in place
        # However, it does print out something in verbose, so we execute
        # for that side effect
        do_set(ctx, dest_value, *var_path)
    else:
        # Either not corresponding move or the src/dest are not a dicts
        # Just a "regular" set
        do_set(ctx, src_value, *var_path)

@bound_ops("String")
def execute_string(ctx: ExecContext, statement: Tree) -> None:
    """
**Concatenate strings**

* String *value*&hellip; Into *variable*
* String\\
  &emsp;&emsp;*value* Delimited By Size\\
  &emsp;&emsp;*value* Delimited By _delimiter_\\
  &emsp;&emsp;Into *variable*\\
  End-String

All *value* arguments may be constants or expressions that yield a string,
integer, or float. If a *value* is `None` it is ignored.

If *variable* does not exist it is created. If it already exists, its
value is overwritten.

By default the entirety of each *value* is added to the result.
If a delimiter is specified, as in the second form of the syntax, the part of
the value to the left of _delimiter_ is used. If *value* does not contain the
delimiter string, it is added in its entirety. The search for _delimiter_
uses the same rules as `FindStr()`.

```vgr
Set h To "Hello"
Set w To "World"
String h, w Into s → "HelloWorld"
String h, ", ", w Into s → "Hello, World"
```

```vgr
Set Customer-Name To "Jones, Inc"
Set Customer-Id To "A104"
String
    Customer-Name Delimited By ","
    Customer-Id   Delimited By Size
    Into Output-Buffer
End-String
Print Output-Buffer → "JonesA104"
```

Also see `FindStr()`
"""
    var_path = get_writable_var_path(ctx, statement.children[-1])
    value = ''
    for item in statement.children[:-1]:
        part_type = item.data
        expr = item.children[0]
        part = ctx.eval_expr(expr)
        if part is None:
            part = ''
        elif isinstance(part, (bool, int, float, str)):
            part = poly_str(part)
        else:
            raise VgrRuntimeError(expr, ValueError(f'Cannot String {poly_type(part)!r}'))
        if part_type == 'full':
            value += part
        elif part_type == 'delimited':
            index = -1
            delimiter = ctx.eval_to_str(item.children[-1], "Delimiter")
            index = poly_findstr(part, delimiter) if delimiter else -1
            value += part[0:index] if index >= 0 else part
        else:
            raise NotImplementedError(f'String option {part_type!r} not implemented')
    do_set(ctx, value, *var_path)

@bound_ops("Exhibit")
def execute_exhibit(ctx: ExecContext, statement: Tree) -> None:
    """
**Display the names and values of variables**

* Exhibit *
* Exhibit *variable*&hellip;

`Exhibit` is not typically used in scripts, but is useful for debugging
and for working in the REPL.

The values are displayed on individual lines. If a variable has sub-values, each
portion is displayed on its own line.

With a single argument of *\\** all variables are displayed.

Unlike `Print` et al, the values display are the _representation_ of the data, not
its printable value. This lets you diferentiate between an integer and a string as
well as seeing control characters.

```vgr
Exhibit math.pi math.e
math.pi = 3.141592653589793
math.e = 2.718281828459045

Print math.float
{'max': 1.7976931348623157e+308, 'min': 2.2250738585072014e-308}
Exhibit math.float
math.float.max = 1.7976931348623157e+308
math.float.min = 2.2250738585072014e-308

Exhibit string.whitespace
string.whitespace = ' \\t\\n\\r\\x0b\\x0c'
```

Also see `Print`, `Printf`, and `Repr()`
"""
    def _exhibit_value(name: str, value: Any) -> None:
        if hasattr(value, 'keys') and callable(value.keys):
            keys = value.keys()
            if len(keys):
                for key in sorted(keys):
                    pkey = str(key)
                    _exhibit_value(name + '.' + pkey if len(name) > 0 else pkey, value[key])
            else:
                print_stdout(name, '= -empty-')
        else:
            print_stdout(name, '=', poly_repr(value))
    children = statement.children
    if children:
        for var_name in children:
            var_path = _var_name_path(var_name)
            exists, true_name, value = ctx.var_exists(*var_path)
            if exists:
                _exhibit_value(true_name, value)
            else:
                print_stdout(true_name, '= -not set-')
    else:
        # No arguments dumps the entire dictionary
        for key in sorted(ctx.dd.keys()):
            _exhibit_value(key, ctx.get_var(key))
