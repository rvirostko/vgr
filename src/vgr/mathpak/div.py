from functools import reduce
from typing import Any

from .common import bound_ops, numeric_operations, get_operation

@bound_ops("/", "÷")
def poly_div(x: Any, *args):
    """
**Division operation**

* _x_ / _y_
* _x_ ÷ _y_
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
| tuple | int   | tuple   | distributive              |
| tuple | float | tuple   | distributive              |
| tuple | str   | tuple   | distributive              |

TypeError raised on all other combinations
"""
    return reduce(_div, args, x)

def _div(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, numeric_operations)
    return operation(_div, x, y) if operation else x / y

def poly_fdiv(x: Any, *args):
    """
**Floor division operation**

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
| tuple | int   | tuple     | distributive                 |
| tuple | float | tuple     | distributive                 |
| tuple | str   | tuple     | distributive                 |

TypeError raised on all other combinations
"""
    return reduce(_fdiv, args, x)

def _fdiv(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, numeric_operations)
    return operation(_fdiv, x, y) if operation else x // y

def poly_divmod(x: Any, y: Any) -> Any:
    """
**Division/modulo operation**

* _x_.DivMod(_y_)

Returns a tuple of (_x_ fdiv _y_, _x_ % _y_)

| x     | y     | returns | operation                         |
|-------|-------|---------|-----------------------------------|
| int   | int   | tuple   | x divmod by y                     |
| int   | float | tuple   | x divmod by y                     |
| int   | str   | tuple   | x divmod by ToNumber(y)           |
| float | int   | tuple   | x divmod by y                     |
| float | float | tuple   | x divmod by y                     |
| float | str   | tuple   | x divmod by ToNumber(y)           |
| str   | int   | tuple   | ToNumber(x) divmod by y           |
| str   | float | tuple   | ToNumber(x) divmod by y           |
| str   | str   | tuple   | ToNumber(x) divmod by ToNumber(y) |
| list  | int   | list    | distributive                      |
| list  | float | list    | distributive                      |
| list  | str   | list    | distributive                      |
| tuple | int   | tuple   | distributive                      |
| tuple | float | tuple   | distributive                      |
| tuple | str   | tuple   | distributive                      |

TypeError raised on all other combinations

"""
    operation = get_operation(x, y, numeric_operations)
    return operation(poly_divmod, x, y) if operation else divmod(x, y)
