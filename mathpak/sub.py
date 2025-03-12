#! /usr/bin/python3

from .common import math_overrides, matching_default, time_test
from functools import reduce
from typing import Any

def poly_vsub(x: Any, *args): return reduce(poly_sub, args, x)
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
    if x == None: return None if y == None else poly_sub(matching_default(y), y)
    if y == None: return poly_sub(x, matching_default(x))
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

def sub_test():

    cases = [
        (5, 3),
        (5, 3.2),
        (5, "2.5"),
        (5.5, 3),
        (5.5, 3.2),
        (5.5, "2.5"),
        ("5.5", 3),
        ("5.5", 3.2),
        ("5.5", "2.5"),
        ([5, 10, 15], 3),
        ([5.5, 10.2, 15.8], 3),
        ([5, 10, 15], 2.5),
        ([5.5, 10.2, 15.8], 2.5),
        ([5, 10, 15], "2.5"),
        ((5, 10, 15), 3),
        ((5.5, 10.2, 15.8), 3),
        ((5, 10, 15), 2.5),
        ((5.5, 10.2, 15.8), 2.5),
        ((5, 10, 15), "2.5"),
        ({"a": 1, "b": 2}, "a"),
        ({"a": 1, "b": 2}, ["a", "d"]),
        ({"a": 1, "b": 2}, ("a", "b")),
        ({"a": 1, "b": 2}, {"a": 3}),
        (None, 5),
        (5, None),
    ]
    time_test(poly_sub, cases, 1)

if __name__ == "__main__": sub_test()
