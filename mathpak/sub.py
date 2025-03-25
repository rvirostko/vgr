from functools import reduce
from typing import Any

from .common import get_operation, numeric_operations

def poly_vsub(x: Any, *args):
    """Varargs version of poly_sub"""
    return reduce(poly_sub, args, x)

def poly_sub(x: Any, y: Any) -> Any:
    """Polymorphic subtraction function.

| x     | y     | returns | operation               |
|-------|-------|---------|-------------------------|
| int   | int   | int     | x - y                   |
| int   | float | float   | x - y                   |
| int   | str   | float   | x - float(y)            |
| float | int   | float   | x - y                   |
| float | float | float   | x - y                   |
| float | str   | float   | x - float(y)            |
| str   | int   | float   | float(x) - y            |
| str   | float | float   | float(x) - y            |
| str   | str   | float   | float(x) - float(y)     |
| list  | int   | list    | distributed             |
| list  | float | list    | distributed             |
| list  | str   | list    | distributed             |
| tuple | int   | tuple   | distributed             |
| tuple | float | tuple   | distributed             |
| tuple | str   | tuple   | distributed             |
| dict  | str   | dict    | remove y from x         |
| dict  | list  | dict    | remove keys in y from x |
| dict  | tuple | dict    | remove keys in y from x |
| dict  | dict  | dict    | remove keys in y from x |

TypeError raised on all other combinations
"""
    operation = get_operation(x, y, sub_operations, numeric_operations)
    return operation(poly_sub, x, y) if operation else x - y

def remove_keys(x: dict, y: Any) -> dict:
    return {k:v for k, v in x.items() if k not in y}

sub_operations = {
    (dict, int): lambda _, x, y: remove_keys(x, [y]),
    (dict, float): lambda _, x, y: remove_keys(x, [y]),
    (dict, str): lambda _, x, y:  remove_keys(x, [y]),
    (dict, list): lambda _, x, y: remove_keys(x, y),
    (dict, tuple): lambda _, x, y: remove_keys(x, y),
    (dict, dict): lambda _, x, y:  remove_keys(x, list(y.keys())),
}
