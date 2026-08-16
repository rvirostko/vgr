from functools import reduce
from re import Pattern
from typing import Any
import itertools

from .common import (
    bound_ops,
    dist_x,
    dist_y,
    get_operation,
    str_to_int,
    X_None_Op,
    Y_None_Op,
)
from .type import poly_type
from .registry import builtin

@bound_ops("*", "×")
@builtin("Mul")
def poly_mul(*args):
    """
**Multiplication operation**

* *x* * *y*
* *x* × *y*
* Mul(*x*, *y*&hellip;)
* *x*.Mul(*y*&hellip;)

| Type(x) | Type(y) | Returns | Operation           |
|---------|---------|---------|---------------------|
| integer | integer | integer | x * y               |
| integer | float   | float   | x * y               |
| integer | string  | string  | String repetition   |
| integer | list    | list    | Distributed         |
| float   | integer | float   | x * y               |
| float   | float   | float   | x * y               |
| float   | string  | string  | String repetition   |
| float   | list    | list    | Distributed         |
| string  | integer | string  | String repetition   |
| string  | float   | string  | String repetition   |
| string  | string  | string  | String repetition   |
| string  | list    | list    | Distributed         |
| list    | integer | list    | Distributed         |
| list    | float   | list    | Distributed         |
| list    | string  | list    | Distributed         |
| list    | list    | list    | Cartesian product   |

A type error is raised on all other combinations

```vgr
None * None → None
None * 5 → None
None * "5" → None
5 * 5 → 25
5 * "7" → "77777"
"5" * 7 → "5555555"
[1, 2] * 5 → [5, 10]
5 * [1, 2] → [5, 10]
[1, 2] * [5, 7] → [[1, 5], [1, 7], [2, 5], [2, 7]]
```
"""
    return reduce(_mul, args[1:], args[0]) if args else None

def _mul(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, _MUL_OPERATIONS)
    try:
        return operation(_mul, x, y) if operation else x * y
    except TypeError as e:
        raise TypeError(f"Cannot multiply type {poly_type(x)!r} by {poly_type(y)!r}") from e

def _product_list(_, x: list, y: Any) -> list:
    return [list(p) for p in itertools.product(iter(x), iter(y))]

_MUL_OPERATIONS = {
    X_None_Op:        lambda _, _x, _y: None,
    Y_None_Op:        lambda _, _x, _y: None,
    (int, Pattern):   lambda _, x, y: x * y.pattern,
    (int, list):      dist_y,
    (float, str):     lambda _, x, y: int(x) * y,
    (float, list):    dist_y,
    (float, Pattern): lambda _, x, y: int(x) * y.pattern,
    (str, float):     lambda _, x, y: x * int(y),
    (str, str):       lambda _, x, y:  x * str_to_int(y),
    (str, list):      dist_y,
    (list, int):      dist_x,
    (list, float):    dist_x,
    (list, str):      dist_x,
    (list, list):     _product_list,
    (list, Pattern):  dist_x,
    (Pattern, int):   lambda _, x, y: x.pattern * y,
    (Pattern, float): lambda _, x, y: x.pattern * int(y),
    (Pattern, str):   lambda _, x, y:  x.pattern * str_to_int(y),
    (Pattern, list):  dist_y,
}
