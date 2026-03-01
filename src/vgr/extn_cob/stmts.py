"""
COBOL statements
"""

from datetime import datetime
from typing import Any
import sys

from lark import Tree
import pwinput

from ..app_exceptions import (
    BlockType,
    VgrExitingException,
    VgrRuntimeError,
    VgrStatementBreak,
    VgrStatementContinue,
)
from ..evaluate import bind_operations, do_set, get_writable_var_path, _var_name_path
from ..exec_context import ExecContext
from ..mathpak import (
    bound_ops,
    poly_add,
    poly_div,
    poly_eq,
    poly_false,
    poly_findstr,
    poly_ge,
    poly_le,
    poly_lt,
    poly_mul,
    poly_ne,
    poly_number,
    poly_repr,
    poly_str,
    poly_sub,
    poly_true,
    poly_type,
)
from ..redir import print_stderr, print_stdout
from ..stmt_exec import exec_if_else, exec_loop, exec_repeat, LOOP_META_PATH, set_loop_meta
from ..stmt_set import execute_set
from ..tags import control_statement

_DT_FUNCS = {
    'cobol_accept_date':     lambda: datetime.now().strftime('%y%m%d'),
    'cobol_accept_day':      lambda: datetime.now().strftime('%y%j'),
    'cobol_accept_dow':      lambda: datetime.now().weekday() + 1,
    'cobol_accept_epoch':    lambda: int(datetime.now().timestamp()),
    'cobol_accept_time':     lambda: (now := datetime.now()).strftime('%H%M%S') + f'{now.microsecond // 10000:02d}',
    'cobol_accept_yyyyddd':  lambda: datetime.now().strftime('%Y%j'),
    'cobol_accept_yyyymmdd': lambda: datetime.now().strftime('%Y%m%d'),
}

@bound_ops("Accept")
def execute_accept(ctx: ExecContext, statement: Tree) -> None:
    """
**Get user input or retrieve date and time values**

* Accept *variable* [*option*] [;]
* Accept *variable* From [Console | Terminal | Stdin | Sysin | Sysinp] [*option*] [;]
* Accept *variable* From [Unix] Epoch [;]
* Accept *variable* From Date [;]
* Accept *variable* From Date YYYYMMDD [;]
* Accept *variable* From Day YYYYDDD [;]
* Accept *variable* From Day-Of-Week [;]
* Accept *variable* From Day [;]
* Accept *variable* From Time [;]
* Accept *variable* From Timestamp [;]

Note that `Timestamp` and `Epoch` are aliases, returning the number of seconds
since 1-Jan-1970.

For user input, when at end-of-file (when not interactive) or if the user hits return
without entering any information, the contents of *variable* remains
unchanged. There is no limit on the length of user input, but it is a single line.

Options are

* [With] Echo - this is the default
* [With] No Echo - no output is generated
* Secure - typing is masked with asterisks

```vgr
Accept value         // input displayed
Accept value Echo    // input displayed
Accept value No Echo // nothing displayed
Accept value Secure  // asterisks displayed

Accept value From Date YYYYMMDD
Print value → "20251003"
Accept now From Epoch
Print now, time.now → 1759506164 1759506164
```

Also see `FormatTimestamp()`
"""
    var_path = get_writable_var_path(ctx, statement.children[0])
    name = statement.data
    if name in _DT_FUNCS:
        do_set(ctx, _DT_FUNCS.get(statement.data)(), *var_path)
    else:
        option = statement.children[-1].data if len(statement.children) > 1 else 'echo'
        if option == 'echo':
            line = sys.stdin.readline()
        elif option == 'no_echo':
            line = pwinput.pwinput(prompt='', mask='')
        elif option == 'secure':
            line = pwinput.pwinput(prompt='', mask='*')
        else:
            raise VgrRuntimeError(statement.children[-1], ValueError(f'Accept option {option!r} not implemented')) # SNO
        line = line.rstrip('\n') if line else line
        if line: do_set(ctx, line, *var_path)

