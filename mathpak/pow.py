"""
"""

from functools import reduce
from typing import Any

from .common import numeric_operations, get_operation

def poly_vpow(x: Any, *args):
    """Varargs version of poly_pow"""
    return reduce(poly_pow, args, x)

def poly_pow(x: Any, y: Any) -> Any:
    """Polymorphic raising to a power function.

| x     | y     | returns | operation                                      |
|-------|-------|---------|------------------------------------------------|
| int   | int   | float   | x ** y                                         |
| int   | float | float   | x ** y                                         |
| int   | str   | float   | x ** float(y)                                  |
| float | int   | float   | x ** y                                         |
| float | float | float   | x ** y                                         |
| float | str   | float   | x ** float(y)                                  |
| str   | int   | float   | float(x) ** y                                  |
| str   | float | float   | float(x) ** y                                  |
| str   | str   | float   | float(x) ** float(y)                           |
| list  | int   | list    | distributed exp: elements in x exp by y        |
| list  | float | list    | distributed exp: elements in x exp by y        |
| list  | str   | list    | distributed exp: elements in x exp by float(y) |
| tuple | int   | tuple   | distributed exp: elements in x exp by y        |
| tuple | float | tuple   | distributed exp: elements in x exp by y        |
| tuple | str   | tuple   | distributed exp: elements in x exp by float(y) |

TypeError raised on all other combinations
"""
    operation = get_operation(x, y, numeric_operations)
    return operation(poly_pow, x, y) if operation else x ** y
