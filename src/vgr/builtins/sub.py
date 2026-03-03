from functools import reduce
from typing import Any

from .common import (
    bound_ops,
    empty_is_zero,
    get_operation,
    numeric_operations,
)

@bound_ops("-", "－")
def poly_sub(*args):
    """
**Subtraction operation**

* *x* - *y*
* *x* － *y*
* Sub(*x*, *y*&hellip;)
* *x*.Sub(*y*&hellip;)

| Type(x)    | Type(y)    | Returns       | Operation                 |
|------------|------------|---------------|---------------------------|
| integer    | integer    | integer       | x - y                     |
| integer    | float      | float         | x - y                     |
| integer    | string     | integer/float | x - ToNumber(y)           |
| float      | integer    | float         | x - y                     |
| float      | float      | float         | x - y                     |
| float      | string     | integer/float | x - ToNumber(y)           |
| string     | integer    | integer/float | ToNumber(x) - y           |
| string     | float      | integer/float | ToNumber(x) - y           |
| string     | string     | integer/float | ToNumber(x) - ToNumber(y) |
| list       | integer    | list          | Distributed               |
| list       | float      | list          | Distributed               |
| list       | string     | list          | Distributed               |
| dictionary | string     | dictionary    | Remove key y from x       |
| dictionary | list       | dictionary    | Remove keys in y from x   |
| dictionary | dictionary | dictionary    | Remove keys in y from x   |

A type error is raised on all other combinations

```vgr
None - None → None
None - 5 → -5
None - "5" → -5
5 - "7" → -2
"5" - 7 → -2
[1, 2] - 5 → [-4, -3]
{"a": 5, "b": 7, "c": 11} - "a" → {"b": 7, "c": 11}
{"a": 5, "b": 7, "c": 11} - ["a", "c"] → {"b": 7}
{"a": 5, "b": 7, "c": 11} - {"a": None, "b": None} → {"c": 11}
```
"""
    return reduce(_sub, args[1:], args[0]) if args else None

def _sub(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, sub_operations, numeric_operations)
    return operation(_sub, x, y) if operation else x - y

def remove_keys(x: dict, y: Any) -> dict:
    return {k:v for k, v in x.items() if k not in y}

sub_operations = {
    (str, str): lambda op, x, y: op(empty_is_zero(x), empty_is_zero(y)),
    (dict, int): lambda _, x, y: remove_keys(x, [y]),
    (dict, float): lambda _, x, y: remove_keys(x, [y]),
    (dict, str): lambda _, x, y:  remove_keys(x, [y]),
    (dict, list): lambda _, x, y: remove_keys(x, y),
    (dict, dict): lambda _, x, y:  remove_keys(x, list(y.keys())),
}
