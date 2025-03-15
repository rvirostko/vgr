#! /usr/bin/env python3

from .common import dist_list, dist_tuple, str_to_number, matching_default, time_test

from typing import Any

def poly_shl(x: Any, y: Any) -> Any:
    """Polymorphic shift left function.

| x     | y     | returns | operation                                     |
|-------|-------|---------|-----------------------------------------------|
| int   | int   | int     | x << y                                        |
| int   | float | int     | x << int(y)                                   |
| int   | str   | int     | x << int(y)                                   |
| float | int   | int     | int(x) << y                                   |
| float | float | int     | int(x) << y                                   |
| float | str   | int     | int(x) << int(y)                              |
| str   | int   | int     | int(x) << y                                   |
| str   | float | int     | int(x) << y                                   |
| str   | str   | int     | int(x) << int(y)                              |
| list  | int   | list    | distributed shift: elements in x << by y      |
| list  | float | list    | distributed shift: elements in x << by y      |
| list  | str   | list    | distributed shift: elements in x << by int(y) |
| tuple | int   | tuple   | distributed shift: elements in x << by y      |
| tuple | float | tuple   | distributed shift: elements in x << by y      |
| tuple | str   | tuple   | distributed shift: elements in x << by int(y) |

TypeError raised on all other combinations
"""
    if x == None: return None if y == None else poly_shl(matching_default(y), y)
    if y == None: return poly_shl(x, matching_default(x))
    override = _overrides.get((type(x), type(y)))
    return override(poly_shl, x, y) if override else x << y

def _str_to_int(x: str) -> int: return int(str_to_number(x))

_overrides = {
    (int, str): lambda op, x, y: op(x, _str_to_int(y)),
    (int, float): lambda op, x, y: op(x, int(y)),
    (float, int): lambda op, x, y: op(int(x), y),
    (float, float): lambda op, x, y: op(int(x), int(y)),
    (float, str): lambda op, x, y: op(int(x), _str_to_int(y)),
    (str, int): lambda op, x, y: op(_str_to_int(x), y),
    (str, float): lambda op, x, y: op(_str_to_int(x), int(y)),
    (str, str): lambda op, x, y: op(_str_to_int(x), _str_to_int(y)),
    (list, int): lambda op, x, y: dist_list(op, x, y),
    (list, float): lambda op, x, y: dist_list(op, x, int(y)),
    (list, str): lambda op, x, y: dist_list(op, x, _str_to_int(y)),
    (tuple, int): lambda op, x, y: dist_tuple(op, x, y),
    (tuple, float): lambda op, x, y: dist_tuple(op, x, int(y)),
    (tuple, str): lambda op, x, y: dist_tuple(op, x, _str_to_int(y)),
}

def poly_shr(x: Any, y: Any) -> Any:
    """Polymorphic shift right function.

| x     | y     | returns | operation                                     |
|-------|-------|---------|-----------------------------------------------|
| int   | int   | int     | x >> y                                        |
| int   | float | int     | x >> int(y)                                   |
| int   | str   | int     | x >> int(y)                                   |
| float | int   | int     | int(x) >> y                                   |
| float | float | int     | int(x) >> int(y)                              |
| float | str   | int     | int(x) >> int(y)                              |
| str   | int   | int     | int(x) >> y                                   |
| str   | float | int     | int(x) >> int(y)                              |
| str   | str   | int     | int(x) >> int(y)                              |
| list  | int   | list    | distributed shift: elements in x >> by y      |
| list  | float | list    | distributed shift: elements in x >> by y      |
| list  | str   | list    | distributed shift: elements in x >> by int(y) |
| tuple | int   | tuple   | distributed shift: elements in x >> by y      |
| tuple | float | tuple   | distributed shift: elements in x >> by y      |
| tuple | str   | tuple   | distributed shift: elements in x >> by int(y) |
| None  | Any   | Any     | same as poly_shr(0, y)                        |
| Any   | None  | Any     | same as poly_shr(x, 0)                        |

TypeError raised on all other combinations
    """
    if x == None: return None if y == None else poly_shr(matching_default(y), y)
    if y == None: return poly_shr(x, matching_default(x))
    override = _overrides.get((type(x), type(y)))
    return override(poly_shr, x, y) if override else x >> y

def shift_test():
    cases = [
        (2, 3),
        (2, 3.5),
        (2, "3"),
        (2.5, 3),
        (2.5, 3.5),
        (2.5, "3"),
        ("2", 3),
        ("2", 3.5),
        ("2", "3"),
        ([2, 3, 4], 2),
        ([2.5, 3.5], 2.0),
        ([2, 3, 4], "2"),
        ((2, 3, 4), 2),
        ((2.5, 3.5), 2.0),
        ((2, 3, 4), "2"),
        (None, 3),
        (2, None),
        (None, None),
    ]
    time_test(poly_shl, cases, 1)
    time_test(poly_shr, cases, 1)

if __name__ == "__main__": shift_test()
