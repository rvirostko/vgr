"""
Modulo operation.
"""

from functools import reduce
from typing import Any

from .common import bound_ops, numeric_operations, get_operation

@bound_ops("%")
def poly_mod(x: Any, *args):
    """
**Modulo operation**

* _x_ % _y_
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
| tuple | int   | tuple   | distributive        |
| tuple | float | tuple   | distributive        |
| tuple | str   | tuple   | distributive        |

TypeError raised on all other combinations
"""
    return reduce(_mod, args, x)

def _mod(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, numeric_operations)
    return operation(_mod, x, y) if operation else x % y
