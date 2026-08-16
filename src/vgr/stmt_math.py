
from lark import Tree

from .builtins import (
    bound_ops,
    poly_add,
    poly_div,
    poly_mul,
    poly_to_number,
    poly_sub,
)
from .evaluate import get_writable_var_path
from .exec_context import ExecContext
from .stmt_set import do_set

@bound_ops("Add")
def execute_add_to(ctx: ExecContext, statement: Tree) -> None:
    """
**Add one or more values to a variable**

* Add *expression*&hellip; To *variable*
* Add *expression*&hellip; To *expression* Giving *variable*

If *variable* does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar operation.

```vgr
Set a To 5
Set b To 7
Set c To Zero

Add a To c
Exhibit c
c = 5

Add a, b To c
Exhibit c
c = 17

Add a, b To c Giving d
Exhibit c, d
c = 17
d = 29
```

Also see `Add()` and `Sum()`, `+`, and `Set`
"""
    var_path = get_writable_var_path(ctx, statement.children[-1])
    x = poly_to_number(ctx.get_var(*var_path)) or 0
    args = list(poly_to_number(ctx.eval_expr(expr)) or 0 for expr in statement.children[:-1])
    do_set(ctx, poly_add(x, *args), *var_path)

# Doc added to add_to
def execute_add_giving(ctx: ExecContext, statement: Tree) -> None:
    var_path = get_writable_var_path(ctx, statement.children[-1])
    args = list(poly_to_number(ctx.eval_expr(expr)) or 0 for expr in statement.children[:-1])
    do_set(ctx, poly_add(*args), *var_path)

@bound_ops("Subtract")
def execute_sub_from(ctx: ExecContext, statement: Tree) -> None:
    """
**Subtract one or more values from a variable**

* Subtract *expression*&hellip; From *variable*
* Subtract *expression*&hellip; From *expression* Giving *variable*

If *variable* does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar operation.

```vgr
Assign 5 To a
Assign 7 To b
Assign 30 To c

Subtract a From c
Exhibit c
c = 25

Subtract a, b From c
Exhibit c
c = 13

Subtract a, b From c Giving d
Exhibit c, d
c = 13
d = 1
```

Also see `Sub()`, `-`, and `Set`
"""
    var_path = get_writable_var_path(ctx, statement.children[-1])
    x = poly_to_number(ctx.get_var(*var_path)) or 0
    args = list(poly_to_number(ctx.eval_expr(expr)) or 0 for expr in statement.children[:-1])
    do_set(ctx, poly_sub(x, *args), *var_path)

# Doc added to sub_from
def execute_sub_giving(ctx: ExecContext, statement: Tree) -> None:
    var_path = get_writable_var_path(ctx, statement.children[-1])
    args = list(poly_to_number(ctx.eval_expr(expr)) or 0 for expr in statement.children[:-1])
    do_set(ctx, poly_sub(args[-1], *args[:-1]), *var_path)

@bound_ops("Multipy")
def execute_mul_by(ctx: ExecContext, statement: Tree) -> None:
    """
**Multiply one number by another**

* Multiply *variable* By *expression*&hellip;

The value of *variable* is multiplied by the results of *expression*.

If *variable* does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar operation.

```vgr
Set a To 5
Set b To 11

Multiply a By b
Exhibit a, b
a = 55
b = 11
```

Also see `Mul()`, `*`, and `Set`
"""
    var_path = get_writable_var_path(ctx, statement.children[0])
    x = poly_to_number(ctx.get_var(*var_path)) or 0
    args = list(poly_to_number(ctx.eval_expr(expr)) or 0 for expr in statement.children[1:])
    value = poly_mul(x, *args)
    do_set(ctx, value, *var_path)

@bound_ops("Divide")
def execute_div_by(ctx: ExecContext, statement: Tree) -> None:
    """
**Divide one number by another**

* Divide *variable* By *expression*&hellip;

The value of *variable* is divided by the results of *expression*.

If *variable* does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar operation.

```vgr
Set a To 2
Set b To 5
Divide a By b
Exhibit a, b
a = .4
b = 5
```

Also see `Div()`, `/`, and `Set`
"""
    var_path = get_writable_var_path(ctx, statement.children[0])
    x = poly_to_number(ctx.get_var(*var_path)) or 0
    args = list(poly_to_number(ctx.eval_expr(expr)) or 0 for expr in statement.children[1:])
    value = poly_div(x, *args)
    do_set(ctx, value, *var_path)
