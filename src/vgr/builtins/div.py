from functools import reduce
from typing import Any
from math import nan

from .common import (
    bound_ops,
    empty_is_zero,
    numeric_operations,
    get_operation,
)
from .type import poly_type
from .registry import builtin

@bound_ops("/", "÷")
@builtin("Div")
def poly_div(*args):
    """
**Division operation**

* *x* / *y*
* *x* ÷ *y*
* Div(*x*, *y*&hellip;)
* *x*.Div(*y*&hellip;)

| Type(x) | Type(y) | Returns | Operation                 |
|---------|---------|---------|---------------------------|
| integer | integer | float   | x / y                     |
| integer | float   | float   | x / y                     |
| integer | string  | float   | x / ToNumber(y)           |
| float   | integer | float   | x / y                     |
| float   | float   | float   | x / y                     |
| float   | string  | float   | x / ToNumber(y)           |
| string  | integer | float   | ToNumber(x) / y           |
| string  | float   | float   | ToNumber(x) / y           |
| string  | string  | float   | ToNumber(x) / ToNumber(y) |
| list    | integer | list    | Distributed               |
| list    | float   | list    | Distributed               |
| list    | string  | list    | Distributed               |

A type error is raised on all other combinations

```vgr
None / None → None
None / 2 → 0.0
None / "2" → 0.0
5 / " 2" → 2.5
"5" / "2.0" → 2.5
[5, 7] / 2 → [2.5, 3.5]
```

Also see `FloorDiv()` and `DivMod()`
"""
    return reduce(_div, args[1:], args[0]) if args else None

def _div(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, _DIV_OPERATIONS, numeric_operations)
    try:
        return operation(_div, x, y) if operation else x / y
    except TypeError as e:
        raise TypeError(f"Cannot perform division on type {poly_type(x)!r} with {poly_type(y)!r}") from e
    except ZeroDivisionError:
        return nan

@builtin("FloorDiv")
def poly_floor_div(*args):
    """
**Floor division operation**

* FloorDiv(*x*, *y*&hellip;)
* *x*.FloorDiv(*y*&hellip;)

Floor division returns the largest integer less than
or equal to the result of the division.

| Type(x) | Type(y) | Returns       | Operation                    |
|---------|---------|---------------|------------------------------|
| integer | integer | integer       | x fdiv y                     |
| integer | float   | integer/float | x fdiv y                     |
| integer | string  | integer/float | x fdiv ToNumber(y)           |
| float   | integer | float         | x fdiv y                     |
| float   | float   | float         | x fdiv y                     |
| float   | string  | float         | x fdiv ToNumber(y)           |
| string  | integer | integer/float | ToNumber(x) fdiv y           |
| string  | float   | float         | ToNumber(x) fdiv y           |
| string  | string  | integer/float | ToNumber(x) fdiv ToNumber(y) |
| list    | integer | list          | Distributed                  |
| list    | float   | list          | Distributed                  |
| list    | string  | list          | Distributed                  |

A type error is raised on all other combinations

```vgr
None.FloorDiv(None) → None
None.FloorDiv(2) → 0
None.FloorDiv("2") → 0
5.FloorDiv(" 2") → 2
"5".FloorDiv("2.0") → 2
[5, 7].FloorDiv(2) → [2, 3]
```

Also `Div()` and `DivMod()`
"""
    return reduce(_fdiv, args[1:], args[0]) if args else None

def _fdiv(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, _DIV_OPERATIONS, numeric_operations)
    try:
        return operation(_fdiv, x, y) if operation else x // y
    except TypeError as e:
        raise TypeError(f"Cannot perform division on type {poly_type(x)!r} with {poly_type(y)!r}") from e
    except ZeroDivisionError:
        return nan

@builtin("DivMod")
def poly_divmod(x: Any=None, y: Any=1) -> Any:
    """
**Division/modulo operation**

* DivMod(*x*, *y*)
* *x*.DivMod(*y*)

Returns a two item list of [*x* fdiv *y*, *x* % *y*]

| Type(x) | Type(y) | Returns | Operation                         |
|---------|---------|---------|-----------------------------------|
| integer | integer | list    | x divmod by y                     |
| integer | float   | list    | x divmod by y                     |
| integer | string  | list    | x divmod by ToNumber(y)           |
| float   | integer | list    | x divmod by y                     |
| float   | float   | list    | x divmod by y                     |
| float   | string  | list    | x divmod by ToNumber(y)           |
| string  | integer | list    | ToNumber(x) divmod by y           |
| string  | float   | list    | ToNumber(x) divmod by y           |
| string  | string  | list    | ToNumber(x) divmod by ToNumber(y) |
| list    | integer | list    | Distributed                       |
| list    | float   | list    | Distributed                       |
| list    | string  | list    | Distributed                       |

A type error is raised on all other combinations

```vgr
None.DivMod(None) → None
None.DivMod(2) → [0, 0]
None.DivMod("2") → [0, 0]
5.DivMod(" 2") → [2, 1]
"5".DivMod("2.0") → [2, 1]
[5, 7].DivMod(2) → [[2, 1], [3, 1]]
```

Also `Div()` and `Mod()`
"""
    operation = get_operation(x, y, _DIV_OPERATIONS, numeric_operations)
    try:
        return operation(poly_divmod, x, y) if operation else list(divmod(x, y))
    except TypeError as e:
        raise TypeError(f"Cannot perform div-modulo on type {poly_type(x)!r} with {poly_type(y)!r}") from e
    except ZeroDivisionError:
        return nan

_DIV_OPERATIONS = {
    (str, str): lambda op, x, y: op(empty_is_zero(x), empty_is_zero(y)),
}
