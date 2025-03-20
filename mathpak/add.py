#! /usr/bin/env python3

from .common import dist_list, dist_tuple, math_overrides, matching_default, time_test
from functools import reduce
from typing import Any

def poly_vadd(x: Any, *args): return reduce(poly_add, args, x)
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
    if x is None: return None if y is None else poly_add(matching_default(y), y)
    if y is None: return poly_add(x, matching_default(x))
    override = _overrides.get((type(x), type(y)))
    if not override: override = math_overrides.get((type(x), type(y)))
    return override(poly_add, x, y) if override else x + y

_overrides = {
    (int, list): lambda op, x, y: dist_list(op, y, x),
    (int, tuple): lambda op, x, y: dist_tuple(op, y, x),
    (float, list): lambda op, x, y: dist_list(op, y, x),
    (float, tuple): lambda op, x, y: dist_tuple(op, y, x),
    (str, str): lambda _, x, y: x + y,
    (str, list): lambda op, x, y: [op(x, y1) for y1 in y],
    (str, tuple): lambda op, x, y: tuple(op(x, y1) for y1 in y),
    (list, tuple): lambda _, x, y: x + list(y),
    (tuple, list): lambda _, x, y: x + tuple(y),
    (dict, dict): lambda _, x, y: {**x, **y}
}

def add_test():
    cases = [
        (1, 2),
        (1, 2.5),
        (1, "3.0"),
        (1, [2, 3]),
        (1, (2, 3)),
        (2.5, 3),
        (2.5, 4.5),
        (2.5, "5.5"),
        (2.5, [6, 7]),
        (2.5, (8, 9)),
        ("a", "b"),
        ("x", 4),
        ("y", 6.7),
        ("z", [1, 2]),
        ("w", (3, 4)),
        ([1, 2], 3),
        ([1, 2], "x"),
        ([1, 2], [3, 4]),
        ([1, 2], (5, 6)),
        ((1, 2), 3),
        ((1, 2), "x"),
        ((1, 2), [3, 4]),
        ((1, 2), (5, 6)),
        ({"a": 1}, {"b": 2}),
        (None, 5),
        (7, None),
        (None, None),
    ]
    time_test(poly_add, cases, 1)

if __name__ == "__main__": add_test()
