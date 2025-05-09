from functools import reduce
from typing import Any
import itertools

from .common import dist_x, dist_y, X_None_Op, Y_None_Op, get_operation, str_to_int

def poly_vmul(x: Any, *args):
    """Varargs version of poly_mul"""
    return reduce(poly_mul, args, x)

def poly_mul(x: Any, y: Any) -> Any:
    """Polymorphic multiplication function.

| x     | y     | returns | operation           |
|-------|-------|---------|---------------------|
| int   | int   | int     | x * y               |
| int   | float | float   | float(x) * y        |
| int   | str   | str     | string repetition   |
| int   | list  | list    | distributive        |
| int   | tuple | tuple   | distributive        |
| float | int   | float   | x * float(y)        |
| float | float | float   | x * y               |
| float | str   | str     | string repetition   |
| float | list  | list    | distributive        |
| float | tuple | tuple   | distributive        |
| str   | int   | str     | string repetition   |
| str   | float | str     | string repetition   |
| str   | str   | str     | string repetition   |
| str   | list  | list    | distributive        |
| str   | tuple | tuple   | distributive        |
| list  | int   | list    | distributive        |
| list  | float | list    | distributive        |
| list  | str   | list    | distributive        |
| list  | list  | list    | cartesian product   |
| list  | tuple | list    | cartesian product   |
| tuple | int   | tuple   | distributive        |
| tuple | float | tuple   | distributive        |
| tuple | str   | tuple   | distributive        |
| tuple | list  | tuple   | cartesian product   |
| tuple | tuple | tuple   | cartesian product   |

TypeError raised on all other combinations
"""
    operation = get_operation(x, y, mul_operations)
    return operation(poly_mul, x, y) if operation else x * y

def product_list(_, x: list, y: Any) -> list:
    return list(itertools.product(iter(x), iter(y)))

def product_tuple(_, x: tuple, y: Any) -> tuple:
    return tuple(itertools.product(iter(x), iter(y)))

mul_operations = {
    X_None_Op: lambda _, x, y: None,
    Y_None_Op: lambda _, x, y: None,
    (float, str): lambda _, x, y: int(x) * y,
    (float, list): dist_y,
    (float, tuple): dist_y,
    (str, float): lambda _, x, y: x * int(y),
    (str, str): lambda _, x, y:  x * str_to_int(y),
    (str, list): dist_y,
    (str, tuple): dist_y,
    (list, int): dist_x,
    (list, float): dist_x,
    (list, str): dist_x,
    (list, list): product_list,
    (list, tuple): product_list,
    (tuple, int): dist_x,
    (tuple, float): dist_x,
    (tuple, str): dist_x,
    (tuple, list): product_tuple,
    (tuple, tuple): product_tuple,
}
