from functools import reduce
from re import Pattern
from typing import Any

from .common import (
    bound_ops,
    get_operation,
    numeric_operations,
    dist_x,
    dist_y,
    str_to_number,
)
from .dict import poly_set_key_value
from .type import poly_type

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
    try:
        return operation(_add, x, y) if operation else x + y
    except TypeError as e:
        raise TypeError(f"Cannot add types {poly_type(x)!r} and {poly_type(y)!r}") from e

def _add_key(_op, d: dict, key: Any) -> dict: return poly_set_key_value(d, key)
def op_pattern_str(op, pattern: Pattern, value: Any) -> str:
    """Convert both values to a string and invoke op()"""
    return op(pattern.pattern, str(value))
def op_str_pattern(op, value: Any, pattern: Pattern) -> str:
    """Convert both values to a string and invoke op()"""
    return op(str(value), pattern.pattern)
def op_str_str(op, x: Any, y: Any) -> str:
    """Convert both values to a string and invoke op()"""
    return op(str(x), str(y))

_add_operations = {
    (bool, Pattern):    op_str_pattern,
    (int, list):        dist_y,
    (int, Pattern):     op_str_pattern,
    (float, list):      dist_y,
    (float, Pattern):   op_str_pattern,
    (str, bool):        op_str_str,
    (str, int):         op_str_str,
    (str, float):       op_str_str,
    (str, str):         lambda _, x, y: x + y,
    (str, list):        dist_y,
    (str, Pattern):     op_str_pattern,
    (list, bool):       dist_x,
    (list, int):        dist_x,
    (list, float):      dist_x,
    (list, Pattern):    lambda op, x, y: dist_x(op, x, y.pattern),
    (dict, bool):       _add_key,
    (dict, int):        _add_key,
    (dict, float):      _add_key,
    (dict, str):        _add_key,
    (dict, list):       _add_key,
    (dict, dict):       lambda _, x, y: {**x, **y},
    (dict, Pattern):    lambda op, x, y: _add_key(op, y, x.pattern),
    (Pattern, bool):    op_pattern_str,
    (Pattern, int):     op_pattern_str,
    (Pattern, float):   op_pattern_str,
    (Pattern, str):     op_pattern_str,
    (Pattern, list):    lambda op, x, y: dist_y(op, x.pattern, y),
    (Pattern, Pattern): lambda _, x, y: x.pattern + y.pattern,
}

def poly_sum(*args) -> Any:
    """
**Recursively sums lists of numbers**

* Sum(*values*&hellip;)
* *values*.Sum()
* *values*.Sum(*values*&hellip;)

If a *values* is `None` it is treated as a zero.
String values are converted to numbers when possible.

While similar to `Add()`, `Sum()` is not distributed over
lists, but instead sums their content.
Additionally, if strings, or other types, cannot be converted to a number
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
    # NB: _num_value should prevent any TypeError in the addition
    return _num_value(args[0]) + sum(_num_value(arg) for arg in args[1:]) if args else 0

def _num_value(obj):
    if obj is None: return 0
    if isinstance(obj, (int, float)): return obj
    # Likely "unuseful" but is consistent
    if isinstance(obj, Pattern): obj = obj.pattern
    if isinstance(obj, str):
        try:
            return str_to_number(obj) or 0
        except ValueError:
            pass
    if isinstance(obj, list): return sum(_num_value(item) for item in obj)
    return 0
