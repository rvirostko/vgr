from functools import reduce
from typing import Any

from .common import get_operation, numeric_operations, dist_x, dist_y, str_to_number

def poly_vadd(x: Any, *args):
    """
**A variable argument, polymorphic addition function**

* _x_.Add()
* _x_.Add(_y..._)


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
    return reduce(poly_add, args, x)

def poly_add(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, add_operations, numeric_operations)
    return operation(poly_add, x, y) if operation else x + y

add_operations = {
    (int, list): dist_y,
    (int, tuple): dist_y,
    (float, list): dist_y,
    (float, tuple): dist_y,
    (str, str): lambda _, x, y: x + y,
    (str, int): lambda _, x, y: x + str(y),
    (str, float): lambda _, x, y: x + str(y),
    (str, list): dist_y,
    (str, tuple): dist_y,
    (list, int): dist_x,
    (list, float): dist_x,
    (tuple, int): dist_x,
    (tuple, float): dist_x,
    (list, tuple): lambda _, x, y: x + list(y),
    (tuple, list): lambda _, x, y: x + tuple(y),
    (dict, dict): lambda _, x, y: {**x, **y}
}

def poly_sum(x: Any, *args) -> Any:
    """
**Recursively sum lists of numbers**

* _value_.Sum()
* _value_.Sum(_values..._)

If a value is _None_ it is treated as a zero.
String values are converted to numbers when possible.

While similar to *Add()*, *Sum()* is not distributed over
lists, but instead sums their content.
"""
    return _sum(x) + sum(_sum(arg) for arg in args)

def _sum(obj):
    if obj is None: return 0
    if isinstance(obj, (int, float)): return obj
    if isinstance(obj, str):
        try:
            return str_to_number(obj) or 0
        except ValueError:
            pass
    if isinstance(obj, (list, tuple)): return sum(_sum(item) for item in obj)
    return 0
