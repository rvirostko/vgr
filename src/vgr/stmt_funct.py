"""
User defined function implementations
"""

from lark import Tree

from .builtins import bound_ops
from .evaluate import do_set, get_writable_var_path, create_param_list, get_function
from .exec_context import ExecContext
from .tags import control_statement
from .user_callable import UserFunction

@control_statement
@bound_ops("Define Function")
def execute_def_function(ctx: ExecContext, statement: Tree) -> None:
    """
**Define a function**

* [Define] Function *variable* [:]\\
  &emsp;&emsp;*statement*&hellip;\\
  [End-Function | End] [;]
* [Define] Function *variable*(_param_&hellip;) [:]\\
  &emsp;&emsp;*statement*&hellip;\\
  [End-Function | End] [;]

```vgr
**TODO**
```

***Arrow Functions***

Arrow Functions are for short expressions, not for full multi-statement functions.
Parameters need not be declared if empty. Names of parameters follow the rules for variables, but
are a single name, not a dotted path.
The arrow operator separates the parameter list from the body.
The body is either an expression or a dynamic expression using _Compile_(&hellip;).

* Set *variable* (*arg*&hellip;) [-> | →] *expression* [;]
* Set *variable* (*arg*&hellip;) [-> | →] Compile(*expression*) [;]

```vgr
# Simple expression
Set fn(a, b) -> a * b
Exhibit fn
fn = (a,b)→a * b
Print fn
a * b

# Zero arg function
Set now() -> time.now
Set also_now -> time.now

# In-line invocation
Print @fn(5, 3)
15

# All functions are variables
Set c = fn
Print 5.@c(3), @fn(5, 3)
15 15
```

```vgr
# The expression can be compiled from a string
Accept op From stdin
Assert op in ["+", "-", "*", "/"]
Set dyn(x, y) -> Compile("(x {} y) + 10".Format(op))
```

Also see `Call` for details on invoking functions
"""
    # if count <= 2, then we don't have a list of params, just a name and statements
    count = len(statement.children)
    ctx.echo_source(statement, statement.children[2 if count > 2 else 1])
    var_path = get_writable_var_path(ctx, statement.children[0])
    param_paths = create_param_list(ctx, statement.children[1]) if count > 2 else []
    do_set(ctx, UserFunction(param_paths, statement.children[-1].children), *var_path)

@bound_ops("Call")
def execute_call(ctx: ExecContext, statement: Tree) -> None:
    """
**Invoke a function**

* Call *variable* [Giving *variable*] [;]
* Call *variable* Using *expression*&hellip; [Giving *variable*] [;]
* Call *variable*(*expression*&hellip;) [Giving *variable*] [;]

```vgr
**TODO**
```
"""
    fn = get_function(ctx, statement.children[0])
    values = [ctx.eval_expr(arg) for arg in statement.children[1:]]
    UserFunction.invoke(ctx, fn, values)

def execute_call_giving(ctx: ExecContext, statement: Tree) -> None:
    """*doc merged with call*"""
    fn = get_function(ctx, statement.children[0])
    var_path = get_writable_var_path(ctx, statement.children[-1])
    values = [ctx.eval_expr(arg) for arg in statement.children[1:-1]]
    do_set(ctx, UserFunction.invoke(ctx, fn, values), *var_path)
