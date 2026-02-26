"""
Modulo operation.
"""

from functools import reduce
from typing import Any

from .common import (
    bound_ops,
    empty_is_zero,
    get_operation,
    numeric_operations,
)

@bound_ops("%")
def poly_mod(*args):
    """
**Modulo operation**

* *x* % *y*
* Mod(*x*, *y*&hellip;)
* *x*.Mod(*y*&hellip;)

| Type(x) | Type(y) | Returns | Operation               |
|---------|---------|---------|-------------------------|
| integer | integer | float   | x % y                   |
| integer | float   | float   | x % y                   |
| integer | string  | float   | x % ToFloat(y)          |
| float   | integer | float   | x % y                   |
| float   | float   | float   | x % y                   |
| float   | string  | float   | x % ToFloat(y)          |
| string  | integer | float   | ToFloat(x) % y          |
| string  | float   | float   | ToFloat(x) % y          |
| string  | string  | float   | ToFloat(x) % ToFloat(y) |
| list    | integer | list    | Distributed             |
| list    | float   | list    | Distributed             |
| list    | string  | list    | Distributed             |

A type error is raised on all other combinations

```vgr
None % None → None
None % 5 → 0
None % "5" → 0
5 % 2 → 1
5 % "2" → 1
"5" % 2 → 1
[5, 7] % 3 → [2, 1]
```
"""
    return reduce(_mod, args[1:], args[0]) if args else None

def _mod(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, mod_operations, numeric_operations)
    return operation(_mod, x, y) if operation else x % y

mod_operations = {
    (str, str): lambda op, x, y: op(empty_is_zero(x), empty_is_zero(y)),
}
