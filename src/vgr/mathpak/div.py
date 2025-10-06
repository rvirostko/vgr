from functools import reduce
from typing import Any

from .common import (
    bound_ops,
    empty_is_zero,
    numeric_operations,
    get_operation,
)

@bound_ops("/", "÷")
def poly_div(x: Any, *args):
    """
**Division operation**

* _x_ / _y_
* _x_ ÷ _y_
* Div(_x_, _y_...)
* _x_.Div(_y_...)

| x     | y     | returns | operation                 |
|-------|-------|---------|---------------------------|
| int   | int   | float   | x / y                     |
| int   | float | float   | x / y                     |
| int   | str   | float   | x / ToNumber(y)           |
| float | int   | float   | x / y                     |
| float | float | float   | x / y                     |
| float | str   | float   | x / ToNumber(y)           |
| str   | int   | float   | ToNumber(x) / y           |
| str   | float | float   | ToNumber(x) / y           |
| str   | str   | float   | ToNumber(x) / ToNumber(y) |
| list  | int   | list    | distributive              |
| list  | float | list    | distributive              |
| list  | str   | list    | distributive              |

TypeError raised on all other combinations

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
    return reduce(_div, args, x)

def _div(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, div_operations, numeric_operations)
    return operation(_div, x, y) if operation else x / y

def poly_fdiv(x: Any, *args):
    """
**Floor division operation**

* FloorDiv(_x_, _y_...)
* _x_.FloorDiv(_y_...)

Floor division returns the largest integer less than
or equal to the result of the division.

| x     | y     | returns   | operation                    |
|-------|-------|-----------|------------------------------|
| int   | int   | int       | x fdiv y                     |
| int   | float | int/float | x fdiv y                     |
| int   | str   | int/float | x fdiv ToNumber(y)           |
| float | int   | float     | x fdiv y                     |
| float | float | float     | x fdiv y                     |
| float | str   | float     | x fdiv ToNumber(y)           |
| str   | int   | int/float | ToNumber(x) fdiv y           |
| str   | float | float     | ToNumber(x) fdiv y           |
| str   | str   | int/float | ToNumber(x) fdiv ToNumber(y) |
| list  | int   | list      | distributive                 |
| list  | float | list      | distributive                 |
| list  | str   | list      | distributive                 |

TypeError raised on all other combinations

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
    return reduce(_fdiv, args, x)

def _fdiv(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, div_operations, numeric_operations)
    return operation(_fdiv, x, y) if operation else x // y

def poly_divmod(x: Any, y: Any) -> Any:
    """
**Division/modulo operation**

* DivMod(_x_, _y_)
* _x_.DivMod(_y_)

Returns a two item list of [_x_ fdiv _y_, _x_ % _y_]

| x     | y     | returns | operation                         |
|-------|-------|---------|-----------------------------------|
| int   | int   | list    | x divmod by y                     |
| int   | float | list    | x divmod by y                     |
| int   | str   | list    | x divmod by ToNumber(y)           |
| float | int   | list    | x divmod by y                     |
| float | float | list    | x divmod by y                     |
| float | str   | list    | x divmod by ToNumber(y)           |
| str   | int   | list    | ToNumber(x) divmod by y           |
| str   | float | list    | ToNumber(x) divmod by y           |
| str   | str   | list    | ToNumber(x) divmod by ToNumber(y) |
| list  | int   | list    | distributive                      |
| list  | float | list    | distributive                      |
| list  | str   | list    | distributive                      |

TypeError raised on all other combinations

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
    operation = get_operation(x, y, div_operations, numeric_operations)
    return operation(poly_divmod, x, y) if operation else list(divmod(x, y))

div_operations = {
    (str, str): lambda op, x, y: op(empty_is_zero(x), empty_is_zero(y)),
}