@bound_ops("Exit Perform")
def execute_exit_perform(_: ExecContext, statement: Tree) -> None:
    """
**Affects the execution of a Perform loop**

* Exit Perform [;] *Exit the containing loop*
* Exit Perform Cycle[;] *Continue loop from the start*

```vgr
Perform 3 Times:
    Display "a"
    Exit Perform
    Display "b" # Never executes
End-Perform
a
```

```vgr
Perform 3 Times:
    Display "a"
    Exit Perform Cycle
    Display "b" # Never executes
End-Perform
a
a
a
```

Also see `Break` and `Continue`
"""
    cmd = statement.data
    if cmd == 'cobol_exit_perform_cycle':
        raise VgrStatementContinue(statement, BlockType.PERFORM)
    if cmd == 'cobol_exit_perform':
        raise VgrStatementBreak(statement, BlockType.PERFORM)
    raise ValueError(f'Unhandled type {cmd!r}') # SNO

@bound_ops("Stop Run")
def execute_stop_run(_: ExecContext, statement: Tree) -> None:
    """
**Terminate execution**

* Stop Run [;]

Ends the program with an exit code of zero.

```vgr
**TODO**
```

Also see `Exit`
"""
    raise VgrExitingException(VgrExitingException.EXIT_SUCCESS, statement)

@control_statement
@bound_ops("Perform Until")
def execute_perform_until(ctx: ExecContext, statement: Tree) -> None:
    """
**Repeatedly execute a block of statements until a condition is reached**

* Perform Until *expression*\\
  &emsp;&emsp;_statement_&hellip;\\
  End-Perform [;]

The block of statements is executed until *expression* evaluates to True.
If a `Break` is encountered, looping ends regardless of the
expression's value. If `Continue` is encountered, statements
following it are skipped, and *expression* is checked again.

Statements have access to the *$loop* variable, but only *index* and _first_.

```vgr
Move 0 To counter
Perform Until counter > 5
    Display counter " : " counter ** 2
    Set counter Up By 1
End-Perform

0 : 0
1 : 1
2 : 4
3 : 9
4 : 16
5 : 25
```

Also see `Exit Perform`
"""
    exec_loop(ctx, statement, False, BlockType.PERFORM)

@control_statement
@bound_ops("Perform Times")
def execute_perform_times(ctx: ExecContext, statement: Tree) -> None:
    """
**Execute a block of statements a fixed number of times**

* Perform *expression* Times\\
  &emsp;&emsp;_statement_&hellip;\\
  End-Perform [;]

The block of statements is executed the given number of times.
The *expression* is evaluated and converted to an integer, rounding down.
For any statements to execute, the value must be greater than or equal to one.
If `Break` is encountered, looping ends regardless of the
expression's value. If `Continue` is encountered, statements
following it are skipped and looping continues.

Statements have access to the *$loop* variable, including *index*, *length*, _first_, and _last_.

```vgr
Move 5 To counter
Perform 3 Times
    Display counter " : " counter ** 2
    Set counter Down By 1
End-Perform

5 : 25
4 : 16
3 : 9
```

Also see `Repeat`
"""
    exec_repeat(ctx, statement, BlockType.PERFORM)

@control_statement
@bound_ops("Perform Varying")
def execute_perform_varying(ctx: ExecContext, statement: Tree) -> None:
    """
**Execute a block of statements while increasing or decreasing a variable's value**

* Perform Varying *variable* From *expression* By *expression* Until *expression*\\
  &emsp;&emsp;_statement_&hellip;\\
  End-Perform [;]
* Perform With Test [Before | After] Varying *variable* From *expression* By *expression* Until *expression*\\
  &emsp;&emsp;_statement_&hellip;\\
  End-Perform [;]

If a `Break` is encountered, looping ends regardless of the
expression's value. If `Continue` is encountered, statements
following it are skipped and looping continues.

If not specified, the test expression is performed before the block of statements.

Statements have access to the *$loop* variable, but only *index* and _first_.

```vgr
Perform Varying counter From 0 By 1 Until counter > 5
    Display counter " : " counter ** 2
End-Perform

0 : 0
1 : 1
2 : 4
3 : 9
4 : 16
5 : 25

Perform Varying x From 2 By 2 Until x > 10:
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

@bound_ops("Compute")
def execute_compute(ctx: ExecContext, statement: Tree) -> None:
    """
