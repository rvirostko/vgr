"""
Procedure implementations
"""

from lark import Tree

from evaluate import get_writable_var_path, create_param_list, do_set
from exec_context import ExecContext
from mathpak import bound_ops
from tags import control_statement
from user_callable import UserProcedure

@control_statement
@bound_ops("Procedure")
def execute_def_procedure(ctx: ExecContext, statement: Tree) -> None:
    """
**Create a reusable procedure**
"""
    ctx.echo_source(statement, statement.children[2])
    var_path = get_writable_var_path(ctx, statement.children[0])
    param_paths = create_param_list(ctx, statement.children[1])
    do_set(ctx, UserProcedure(param_paths, statement.children[-1].children), *var_path)

@bound_ops("Call")
def execute_call(ctx: ExecContext, statement: Tree) -> None:
    pass
