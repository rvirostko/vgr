#! /usr/bin/env python3

from functools import reduce
from typing import Any

from .common import math_overrides, matching_default

def poly_vsub(x: Any, *args):
    """Varargs version of poly_sub"""
    return reduce(poly_sub, args, x)

def poly_sub(x: Any, y: Any) -> Any:
    """Polymorphic subtraction function.

| x     | y     | returns | operation                                      |
|-------|-------|---------|------------------------------------------------|
| int   | int   | int     | x - y                                          |
| int   | float | float   | x - y                                          |
| int   | str   | float   | x - float(y)                                   |
| float | int   | float   | x - y                                          |
| float | float | float   | x - y                                          |
| float | str   | float   | x - float(y)                                   |
| str   | int   | float   | float(x) - y                                   |
| str   | float | float   | float(x) - y                                   |
| str   | str   | float   | float(x) - float(y)                            |
| list  | int   | list    | distributed sub: elements in x sub by y        |
| list  | float | list    | distributed sub: elements in x sub by y        |
| list  | str   | list    | distributed sub: elements in x sub by float(y) |
| tuple | int   | tuple   | distributed sub: elements in x sub by y        |
| tuple | float | tuple   | distributed sub: elements in x sub by y        |
| tuple | str   | tuple   | distributed sub: elements in x sub by float(y) |
| dict  | str   | dict    | remove y from x                                |
| dict  | list  | dict    | remove keys in y from x                        |
| dict  | tuple | dict    | remove keys in y from x                        |
| dict  | dict  | dict    | remove keys in y from x                        |

TypeError raised on all other combinations
"""
    if x is None: return None if y is None else poly_sub(matching_default(y), y)
    if y is None: return poly_sub(x, matching_default(x))
    type_x = type(x)
    if type_x == dict:
        override = _sub_overrides.get((type_x, type(y)))
    else:
        override = math_overrides.get((type_x, type(y)))
    return override(poly_sub, x, y) if override else x - y

def _dict_sub(x: dict, y: Any) -> dict: return {k:v for k, v in x.items() if k not in y}

_sub_overrides = {
    (dict, int): lambda _, x, y: _dict_sub(x, [y]),
    (dict, float): lambda _, x, y: _dict_sub(x, [y]),
    (dict, str): lambda _, x, y:  _dict_sub(x, [y]),
    (dict, list): lambda _, x, y: _dict_sub(x, y),
    (dict, tuple): lambda _, x, y: _dict_sub(x, y),
    (dict, dict): lambda _, x, y:  _dict_sub(x, [k for k in y.keys()]),
}
