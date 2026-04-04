"""
Contains the implementation for the ECHO, DEBUG and VERBOSE statements
"""

from lark import Tree, Token

from .builtins import bound_ops
from .evaluate import bind_operations
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
exhibit vgr.echo
exhibit vgr.echo
vgr.echo = True
```

Also see `Debug` and `Verbose`
"""
    ctx.echo = _flag_value(ctx, bind_operations(statement), 'Echo')
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
debug on
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
    ctx.debug = _flag_value(ctx, statement, 'Debug')
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
    ctx.verbose = _flag_value(ctx, statement, 'Verbose')
    if ctx.verbose or o_verbose: print_stderr('Verbose =', ctx.verbose)

def _flag_value(ctx: ExecContext, statement: Tree, name: str) -> bool:
    # default behavior for a flag is a request to turn on
    if not statement.children: return True
    # This is a bit of a hack to allow "<flag> [on|off]"
    # without messing with the grammar
    first_child = statement.children[0]
    if isinstance(first_child, Tree) and first_child.data == 'var_ref' and len(first_child.children) == 1:
        arg = first_child.children[0]
        if isinstance(arg, Token) and arg.type == 'NAME':
            value = str(arg.value).casefold()
            if value == 'on': return True
            if value == 'off': return False
    rc = ctx.eval_to_bool(first_child, name, True)
    return False if rc is None else rc
