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

* *x* ** *y*
* Pow(*x*, *y*&hellip;)
* *x*.Pow(*y*&hellip;)

| Type(x) | Type(y) | Returns       | Operation                  |
|---------|---------|---------------|----------------------------|
| integer | integer | float         | x ** y                     |
| integer | float   | float         | x ** y                     |
| integer | string  | integer/float | x ** ToNumber(y)           |
| float   | integer | float         | x ** y                     |
| float   | float   | float         | x ** y                     |
| float   | string  | integer/float | x ** ToNumber(y)           |
| string  | integer | integer/float | ToNumber(x) ** y           |
| string  | float   | float         | ToNumber(x) ** y           |
| string  | string  | integer/float | ToNumber(x) ** ToNumber(y) |
| list    | integer | list          | Distributed                |
| list    | float   | list          | Distributed                |
| list    | string  | list          | Distributed                |

A type error is raised on all other combinations

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
