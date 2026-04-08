"""
Contains the implementation for the ECHO, DEBUG and VERBOSE statements
"""

from lark import Tree

from .builtins import(
    bound_ops,
    poly_bool,
)
from .evaluate import(
    bind_operations,
    eval_expr_or_const,
)
from .exec_context import ExecContext
from .redir import print_stderr
from .tags import control_statement

@control_statement
@bound_ops("Echo")
def execute_echo(ctx: ExecContext, statement: Tree) -> None:
    """
**Turn echo mode on or off**

* Echo [;]
* Echo [On | Off] [;]
* Echo *expression* [;]

Without arguments, statement echoing is turned on.
When on, statements are echoed to stderr before execution.
Note that this command never echoes itself.

```vgr
Echo On
Print "Hello"
Print "Hello"
Hello
Echo Off

Exhibit vgr.echo # read-only variable
vgr.echo = False
Echo !vgr.echo
Exhibit vgr.echo
Exhibit vgr.echo
vgr.echo = True
```

Also see `Debug` and `Verbose`
"""
    ctx.echo = _flag_value(ctx, bind_operations(statement))
    ctx.print_verbose('Echo =', ctx.echo)

@bound_ops("Debug")
def execute_debug(ctx: ExecContext, statement: Tree) -> None:
    """
**Turn debug mode on or off**

* Debug [;]
* Debug [On | Off] [;]
* Debug *expression* [;]

Without arguments, debug is turned on.
When on, additional technical output is sent to stderr.

```vgr
Debug On
debug !vgr.debug # read-only variable
  (debug: (Pos: 1:1-1:17)
    (unary_not:not (Pos: 1:7-1:17)
      (var_ref:var_ref (Pos: 1:8-1:11)
        NAME: 'vgr' (Pos: 1:8-1:11 'string')
        NAME: 'debug' (Pos: 1:12-1:17 'string')
      )
    )
  )
```

Also see `Echo` and `Verbose`
"""
    ctx.debug = _flag_value(ctx, statement)
    ctx.print_verbose('Debug =', ctx.debug)

@bound_ops("Verbose")
def execute_verbose(ctx: ExecContext, statement: Tree) -> None:
    """
**Turn verbose mode on or off**

* Verbose [;]
* Verbose [On | Off] [;]
* Verbose *expression* [;]

Without arguments, verbose is turned on.
When on, additional operational output is sent to stderr.

```vgr
Verbose on
Verbose = True
Set a To vgr.verbose # read-only variable
Set a To True
```

Also see `Echo` and `Debug`
"""
    o_verbose = ctx.verbose
    ctx.verbose = _flag_value(ctx, statement)
    if ctx.verbose or o_verbose: print_stderr('Verbose =', ctx.verbose)

def _flag_value(ctx: ExecContext, statement: Tree) -> bool:
    # default behavior for a flag is a request to turn on
    return poly_bool(eval_expr_or_const(ctx, statement.children[0])) if statement.children else True
