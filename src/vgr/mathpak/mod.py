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
def poly_mod(x: Any, *args):
    """
**Modulo operation**

* _x_ % _y_
* Mod(_x_, _y_...)
* _x_.Mod(_y_...)

| x     | y     | returns | operation           |
|-------|-------|---------|---------------------|
| int   | int   | float   | x % y               |
| int   | float | float   | x % y               |
| int   | str   | float   | x % float(y)        |
| float | int   | float   | x % y               |
| float | float | float   | x % y               |
| float | str   | float   | x % float(y)        |
| str   | int   | float   | float(x) % y        |
| str   | float | float   | float(x) % y        |
| str   | str   | float   | float(x) % float(y) |
| list  | int   | list    | distributive        |
| list  | float | list    | distributive        |
| list  | str   | list    | distributive        |

TypeError raised on all other combinations

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
    return reduce(_mod, args, x)

def _mod(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, mod_operations, numeric_operations)
    return operation(_mod, x, y) if operation else x % y

mod_operations = {
    (str, str): lambda op, x, y: op(empty_is_zero(x), empty_is_zero(y)),
}
