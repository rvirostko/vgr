from functools import reduce
from typing import Any

from .common import get_operation, numeric_operations, dist_y_list, dist_y_tuple

def poly_vadd(x: Any, *args):
    """Varargs version of poly_add"""
    return reduce(poly_add, args, x)

def poly_add(x: Any, y: Any) -> Any:
    """Polymorphic addition function.

| x       | y       | returns   | operation                |
|---------|---------|-----------|--------------------------|
| int     | int     | int       | addition                 |
| int     | float   | float     | addition                 |
| int     | str     | Any       | addition/concatenation   |
| int     | list    | list      | distributive             |
| int     | tuple   | tuple     | distributive             |
| float   | int     | float     | addition                 |
| float   | float   | float     | addition                 |
| float   | str     | Any       | addition/concatenation   |
| float   | list    | list      | distributive             |
| float   | tuple   | tuple     | distributive             |
| str     | int     | Any       | addition/concatenation   |
| str     | float   | Any       | addition/concatenation   |
| str     | str     | str       | concatenation            |
| str     | list    | list      | distributive             |
| str     | tuple   | tuple     | distributive             |
| list    | int     | list      | distributive             |
| list    | float   | list      | distributive             |
| list    | str     | list      | distributive             |
| list    | list    | list      | union                    |
| list    | tuple   | list      | union                    |
| tuple   | int     | tuple     | distributive             |
| tuple   | float   | tuple     | distributive             |
| tuple   | str     | tuple     | distributive             |
| tuple   | list    | tuple     | union                    |
| tuple   | tuple   | tuple     | union                    |
| dict    | dict    | dict      | union                    |

TypeError raised on all other combinations
"""
    operation = get_operation(x, y, add_operations, numeric_operations)
    return operation(poly_add, x, y) if operation else x + y

add_operations = {
    (int, list): dist_y_list,
    (int, tuple): dist_y_tuple,
    (float, list): dist_y_list,
    (float, tuple): dist_y_tuple,
    (str, str): lambda _, x, y: x + y,
    (str, list): dist_y_list,
    (str, tuple): dist_y_tuple,
    (list, tuple): lambda _, x, y: x + list(y),
    (tuple, list): lambda _, x, y: x + tuple(y),
    (dict, dict): lambda _, x, y: {**x, **y}
}
