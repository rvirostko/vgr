from functools import reduce
from typing import Any
import itertools

from .common import dist_x_list, dist_x_tuple, dist_y_list, dist_y_tuple, X_None_Op, Y_None_Op, get_operation

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
| int   | list  | list    | repetition          |
| int   | tuple | tuple   | repetition          |
| float | int   | float   | x * float(y)        |
| float | float | float   | x * y               |
| float | str   | str     | string repetition   |
| float | list  | list    | repetition          |
| float | tuple | tuple   | repetition          |
| str   | int   | str     | string repetition   |
| str   | float | str     | string repetition   |
| str   | str   | str     | concatenation       |
| str   | list  | list    | distributive        |
| str   | tuple | tuple   | distributive        |
| list  | int   | list    | repetition          |
| list  | float | list    | repetition          |
| list  | str   | list    | distributive        |
| list  | list  | list    | cartesian product   |
| list  | tuple | list    | cartesian product   |
| tuple | int   | tuple   | repetition          |
| tuple | float | tuple   | repetition          |
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
    (float, list): lambda _, x, y: int(x) * y,
    (float, tuple): lambda _, x, y: int(x) * y,
    (str, float): lambda _, x, y: x * int(y),
    (str, str): lambda _, x, y: x + y, # TODO rethink?
    (str, list): dist_y_list,
    (str, tuple): dist_y_tuple,
    (list, float): lambda _, x, y: x * int(y),
    (list, str): dist_x_list,
    (list, list): product_list,
    (list, tuple): product_list,
    (tuple, float): lambda _, x, y: x * int(y),
    (tuple, str): dist_x_tuple,
    (tuple, list): product_tuple,
    (tuple, tuple): product_tuple,
}
