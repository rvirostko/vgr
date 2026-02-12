"""
Bitwise shift left and right.
"""

from functools import reduce
from typing import Any

from .common import (
    bound_ops,
    dist_x,
    empty_is_zero,
    get_operation,
    matching_default,
    X_None_Op,
    Y_None_Op,
)

@bound_ops("<<")
def poly_shl(x: Any, *args) -> Any:
    """
**Bitwise Shift Left operation**

* *x* << *y*
* LeftShift(*x*, *y*&hellip;)
* *x*.LeftShift(*y*&hellip;)

The values of both *x* and *y* are converted to
integers to perform the operation.

| x     | y     | returns | operation            |
|-------|-------|---------|----------------------|
| int   | int   | int     | x << y               |
| int   | float | int     | x << ToInteger(y)    |
| int   | str   | int     | x << ToInteger(y)    |
| float | int   | int     | ToInteger(x) << y    |
| float | float | int     | ToInteger(x) << y    |
| float | str   | int     | ToInteger(x) << ToInteger(y) |
| str   | int   | int     | ToInteger(x) << y    |
| str   | float | int     | ToInteger(x) << y    |
| str   | str   | int     | ToInteger(x) << ToInteger(y) |
| list  | int   | list    | distributed          |
| list  | float | list    | distributed          |
| list  | str   | list    | distributed          |

A type error is raised on all other combinations

```vgr
None << None → None
None << 2 → 0
None << "2" → 0
5 << " 2" → 20
"5" << "2.0" → 20
[5, 7] << 2 → [20, 28]
```

Also see `RightShift()`
"""
    return reduce(_shl, args, x)

@bound_ops(">>")
def poly_shr(x: Any, *args):
    """
**Bitwise Shift Right operation**

* *x* >> *y*
* RightShift(*x*, *y*&hellip;)
* *x*.RightShift(*y*&hellip;)

The values of both *x* and *y* are converted to
integers to perform the operation.

| x     | y     | returns | operation            |
|-------|-------|---------|----------------------|
| int   | int   | int     | x >> y               |
| int   | float | int     | x >> ToInteger(y)    |
| int   | str   | int     | x >> ToInteger(y)    |
| float | int   | int     | ToInteger(x) >> y    |
| float | float | int     | ToInteger(x) >> ToInteger(y) |
| float | str   | int     | ToInteger(x) >> ToInteger(y) |
| str   | int   | int     | ToInteger(x) >> y    |
| str   | float | int     | ToInteger(x) >> ToInteger(y) |
| str   | str   | int     | ToInteger(x) >> ToInteger(y) |
| list  | int   | list    | distributed          |
| list  | float | list    | distributed          |
| list  | str   | list    | distributed          |

A type error is raised on all other combinations

```vgr
None >> None → None
None >> 2 → 0
None >> "2" → 0
5 >> " 2" → 1
"5" >> "2.0" → 1
[5, 7] >> 2 → [1, 1]
```

Also see `LeftShift()`
"""
    return reduce(_shr, args, x)

def _shl(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, shift_operations)
    return operation(_shl, x, y) if operation else x << y

def _shr(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, shift_operations)
    return operation(_shr, x, y) if operation else x >> y

shift_operations = {
    X_None_Op: lambda op, _, y: None if y is None else op(matching_default(y), y),
    Y_None_Op: lambda op, x, _: op(x, matching_default(x)),
    (int, str): lambda op, x, y: op(x, empty_is_zero(y)),
    (int, float): lambda op, x, y: op(x, int(y)),
    (float, int): lambda op, x, y: op(int(x), y),
    (float, float): lambda op, x, y: op(int(x), int(y)),
    (float, str): lambda op, x, y: op(int(x), empty_is_zero(y)),
    (str, int): lambda op, x, y: op(empty_is_zero(x), y),
    (str, float): lambda op, x, y: op(empty_is_zero(x), int(y)),
    (str, str): lambda op, x, y: op(empty_is_zero(x), empty_is_zero(y)),
    (list, int): dist_x,
    (list, float): lambda op, x, y: dist_x(op, x, int(y)),
    (list, str): lambda op, x, y: dist_x(op, x, empty_is_zero(y)),
}
