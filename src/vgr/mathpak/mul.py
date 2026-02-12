from functools import reduce
from typing import Any
import itertools

from .common import bound_ops, dist_x, dist_y, X_None_Op, Y_None_Op, get_operation, str_to_int

@bound_ops("*", "×")
def poly_mul(x: Any, *args):
    """
**Multiplication operation**

* *x* * *y*
* *x* × *y*
* Mul(*x*, *y*&hellip;)
* *x*.Mul(*y*&hellip;)

| x     | y     | returns | operation           |
|-------|-------|---------|---------------------|
| int   | int   | int     | x * y               |
| int   | float | float   | x * y               |
| int   | str   | str     | string repetition   |
| int   | list  | list    | distributive        |
| float | int   | float   | x * y               |
| float | float | float   | x * y               |
| float | str   | str     | string repetition   |
| float | list  | list    | distributive        |
| str   | int   | str     | string repetition   |
| str   | float | str     | string repetition   |
| str   | str   | str     | string repetition   |
| str   | list  | list    | distributive        |
| list  | int   | list    | distributive        |
| list  | float | list    | distributive        |
| list  | str   | list    | distributive        |
| list  | list  | list    | cartesian product   |

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
    return reduce(_mul, args, x)

def _mul(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, mul_operations)
    return operation(_mul, x, y) if operation else x * y

def product_list(_, x: list, y: Any) -> list:
    return [list(p) for p in itertools.product(iter(x), iter(y))]

mul_operations = {
    X_None_Op: lambda _, _x, _y: None,
    Y_None_Op: lambda _, _x, _y: None,
    (int, list): dist_y,
    (float, str): lambda _, x, y: int(x) * y,
    (float, list): dist_y,
    (str, float): lambda _, x, y: x * int(y),
    (str, str): lambda _, x, y:  x * str_to_int(y),
    (str, list): dist_y,
    (list, int): dist_x,
    (list, float): dist_x,
    (list, str): dist_x,
    (list, list): product_list,
}
