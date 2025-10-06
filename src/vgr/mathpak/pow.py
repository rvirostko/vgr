"""
The pow() function
"""

from functools import reduce
from typing import Any

from .common import bound_ops, numeric_operations, get_operation

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
| tuple | int   | tuple     | distributed                |
| tuple | float | tuple     | distributed                |
| tuple | str   | tuple     | distributed                |

TypeError raised on all other combinations

```vgr
**TODO**
```
"""
    return reduce(_pow, args, x)

def _pow(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, numeric_operations)
    return operation(_pow, x, y) if operation else x ** y
