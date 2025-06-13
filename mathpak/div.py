from functools import reduce
from typing import Any

from .common import numeric_operations, get_operation

def poly_div(x: Any, *args):
    """
**Polymorphic division**

* _x_ / _y_
* _x_ ÷ _y_
* _x_.Div(_y..._)

| x     | y     | returns | operation           |
|-------|-------|---------|---------------------|
| int   | int   | float   | x / y               |
| int   | float | float   | x / y               |
| int   | str   | float   | x / float(y)        |
| float | int   | float   | x / y               |
| float | float | float   | x / y               |
| float | str   | float   | x / float(y)        |
| str   | int   | float   | float(x) / y        |
| str   | float | float   | float(x) / y        |
| str   | str   | float   | float(x) / float(y) |
| list  | int   | list    | distributive        |
| list  | float | list    | distributive        |
| list  | str   | list    | distributive        |
| tuple | int   | tuple   | distributive        |
| tuple | float | tuple   | distributive        |
| tuple | str   | tuple   | distributive        |

TypeError raised on all other combinations
"""
    return reduce(_div, args, x)

def _div(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, numeric_operations)
    return operation(_div, x, y) if operation else x / y

def poly_fdiv(x: Any, *args):
    """
**Polymorphic floor division**

* _x_ // _y_
* _x_.FloorDiv(_y..._)

| x     | y     | returns | operation            |
|-------|-------|---------|----------------------|
| int   | int   | float   | x // y               |
| int   | float | float   | x // y               |
| int   | str   | float   | x // float(y)        |
| float | int   | float   | x // y               |
| float | float | float   | x // y               |
| float | str   | float   | x // float(y)        |
| str   | int   | float   | float(x) // y        |
| str   | float | float   | float(x) // y        |
| str   | str   | float   | float(x) // float(y) |
| list  | int   | list    | distributive         |
| list  | float | list    | distributive         |
| list  | str   | list    | distributive         |
| tuple | int   | tuple   | distributive         |
| tuple | float | tuple   | distributive         |
| tuple | str   | tuple   | distributive         |

TypeError raised on all other combinations
"""
    return reduce(_fdiv, args, x)

def _fdiv(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, numeric_operations)
    return operation(_fdiv, x, y) if operation else x // y

def poly_divmod(x: Any, y: Any) -> Any:
    """
**Polymorphic division/modulo**

* _x_.DivMod(_y_)

| x     | y     | returns | operation                  |
|-------|-------|---------|----------------------------|
| int   | int   | float   | divmod(x, y)               |
| int   | float | float   | divmod(x, y)               |
| int   | str   | float   | divmod(x, float(y))        |
| float | int   | float   | divmod(x, y)               |
| float | float | float   | divmod(x, y)               |
| float | str   | float   | divmod(x, float(y))        |
| str   | int   | float   | divmod(float(x), y         |
| str   | float | float   | divmod(float(x), y         |
| str   | str   | float   | divmod(float(x), float(y)) |
| list  | int   | list    | distributive               |
| list  | float | list    | distributive               |
| list  | str   | list    | distributive               |
| tuple | int   | tuple   | distributive               |
| tuple | float | tuple   | distributive               |
| tuple | str   | tuple   | distributive               |

TypeError raised on all other combinations

Returns a tuple of (_x_ // _y_, _x_ % _y_)
"""
    operation = get_operation(x, y, numeric_operations)
    return operation(poly_divmod, x, y) if operation else divmod(x, y)
