"""
The pow() function
"""

from functools import reduce
from typing import Any

from .common import (
    bound_ops,
    empty_is_zero,
    numeric_operations,
    get_operation,
)

@bound_ops("**")
def poly_pow(x: Any, *args):
    """
**Raise a value to a power**

* _x_ ** _y_
* Pow(_x_, _y_...)
* _x_.Pow(_y_...)

| x     | y     | returns   | operation                  |
|-------|-------|-----------|----------------------------|
| int   | int   | float     | x ** y                     |
| int   | float | float     | x ** y                     |
| int   | str   | int/float | x ** ToNumber(y)           |
| float | int   | float     | x ** y                     |
| float | float | float     | x ** y                     |
| float | str   | int/float | x ** ToNumber(y)           |
| str   | int   | int/float | ToNumber(x) ** y           |
| str   | float | float     | ToNumber(x) ** y           |
| str   | str   | int/float | ToNumber(x) ** ToNumber(y) |
| list  | int   | list      | distributed                |
| list  | float | list      | distributed                |
| list  | str   | list      | distributed                |

TypeError raised on all other combinations

```vgr
None ** None → None
None ** 5 → 0
None ** "5" → 0
5 ** 2 → 25
5 ** "2" → 25
"5" ** 2 → 25
[3, 5] ** 3 → [27, 125]
25 ** .5 → 5.0
```
"""
    return reduce(_pow, args, x)

def _pow(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, pow_operations, numeric_operations)
    return operation(_pow, x, y) if operation else x ** y

pow_operations = {
    (str, str): lambda op, x, y: op(empty_is_zero(x), empty_is_zero(y)),
}