**Evaluate and expression and assign to a variable**

* Compute *variable* = *expression* [;]
* Compute *variable* Equal *expression* [;]

```vgr
Move {"x": 5, "y": 5} To start_pt
Move {"x": -10, "y": -10} To end_pt
Compute distance Equal (
        ((start_pt.x - end_pt.x) ** 2) +
        ((start_pt.y - end_pt.y) ** 2)
    ) ** .5
End-Compute
distance → 21.213203435596427
```

Also see `Set` and `Move`
"""
    execute_set(ctx, statement)

@control_statement
@bound_ops("If End-If")
def execute_if(ctx: ExecContext, statement: Tree) -> None:
    """
**Conditionally execute a block of statements**

* If *expression*\\
  &emsp;&emsp;_statement_&hellip;\\
  End-If [;]
* If *expression*\\
  &emsp;&emsp;_statement_&hellip;\\
  Else\\
  &emsp;&emsp;_statement_&hellip;\\
  End-If [;]

COBOL compatiple version of `If Else`

If *expression* evaluates to `True` the first block of statements is executed.
If it evaluates to `False`, the second block of statements, if provided, is executed.

```vgr
Move 5 To a
Move 7 To b
If a > b
    Display "a is larger"
Else
    If b > a
        Display "b is larger"
    Else
        Display "a and b are equal"
    End-If
End-If

"b is larger"
```

Also see `If Else`, `Break`, and `Continue`
"""
    exec_if_else(ctx, statement, True)

@bound_ops("Set Up")
def execute_inc(ctx: ExecContext, statement: Tree) -> None:
    """
**Increment a counter by an amount**

* Set *variable* Up By *expression* [;]

If *variable* does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar operation.

```vgr
Move 5 To counter
Perform 4 Times
    Display counter " : " counter ** 2
    Set counter Up By counter * 1.5
End-Perform

5 : 25
12.5 : 156.25
31.25 : 976.5625
78.125 : 6103.515625
```

Also see `Exit Perform`, `Set Down`, `-`, and `Set`
"""
    var_path = get_writable_var_path(ctx, statement.children[0])
    x = poly_number(ctx.get_var(*var_path)) or 0
    y = poly_number(ctx.eval_expr(statement.children[1])) or 0
    do_set(ctx, poly_add(x, y), *var_path)

@bound_ops("Set Down")
def execute_dec(ctx: ExecContext, statement: Tree) -> None:
    """
**Deccrement a counter by an amount**

* Set *variable* Down By *expression* [;]

If *variable* does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar operation.

```vgr
Move 5 To counter
Perform 4 Times
    Display counter " : " counter ** 2
    Set counter Down By counter * .5
End-Perform

5 : 25
2.5 : 6.25
1.25 : 1.5625
0.625 : 0.390625
```

Also see `Set Up`, `+`, and `Set`
"""
    var_path = get_writable_var_path(ctx, statement.children[0])
    x = poly_number(ctx.get_var(*var_path)) or 0
    y = poly_number(ctx.eval_expr(statement.children[1])) or 0
    do_set(ctx, poly_sub(x, y), *var_path)

@bound_ops("Move")
def execute_move_to(ctx: ExecContext, statement: Tree) -> None:
    """
**Assign a value to a variable**

* Move *expression* To *variable* [;]
* Move Corresponding *expression* To *variable* [;]
* Move Corr *expression* To *variable* [;]

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

