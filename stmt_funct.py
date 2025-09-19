"""
User defined function implementations
"""

from lark import Tree

from evaluate import do_set, get_writable_var_path, create_param_list
from exec_context import ExecContext
from mathpak import bound_ops
from tags import control_statement
from user_callable import UserFunction

@control_statement
@bound_ops("Function")
def execute_def_function(ctx: ExecContext, statement: Tree) -> None:
    """
**Define a function**

TODO
"""
    ctx.echo_source(statement, statement.children[2])
    var_path = get_writable_var_path(ctx, statement.children[0])
    param_paths = create_param_list(ctx, statement.children[1])
    do_set(ctx, UserFunction(param_paths, statement.children[-1].children), *var_path)
