"""
User defined function implementations
"""

from typing import Any
from lark import Tree

from .app_exceptions import VgrRuntimeError
from .builtins import (
    bound_ops,
    poly_clamp,
)
from .evaluate import (
    bind_operations,
    create_param_list,
    do_set,
    get_function,
    get_writable_var_path,
)
from .exec_context import ExecContext
from .tags import control_statement
from .stmt_set import (
    assert_var_okay_for_const,
    do_set_constant,
)
from .user_callable import (
    ArrowFunction,
    UserFunction,
)

# This is used when user requests caching for a function but doesn't specify a size
DEFAULT_CACHE_SIZE: int = 64
MAX_CACHE_SIZE: int = 32_768

@control_statement
@bound_ops("Define Function")
def execute_def_function(ctx: ExecContext, statement: Tree) -> None:
    """
**Define a function**

* [Define] [*modifiers*&hellip;] Function *variable* [:]\\
  &emsp;&emsp;*statement*&hellip;\\
  [End-Function | End]
* [Define] [*modifiers*&hellip;] Function *variable*(_param_&hellip;) [:]\\
  &emsp;&emsp;*statement*&hellip;\\
  [End-Function | End]
* [Define] [*modifiers*&hellip;] Function *variable*(*arg*&hellip;) [-> | →] *expression*
* [Define] [*modifiers*&hellip;] Function *variable*(*arg*&hellip;) [-> | →] Compile(*expression*)

**Modifiers**

* Constant - the *variable* for the function cannot be modified, just as with the `Constant` statement
* Cache or Cached - results are kepts in an LRU cache. Caching results introduces time and
  memory overhead, so this is should be used only for unctions with complicated or long computations,
  or those making idempotent calls to external systems.\\
  Cache size can be set by using `Cache(expression)` where *expression* resolves at definition time
  to an integer greater than zero. If `None`, the default cache size is used. If less than zero,
  caching is turned off.

```vgr
Define Function lcm(a, b):
    Declare i, limit, g, s As Local
    Set g To a.Max(b)  // Larger value
    Set s To a.Min(b)  // Smaller value
    Set i To g
    Set limit To a * b
    While i <= limit
        If (i % s) == 0 Return i End-If
        Set i += g
    End-While
    Return limit
End-Function
```

***Arrow Functions***

Arrow Functions are for short expressions, not for full multi-statement functions.
Parameters need not be declared if empty. Names of parameters follow the rules for variables, but
are a single name, not a dotted path.
The arrow operator separates the parameter list from the body.
The body is either an expression or a dynamic expression using _Compile_(&hellip;).

```vgr
# Simple expression
Function fn(a, b) -> a * b
Exhibit fn
fn = (a,b)→a * b
Print fn
 → "a * b"

# Zero arg function
Function now() -> time.now
Function also_now -> time.now

# Function invocation
Call fn Using 5, 2 Giving c
Print c
 → 10

# In-line invocation
Print @fn(5, 3)
 → 15

# All functions are variables
Set c To fn
Print 5.@c(3), @fn(5, 3)
 → 15 15
```

```vgr
# The expression can be compiled from a string
Accept op From stdin
Assert op in ["+", "-", "*", "/"]
Function dyn(x, y) -> Compile("(x {} y) + 10".Format(op))
```

Also see `Call` for details on invoking functions.
See `Return` for returning values and `Declare` for variable scoping.
"""
    # Echo only the declaration and signature (if present)
    if ctx.echo:
        # if count <= 2, then we don't have a list of params, just a name and statements
        # TODO: not sure if working corectly...
        #count = len(statement.children)
        ctx.echo_source(statement, statement.children[-1])#2 if count > 3 else 1])
    _create_function(ctx, statement, _new_user_function)

def execute_def_arrow(ctx: ExecContext, statement: Tree) -> None:
    """-documentation combined with Function-"""
    _create_function(ctx, statement, _new_arrow_function)

def execute_compile_arrow(ctx: ExecContext, statement: Tree) -> None:
    """-documentation combined with Function-"""
    _create_function(ctx, statement, _compile_arrow_function)

def _create_function(ctx: ExecContext, statement: Tree, ctor) -> None:
    is_const, cache_size = _read_function_def(ctx, statement.children[0])
    name_node = statement.children[1]
    var_path = get_writable_var_path(ctx, name_node)
    if is_const: assert_var_okay_for_const(ctx, name_node, var_path)
    new_value = ctor(ctx,
                statement,
                cache_size,
                create_param_list(ctx, statement.children[2]),
                statement.children[-1])
    if is_const:
        do_set_constant(ctx, new_value, *var_path)
    else:
        do_set(ctx, new_value, *var_path)

def _new_user_function(ctx: ExecContext, statement: Tree, cache_size: int, param_paths: tuple, body: Tree) -> Any:
    return UserFunction(statement, cache_size, param_paths, body.children)

def _new_arrow_function(ctx: ExecContext, statement: Tree, cache_size: int, param_paths: tuple, body: Tree) -> Any:
    return ArrowFunction(statement, cache_size, ctx.get_source(body), body, param_paths)

def _compile_arrow_function(ctx: ExecContext, statement: Tree, cache_size: int, param_paths: tuple, body: Tree) -> Any:
    return UserFunction.compile(ctx, statement, ctx.eval_expr(body), cache_size, param_paths)

def _read_function_def(ctx: ExecContext, definition: Tree) -> tuple:
    """returns (is_const, cache_size)"""
    is_const: bool = None
    is_cached: bool = None
    cache_size: int = None
    def _redundant(m): raise VgrRuntimeError(m, TypeError('Redundant modifier'))
    for modifier in definition.children:
        mod: str = modifier.data
        if mod == 'mod_const':
            if is_const: _redundant(modifier)
            is_const = True;
        elif mod == 'mod_cached':
            if is_cached: _redundant(modifier)
            is_cached = True
            if len(modifier.children):
                cache_size = poly_clamp(ctx.eval_to_int(bind_operations(modifier.children[0]), "Cache size", True), 0, MAX_CACHE_SIZE)
            else:
                cache_size = DEFAULT_CACHE_SIZE
        else:
            raise ValueError(f'{mod} not implemented')
    return (bool(is_const), cache_size if bool(is_cached) else 0)

@bound_ops("Call")
def execute_call(ctx: ExecContext, statement: Tree) -> None:
    """
**Invoke a function**

* Call *variable* [Giving *variable*]
* Call *variable* Using *expression*&hellip; [Giving *variable*]
* Call *variable*(*expression*&hellip;) [Giving *variable*]

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
