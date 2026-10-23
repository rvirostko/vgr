from functools import reduce
from typing import Any
import itertools
import math

from .common import (
    bound_ops,
    dist_x,
    dist_y,
    get_operation,
    str_to_int,
    str_to_number,
    X_None_Op,
    Y_None_Op,
)
from .type import poly_type
from .registry import builtin
from .vpattern import VPattern

#TODO circular import issue! from ..user_callable import VgrCallable

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
| string  | float   | string  | ToInteger(x) * ToInteger(y) |
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
    if x is None and y is None: return None
    operation = get_operation(x, y, _MUL_OPERATIONS)
    try:
        if operation is not None: return operation(_mul, x, y)
        return 0 if (math.isinf(x) and y == 0) or (math.isinf(y) and x == 0) else x * y
    except TypeError as e:
        raise TypeError(f"Cannot multiply type {poly_type(x)!r} by {poly_type(y)!r}") from e

def _product_list(_, x: list, y: Any) -> list:
    return [list(p) for p in itertools.product(iter(x), iter(y))]

def _mul_str_str(op, x: Any, y: Any) -> Any:
    if (x1 := str_to_number(x)) is None: raise ValueError(f"Cannot convert {x!r} to a number")
    if (y1 := str_to_number(y)) is None: raise ValueError(f"Cannot convert {y!r} to a number")
    return op(x1, y1)

def _copy_count(x: Any) -> int:
    if isinstance(x, float):
        if x == math.inf: raise ValueError("Cannot create infinite copies")
        x = 0 if math.isnan(x) else int(x)
    else:
        if isinstance(x, str): x = str_to_int(x)
    return max(0, x)

_MUL_OPERATIONS = {
    X_None_Op:            lambda op, _x, y: op(0, y),            # None as zero
    Y_None_Op:            lambda op, x, _y: op(x, 0),            # None as zero
    (int, str):           lambda _, x, y: y * _copy_count(x),    # x copies of string y
    (int, VPattern):      lambda _, x, y: [y] * x,               # x copies of pattern y
#    (int, VgrCallable):   lambda _, x, y: [y] * x,               # x copies of function y
    (int, list):          dist_y,
    (float, str):         lambda _, x, y: y * _copy_count(x),    # x copies of string y
    (float, list):        dist_y,
    (float, VPattern):    lambda _, x, y: [y] * _copy_count(x),  # x copies of pattern y
#    (float, VgrCallable): lambda _, x, y: [y] * _copy_count(x),  # x copies of function y
    (str, int):           lambda _, x, y: x * _copy_count(y),    # y copies of string x
    (str, float):         lambda _, x, y: x * _copy_count(y),    # y copies of string x
    (str, str):           _mul_str_str,
    (str, list):          dist_y,
    (list, int):          dist_x,
    (list, float):        dist_x,
    (list, str):          dist_x,
    (list, list):         _product_list,
    (list, VPattern):     dist_x,
#    (list, VgrCallable):  dist_x,
    (VPattern, int):      lambda _, x, y: [x] * _copy_count(y),   # y copies of pattern x
    (VPattern, float):    lambda _, x, y: [x] * _copy_count(y),   # y copies of pattern x
    (VPattern, list):     dist_y,
#    (VgrCallable, int):   lambda _, x, y: [x] * _copy_count(y),   # y copies of function x
#    (VgrCallable, float): lambda _, x, y: [x] * _copy_count(y),   # y copies of function x
#    (VgrCallable, list):  dist_y,
}
