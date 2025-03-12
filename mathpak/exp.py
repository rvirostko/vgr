#! /usr/bin/python3

from .common import math_overrides, matching_default, time_test

from typing import Any

def poly_exp(x: Any, y: Any) -> Any:
    """Polymorphic exponential function.

| x     | y     | returns | operation                                      |
|-------|-------|---------|------------------------------------------------|
| int   | int   | float   | x ** y                                         |
| int   | float | float   | x ** y                                         |
| int   | str   | float   | x ** float(y)                                  |
| float | int   | float   | x ** y                                         |
| float | float | float   | x ** y                                         |
| float | str   | float   | x ** float(y)                                  |
| str   | int   | float   | float(x) ** y                                  |
| str   | float | float   | float(x) ** y                                  |
| str   | str   | float   | float(x) ** float(y)                           |
| list  | int   | list    | distributed exp: elements in x exp by y        |
| list  | float | list    | distributed exp: elements in x exp by y        |
| list  | str   | list    | distributed exp: elements in x exp by float(y) |
| tuple | int   | tuple   | distributed exp: elements in x exp by y        |
| tuple | float | tuple   | distributed exp: elements in x exp by y        |
| tuple | str   | tuple   | distributed exp: elements in x exp by float(y) |

TypeError raised on all other combinations
"""
    if x == None: return None if y == None else poly_exp(matching_default(y), y)
    if y == None: return poly_exp(x, matching_default(x))
    override = math_overrides.get((type(x), type(y)))
    return override(poly_exp, x, y) if override else x ** y

def exp_test():
    cases = [
        (2, 3),
        (2, 3.5),
        (2, "3.5"),
        (2.5, 3),
        (2.5, 3.5),
        (2.5, "3.5"),
        ("2.5", 3),
        ("2.5", 3.5),
        ("2.5", "3.5"),
        ([2, 3, 4], 2),
        ([2.5, 3.5], 2.0),
        ([2, 3, 4], "2.0"),
        ((2, 3, 4), 2),
        ((2.5, 3.5), 2.0),
        ((2, 3, 4), "2.0"),
        (None, 3),
        (2, None),
    ]
    time_test(poly_exp, cases, 1)

if __name__ == "__main__": exp_test()
