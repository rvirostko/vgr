from functools import reduce
from typing import Any

from .common import bound_ops, get_operation, numeric_operations, dist_x, dist_y, str_to_number

@bound_ops("+", "＋")
def poly_add(x: Any, *args):
    """
**Addition/concatenation operation**

* *x* + *y*
* *x* ＋ *y*
* Add(*x*, *y*&hellip;)
* *x*.Add(*y*&hellip;)

| x     | y     | returns   | operation                |
|-------|-------|-----------|--------------------------|
| int   | int   | int       | x + y                    |
| int   | float | float     | x + y                    |
| int   | str   | int/float | x + ToNumber(y)          |
| int   | list  | list      | distributive             |
| float | int   | int/float | x + ToFloat(y)           |
| float | float | float     | x + y                    |
| float | str   | int/float | x + ToNumber(y)          |
| float | list  | list      | distributive             |
| str   | int   | str       | concat x and ToString(y) |
| str   | float | str       | concat x and ToString(y) |
| str   | str   | str       | concat x and y           |
| str   | list  | list      | distributive             |
| list  | int   | list      | distributive             |
| list  | float | list      | distributive             |
| list  | str   | list      | distributive             |
| list  | list  | list      | union of lists           |
| dict  | dict  | dict      | union of dicts           |

A type error is raised on all other combinations

```vgr
None + None → None
None + 5 → 5
None + "5" → "5"
5 + "7" → 12
"5" + 7 → "57"
[1, 2] + 5 → [6, 7]
5 + [1, 2] → [6, 7]
[1, 2] + [5] → [1, 2, 5]
{"a": 5} + {"b": 6} → {"a": 5, "b": 6}
```

Also see `ToNumber()` and `ToString()` for conversion details

"""
    return reduce(_add, args, x)

def _add(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, _add_operations, numeric_operations)
    return operation(_add, x, y) if operation else x + y

_add_operations = {
    (int, list): dist_y,
    (int, tuple): dist_y,
    (float, list): dist_y,
    (float, tuple): dist_y,
    (str, str): lambda _, x, y: x + y,
    (str, int): lambda _, x, y: x + str(y),
    (str, float): lambda _, x, y: x + str(y),
    (str, list): dist_y,
    (str, tuple): dist_y,
    (list, int): dist_x,
    (list, float): dist_x,
    (tuple, int): dist_x,
    (tuple, float): dist_x,
    (list, tuple): lambda _, x, y: x + list(y),
    (tuple, list): lambda _, x, y: x + tuple(y),
    (dict, dict): lambda _, x, y: {**x, **y}
}

def poly_sum(x: Any, *args) -> Any:
    """
**Recursively sum lists of numbers**

* Sum(*values*&hellip;)
* *values*.Sum()
* *values*.Sum(*values*&hellip;)

If a *values* is `None` it is treated as a zero.
String values are converted to numbers when possible.

While similar to `Add()`, `Sum()` is not distributed over
lists, but instead sums their content.
Additionally, if strings cannot be converted to a number
they are ignored.

```vgr
None.Sum() → 0
5.Sum(None) → 5
5.Sum(7) → 12
5.Sum(" 7.0") → 12
[1, 2, 3, 5].Sum() → 11
0.Sum([1, 2], [3, 5]) → 11
True.Sum(True, None, True) → 3
["cat", "dog", "fish"].Sum() → 0
```
"""
    return _sum(x) + sum(_sum(arg) for arg in args)

def _sum(obj):
    if obj is None: return 0
    if isinstance(obj, (int, float)): return obj
    if isinstance(obj, str):
        try:
            return str_to_number(obj) or 0
        except ValueError:
            pass
    if isinstance(obj, (list, tuple)): return sum(_sum(item) for item in obj)
    return 0
