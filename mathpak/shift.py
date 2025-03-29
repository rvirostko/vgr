"""
Bitwise shift left and right.
"""

from functools import reduce
from typing import Any

from .common import dist_x_list, dist_x_tuple, str_to_int, X_None_Op, Y_None_Op, get_operation, matching_default

def poly_vshl(x: Any, *args):
    """Varargs version of poly_shl"""
    return reduce(poly_shl, args, x)

def poly_shl(x: Any, y: Any) -> Any:
    """Polymorphic shift left function.

| x     | y     | returns | operation        |
|-------|-------|---------|------------------|
| int   | int   | int     | x << y           |
| int   | float | int     | x << int(y)      |
| int   | str   | int     | x << int(y)      |
| float | int   | int     | int(x) << y      |
| float | float | int     | int(x) << y      |
| float | str   | int     | int(x) << int(y) |
| str   | int   | int     | int(x) << y      |
| str   | float | int     | int(x) << y      |
| str   | str   | int     | int(x) << int(y) |
| list  | int   | list    | distributed      |
| list  | float | list    | distributed      |
| list  | str   | list    | distributed      |
| tuple | int   | tuple   | distributed      |
| tuple | float | tuple   | distributed      |
| tuple | str   | tuple   | distributed      |

TypeError raised on all other combinations
"""
    operation = get_operation(x, y, shift_operations)
    return operation(poly_shl, x, y) if operation else x << y

def poly_vshr(x: Any, *args):
    """Varargs version of poly_shr"""
    return reduce(poly_shr, args, x)

def poly_shr(x: Any, y: Any) -> Any:
    """Polymorphic shift right function.

| x     | y     | returns | operation        |
|-------|-------|---------|------------------|
| int   | int   | int     | x >> y           |
| int   | float | int     | x >> int(y)      |
| int   | str   | int     | x >> int(y)      |
| float | int   | int     | int(x) >> y      |
| float | float | int     | int(x) >> int(y) |
| float | str   | int     | int(x) >> int(y) |
| str   | int   | int     | int(x) >> y      |
| str   | float | int     | int(x) >> int(y) |
| str   | str   | int     | int(x) >> int(y) |
| list  | int   | list    | distributed      |
| list  | float | list    | distributed      |
| list  | str   | list    | distributed      |
| tuple | int   | tuple   | distributed      |
| tuple | float | tuple   | distributed      |
| tuple | str   | tuple   | distributed      |

TypeError raised on all other combinations
    """
    operation = get_operation(x, y, shift_operations)
    return operation(poly_shr, x, y) if operation else x >> y

shift_operations = {
    X_None_Op: lambda op, _, y: None if y is None else op(matching_default(y), y),
    Y_None_Op: lambda op, x, _: op(x, matching_default(x)),
    (int, str): lambda op, x, y: op(x, str_to_int(y)),
    (int, float): lambda op, x, y: op(x, int(y)),
    (float, int): lambda op, x, y: op(int(x), y),
    (float, float): lambda op, x, y: op(int(x), int(y)),
    (float, str): lambda op, x, y: op(int(x), str_to_int(y)),
    (str, int): lambda op, x, y: op(str_to_int(x), y),
    (str, float): lambda op, x, y: op(str_to_int(x), int(y)),
    (str, str): lambda op, x, y: op(str_to_int(x), str_to_int(y)),
    (list, int): dist_x_list,
    (list, float): lambda op, x, y: dist_x_list(op, x, int(y)),
    (list, str): lambda op, x, y: dist_x_list(op, x, str_to_int(y)),
    (tuple, int): dist_x_tuple,
    (tuple, float): lambda op, x, y: dist_x_tuple(op, x, int(y)),
    (tuple, str): lambda op, x, y: dist_x_tuple(op, x, str_to_int(y)),
}