@bound_ops("Add")
def execute_add_to(ctx: ExecContext, statement: Tree) -> None:
    """
**Add one or more values to a variable**

* Add *expression*&hellip; To *variable* [End-Add] [;]
* Add *expression*&hellip; To *expression* Giving *variable* [End-Add] [;]

If *variable* does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar operation.

```vgr
Move 5 To a
Move 7 To b
Move 0 To c

Add a To c
Exhibit c
c = 5

Add a b To c
Exhibit c
c = 17

Add a b To c Giving d
Exhibit c d
c = 17
d = 29
```

Also see `Add()` and `Sum()`, `+`, and `Set`
"""
    var_path = get_writable_var_path(ctx, statement.children[-1])
    x = poly_number(ctx.get_var(*var_path)) or 0
    args = list(poly_number(ctx.eval_expr(expr)) or 0 for expr in statement.children[:-1])
    do_set(ctx, poly_add(x, *args), *var_path)

# Doc added to add_to
def execute_add_giving(ctx: ExecContext, statement: Tree) -> None:
    var_path = get_writable_var_path(ctx, statement.children[-1])
    args = list(poly_number(ctx.eval_expr(expr)) or 0 for expr in statement.children[:-1])
    do_set(ctx, poly_add(*args), *var_path)

@bound_ops("Subtract")
def execute_sub_from(ctx: ExecContext, statement: Tree) -> None:
    """
**Subtract one or more values from a variable**

* Subtract *expression*&hellip; From *variable* [;]
* Subtract *expression*&hellip; From *expression* Giving *variable* [;]

If *variable* does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar operation.

```vgr
Move 5 To a
Move 7 To b
Move 30 To c

Subtract a From c
Exhibit c
c = 25

Subtract a b From c
Exhibit c
c = 13

Subtract a b From c Giving d
Exhibit c d
c = 13
d = 1
```

Also see `Sub()`, `-`, and `Set`
"""
    var_path = get_writable_var_path(ctx, statement.children[-1])
    x = poly_number(ctx.get_var(*var_path)) or 0
    args = list(poly_number(ctx.eval_expr(expr)) or 0 for expr in statement.children[:-1])
    do_set(ctx, poly_sub(x, *args), *var_path)

# Doc added to sub_from
def execute_sub_giving(ctx: ExecContext, statement: Tree) -> None:
    var_path = get_writable_var_path(ctx, statement.children[-1])
    args = list(poly_number(ctx.eval_expr(expr)) or 0 for expr in statement.children[:-1])
    do_set(ctx, poly_sub(args[-1], *args[:-1]), *var_path)

@bound_ops("Multipy")
def execute_mul_by(ctx: ExecContext, statement: Tree) -> None:
    """
**Multiply one number by another**

* Multiply *expression* By *variable* [;]
* Multiply *expression* By *expression* Giving *variable* [;]

In the first form, *variable* is multiplied by the results of *expression*.
In the second, the result of the multiplication is placed into *variable*.

In either case, if *variable* does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar operation.

```vgr
Move 5 To a
Move 7 To b
Move 11 To c

Multiply a By c
Exhibit c
c = 55

Multiply b By c Giving d
Exhibit c d
c = 55
d = 385
```

Also see `Mul()`, `*`, and `Set`
"""
    var_path = get_writable_var_path(ctx, statement.children[-1])
    args = list(poly_number(ctx.eval_expr(expr)) or 0 for expr in statement.children[:-1])
    if len(args) == 1:
        value = poly_mul(poly_number(ctx.get_var(*var_path)) or 0, args[0])
    else:
        value = poly_mul(args[0], args[1])
    do_set(ctx, value, *var_path)

@bound_ops("Divide")
def execute_div_into(ctx: ExecContext, statement: Tree) -> None:
    """
**Divide one number by another**

* Divide *expression* Into *variable* [;]
* Divide *expression* Into *expression* Giving *variable* [;]
* Divide *expression* By *expression* Giving *variable* [;]

In the first form *variable* is divided by the results of *expression*.
In the other forms the result of the division is placed into *variable*.

In either case, if *variable* does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar operation.

```vgr
Move 2 To a
Move 5 To b
Divide a Into b
Exhibit a b
a = 2
b = 2.5

Divide a Into b Giving c
Exhibit b c
b = 2.5
c = 1.25

Divide b By a Giving c
Exhibit c
c = 1.25
```

Also see `Div()`, `/`, and `Set`
"""
    var_path = get_writable_var_path(ctx, statement.children[-1])
    args = list(poly_number(ctx.eval_expr(expr)) or 0 for expr in statement.children[:-1])
    if len(args) == 1:
        value = poly_div(poly_number(ctx.get_var(*var_path)) or 0, args[0])
    else:
        value = poly_div(args[1], args[0])
    do_set(ctx, value, *var_path)

