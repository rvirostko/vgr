"""
User defined function implementations
"""

from lark import Tree

from evaluate import do_set, get_writable_var_path, create_param_list, get_function
from exec_context import ExecContext
from mathpak import bound_ops
from tags import control_statement
from user_callable import UserFunction

@control_statement
@bound_ops("Function")
def execute_def_function(ctx: ExecContext, statement: Tree) -> None:
    """
**Define a function**

* [Define] Function _variable_ [:]
    _statement_...
  End [;]
* [Define] Function _variable_(_param_...) [:]
    _statement_...
  End [;]

TODO
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

* Call _variable_ [Giving _variable_] [;]
* Call _variable_(_expression_...) [Giving _variable_] [;]

TODO
"""
    fn = get_function(ctx, statement)
    values = [ctx.eval_expr(arg) for arg in statement.children[1:]]
    UserFunction.invoke(ctx, fn, values)

def execute_call_giving(ctx: ExecContext, statement: Tree) -> None:
    """*doc merged with call*"""
    fn = get_function(ctx, statement)
    var_path = get_writable_var_path(ctx, statement.children[-1])
    values = [ctx.eval_expr(arg) for arg in statement.children[1:-1]]
    do_set(ctx, UserFunction.invoke(ctx, fn, values), *var_path)
