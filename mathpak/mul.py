#! /usr/bin/env python3

from functools import reduce
from typing import Any
import itertools

from .common import dist_list, dist_tuple

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
    if x is None or y is None: return None
    override = _overrides.get((type(x), type(y)))
    return override(poly_mul, x, y) if override else x * y

def _prod_list(x: list, y: Any) -> list: return list(itertools.product(iter(x), iter(y)))
def _prod_tuple(x: tuple, y: Any) -> tuple: return tuple(itertools.product(iter(x), iter(y)))

_overrides = {
    (float, str): lambda _, x, y: int(x) * y,
    (float, list): lambda _, x, y: int(x) * y,
    (float, tuple): lambda _, x, y: int(x) * y,
    (str, float): lambda _, x, y: x * int(y),
    (str, str): lambda _, x, y: x + y, # TODO rethink?
    (str, list): lambda op, x, y: dist_list(op, y, x),
    (str, tuple): lambda op, x, y: dist_tuple(op, y, x),
    (list, float): lambda _, x, y: x * int(y),
    (list, str): lambda op, x, y: dist_list(op, x, y),
    (list, list): lambda _, x, y: _prod_list(x, y),
    (list, tuple): lambda _, x, y: _prod_list(x, y),
    (tuple, float): lambda _, x, y: x * int(y),
    (tuple, str): lambda op, x, y: dist_tuple(op, x, y),
    (tuple, list): lambda _, x, y: _prod_tuple(x, y),
    (tuple, tuple): lambda _, x, y: _prod_tuple(x, y),
}
