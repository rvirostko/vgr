from functools import reduce
from typing import Any

from .common import bound_ops, get_operation, numeric_operations, dist_x, dist_y, str_to_number

@bound_ops("+", "＋")
def poly_add(*args):
    """
**Addition/concatenation operation**

* *x* + *y*
* *x* ＋ *y*
* Add(*x*, *y*&hellip;)
* *x*.Add(*y*&hellip;)

| Type(x)    | Type(y)    | Returns       | Operation                |
|------------|------------|---------------|--------------------------|
| integer    | integer    | integer       | x + y                    |
| integer    | float      | float         | x + y                    |
| integer    | string     | integer/float | x + ToNumber(y)          |
| integer    | list       | list          | Distributed              |
| float      | integer    | integer/float | x + ToFloat(y)           |
| float      | float      | float         | x + y                    |
| float      | string     | integer/float | x + ToNumber(y)          |
| float      | string     | float         | x + ToNumber(y)          |
| float      | list       | list          | Distributed              |
| string     | integer    | string        | concat x and ToString(y) |
| string     | float      | string        | concat x and ToString(y) |
| string     | string     | string        | concat x and y           |
| string     | list       | list          | Distributed              |
| list       | integer    | list          | Distributed              |
| list       | float      | list          | Distributed              |
| list       | string     | list          | Distributed              |
| list       | list       | list          | union of lists           |
| dictionary | dictionary | dictionary    | union of dicts           |

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
    return reduce(_add, args[1:], args[0]) if args else None

def _add(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, _add_operations, numeric_operations)
    return operation(_add, x, y) if operation else x + y

_add_operations = {
    (int, list): dist_y,
    (float, list): dist_y,
    (str, str): lambda _, x, y: x + y,
    (str, int): lambda _, x, y: x + str(y),
    (str, bool): lambda _, x, y: x + str(y),
    (str, float): lambda _, x, y: x + str(y),
    (str, list): dist_y,
    (list, int): dist_x,
    (list, float): dist_x,
    (dict, dict): lambda _, x, y: {**x, **y}
}

def poly_sum(*args) -> Any:
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
    return _sum(args[0]) + sum(_sum(arg) for arg in args[1:]) if args else 0

def _sum(obj):
    if obj is None: return 0
    if isinstance(obj, (int, float)): return obj
    if isinstance(obj, str):
        try:
            return str_to_number(obj) or 0
        except ValueError:
            pass
    if isinstance(obj, list): return sum(_sum(item) for item in obj)
    return 0
