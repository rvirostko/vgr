"""
"""

from lark import Tree

from data_dict import DataDictionary
from evaluate import eval_expr
from mathpak import poly_vadd, poly_vsub, poly_number, poly_mul, poly_div
from stmt_set import do_set

def execute_add_to(dd: DataDictionary, statement: Tree) -> None:
    """ Add one or more values to a variable

* ADD _expression_... TO _variable_ [;]

If the variable does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar opertion.
"""
    path = tuple(name.value for name in statement.children[-1].children)
    x = poly_number(dd.get_var_user(*path)) or 0
    args = tuple(poly_number(eval_expr(dd, expr)) or 0 for expr in statement.children[:-1])
    do_set(dd, poly_vadd(x, *args), *path)

def execute_add_giving(dd: DataDictionary, statement: Tree) -> None:
    """ Add two or more values and assign to a variable

* ADD _expression_... TO _expression_ GIVING __variable_ [;]

If the variable does not exist, it is created.
This is fundamentally an arithmetic, scalar opertion.
"""
    path = tuple(name.value for name in statement.children[-1].children)
    args = tuple(poly_number(eval_expr(dd, expr)) or 0 for expr in statement.children[:-1])
    do_set(dd, poly_vadd(*args), *path)

def execute_sub_from(dd: DataDictionary, statement: Tree) -> None:
    """ Subtract one or more values from a variable

* SUBTRACT _expression_... FROM _variable_ [;]

If the variable does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar opertion.
"""
    path = tuple(name.value for name in statement.children[-1].children)
    x = poly_number(dd.get_var_user(*path)) or 0
    args = tuple(poly_number(eval_expr(dd, expr)) or 0 for expr in statement.children[:-1])
    do_set(dd, poly_vsub(x, *args), *path)

def execute_sub_giving(dd: DataDictionary, statement: Tree) -> None:
    """ Subtract two or more values and assign to a variable

* SUBTRACT _expression_... FROM _expression_ GIVING _variable_ [;]

If the variable does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar opertion.
"""
    path = tuple(name.value for name in statement.children[-1].children)
    args = tuple(poly_number(eval_expr(dd, expr)) or 0 for expr in statement.children[:-1])
    do_set(dd, poly_vsub(args[-1], *args[:-1]), *path)

def execute_mul_by(dd: DataDictionary, statement: Tree) -> None:
    """ Multiply one number by another

* MULTIPLY _expression_ BY _variable_ [;]
* MULTIPLY _expression_ BY _expression_ GIVING _variable_ [;]

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

* DIVIDE _expression_ INTO _variable_ [;]
* DIVIDE _expression_ INTO _expression_ GIVING _variable_ [;]

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

* DIVIDE _expression_ BY _expression_ GIVING _variable_ [;]

The result of the division is placed into the variable.

If the variable does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar opertion.
"""
    path = tuple(name.value for name in statement.children[-1].children)
    args = tuple(poly_number(eval_expr(dd, expr)) or 0 for expr in statement.children[:-1])
    do_set(dd, poly_div(*args), *path)