# Doc added to div_into
def execute_div_by(ctx: ExecContext, statement: Tree) -> None:
    var_path = get_writable_var_path(ctx, statement.children[-1])
    args = list(poly_number(ctx.eval_expr(expr)) or 0 for expr in statement.children[:-1])
    do_set(ctx, poly_div(*args), *var_path)

@bound_ops("String")
def execute_string(ctx: ExecContext, statement: Tree) -> None:
    """
**Concatenate strings**

* String *value*&hellip; Into *variable* [;]
* String\\
  &emsp;&emsp;*value* Delimited By Size\\
  &emsp;&emsp;*value* Delimited By _delimiter_\\
  &emsp;&emsp;Into *variable*\\
  End-String [;]

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

* Exhibit * [;]
* Exhibit *variable*&hellip; [;]

`Exhibit` is not typically used in scripts, but is useful for debugging
and for working in the REPL.

The values are displayed on individual lines. If a variable has sub-values, each
portion is displayed on its own line.

With a single argument of *\\** all variables are displayed.

Unlike `Display` et al, the values display are the _representation_ of the data, not
its printable value. This lets you diferentiate between an integer and a string, and
see control characters.

```vgr
Exhibit math.pi math.e
math.pi = 3.141592653589793
math.e = 2.718281828459045

Display math.float
{'max': 1.7976931348623157e+308, 'min': 2.2250738585072014e-308}
Exhibit math.float
math.float.max = 1.7976931348623157e+308
math.float.min = 2.2250738585072014e-308

Exhibit string.whitespace
string.whitespace = ' \\t\\n\\r\\x0b\\x0c'
```

Also see `Display`, `Print`, `Printf`, and `Repr()`
"""
    def _exhibit_value(name: str, value: Any) -> None:
        if hasattr(value, 'keys') and callable(value.keys):
            keys = value.keys()
            if len(keys):
                for key in sorted(keys):
                    _exhibit_value(name + '.' + key if len(name) > 0 else key, value[key])
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

@bound_ops("Display")
def execute_display_on(ctx: ExecContext, statement: Tree) -> None:
    """
**Print values to either the output or error streams**

* Display *expression*&hellip; [*option*]&hellip; [;]

The default is to print to the output stream.
While similar to `Print`, `Display` does not use *env.OFS* or *env.ORS*, instead
it defaults to no separator between items and always ending with a newline.

*Options*

* Upon [Output | Error] - send the output to stdout or stderr respectively. If this
  option is not specified, output goes to stdout.
* [With] No Advancing - do not add a newline at the end of the output

```vgr
Move "Hello" To Greeting
Move "World" To Whom
Print Greeting, Whom
Hello World
Printf "{}, {}!", Greeting, Whom
Hello, World!
Display Greeting Whom
HelloWorld
```

Also see `Print`, `Printf`, and `Exhibit`, as well as `Open` and `Close`
"""
    dest_stdout = True
    ender = None
    flush = None
    # Options appear after arguments
    # We keep looking at the end of the list for known options
    # and pull then off the list
    args = list(statement.children)
    while args:
        last_child = args[-1]
        if isinstance(last_child, Tree):
            if last_child.data == 'upon':
                where = last_child.children[0].data
                if where in ['stdout', 'stderr']:
                    dest_stdout = where == 'stdout'
                else:
                    raise VgrRuntimeError(last_child, ValueError(f'Cannot send output to {where!r}'))
                args.pop()
                continue
            if last_child.data == 'no_advance':
                ender = ''
                flush = True
                args.pop()
                continue
        # Not an option, so exit loop
        break
    args = list(ctx.eval_expr(expr) for expr in args)
    if dest_stdout:
        print_stdout(*args, sep='', end=ender, flush=flush)
    else:
        print_stderr(*args, sep='', end=ender, flush=flush)

