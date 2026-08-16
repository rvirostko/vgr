from functools import reduce
from re import Pattern
from typing import Any

from .common import (
    bound_ops,
    empty_is_zero,
    get_operation,
    numeric_operations,
)
from .dict import poly_remove_key
from .type import poly_type
from .registry import builtin

@bound_ops("-", "－")
@builtin("Sub")
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
| dictionary | list       | dictionary    | Remove key path y from x  |
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
    operation = get_operation(x, y, _SUB_OPERATIONS, numeric_operations)
    try:
        return operation(_sub, x, y) if operation else x - y
    except TypeError as e:
        raise TypeError(f"Cannot subtract type {poly_type(y)!r} from {poly_type(x)!r}") from e

def _remove_key(_op, x: dict, path: Any) -> dict:
    """Remove a key using a path"""
    return poly_remove_key(x, path)

def _remove_keys(_op, x: dict, y: dict) -> dict:
    """Remove all the keys present in y from x (disjunction)"""
    keys = list(y.keys())
    return {k:v for k, v in x.items() if k not in keys}

_SUB_OPERATIONS = {
    (str, str):      lambda op, x, y: op(empty_is_zero(x), empty_is_zero(y)),
    (dict, bool):    _remove_key,
    (dict, int):     _remove_key,
    (dict, float):   _remove_key,
    (dict, str):     _remove_key,
    (dict, list):    _remove_key,
    (dict, dict):    _remove_keys,
    (dict, Pattern): lambda op, x, y: _remove_key(op, x, y.pattern)
}