@control_statement
@bound_ops("Evaluate")
def execute_evaluate(ctx: ExecContext, statement: Tree) -> None:
    """
**Choose from a set of statements based on a value**

* Evaluate *expression*\\
  &emsp;&emsp;When [Not] *expression* _statement_&hellip;\\
  &emsp;&emsp;When [Not] *expression* [Through | Thru] *expression* _statement_&hellip;\\
  &emsp;&emsp;When Other _statement_&hellip;\\
  End-Evaluate [;]

The *expression* in the statement is evaluated and it becomes the
_desired value_ which is compared against values in `When` clauses.
The `Other` clause is executed if no `When`s match. Its use is optional.

The comparison performed is identical to the `==` operator–or `!-` if `Not` is present– and follows
the same type rules.
The values in `When` clauses are examined in order, and the first to match
the desired value has its block of statements executed.

If none of the `When` clauses match the desired value the `When Other` cause,
if provided, is selected. Note that this clause _must_ be the last `When`
cause, and that at least one other `When` must be specified.

```vgr
Move time.today.month To month
Evaluate month
    When 1 Thru 2   Move "a Winter" To season
    When 3 Thru 5   Move "a Spring" To season
    When 6 Thru 8   Move "a Summer" To season
    When 9 Thru 11  Move "an Autumn" To season
    When 12         Move "a Winter" To season
    When Other Assert False: "Invalid month {}", month
End-Evaluate
Display "Month " month " is " season " month"

Move 0 to Lower_bound
Move 255 to Upper_bound
Move 3 to Modulus
Evaluate True
    When X Is None             Assert False: "X is not set"
    When X.Type() != "integer" Assert False: "X must be an integer"
    When X < Lower_bound       Assert False: "X cannot be less than {}", Lower_bound
    When X > Upper_bound       Assert False: "X cannot be greater than {}", Upper_bound
    When X.FloorDiv(Modulus)   Assert False: "X must be divisible by {}", Modulus
    When Other Display X " checks out!"
End-Evaluate
```

Also see `Choose` and `Choose Using`
"""
    ctx.echo_source(statement, statement.children[1])
    statement_children = iter(statement.children)
    # The first child is the expression used in the value comparisons
    desired_value = ctx.eval_expr(bind_operations(next(statement_children, None)))
    choosen_block = None
    for block in statement_children:
        if block.data in ['cobol_when_block', 'cobol_when_not_block']:
            compare_op = poly_eq if block.data == 'cobol_when_block' else poly_ne
            # NB: this may cause a TypeError if there is a mismatch
            #     betweeen the desired_value's type, which drives "casting"
            #     and the resulting type of the expression
            values_children = iter(block.children)
            if compare_op(desired_value, ctx.eval_expr(bind_operations(next(values_children)))):
                ctx.echo_source(block, block.children[1])
                # The children start with the value, and the iterator now
                # points to the following statements
                choosen_block = values_children
        elif block.data in ['cobol_when_thru_block', 'cobol_when_not_thru_block']:
            test_op = poly_true if block.data == 'cobol_when_thru_block' else poly_false
            values_children = iter(block.children)
            v1 = ctx.eval_expr(bind_operations(next(values_children)))
            v2 = ctx.eval_expr(bind_operations(next(values_children)))
            if poly_lt(v2, v1): v1, v2 = v2, v1
            if test_op(poly_ge(desired_value, v1) and poly_le(desired_value, v2)):
                ctx.echo_source(block, block.children[1])
                # The children start with the value, and the iterator now
                # points to the following statements
                choosen_block = values_children
        else:
            # it is 'when other' which is automatically selected
            ctx.echo_source(block, block.children[0])
            choosen_block = iter(block.children)
        # If a block of statements was choosen execute them
        if choosen_block is not None:
            ctx.dispatch_statements(choosen_block)
            return
