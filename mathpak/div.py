#! /usr/bin/env python3

from .common import math_overrides, matching_default, time_test
from functools import reduce
from typing import Any

def poly_vdiv(x: Any, *args): return reduce(poly_div, args, x)
def poly_div(x: Any, y: Any) -> Any:
    """Polymorphic division function.

| x     | y     | returns | operation            |
|-------|-------|---------|----------------------|
| int   | int   | float   | x / y                |
| int   | float | float   | x / y                |
| int   | str   | float   | x / float(y)         |
| float | int   | float   | x / y                |
| float | float | float   | x / y                |
| float | str   | float   | x / float(y)         |
| str   | int   | float   | float(x) / y         |
| str   | float | float   | float(x) / y         |
| str   | str   | float   | float(x) / float(y)  |
| list  | int   | list    | distributive         |
| list  | float | list    | distributive         |
| list  | str   | list    | distributive         |
| tuple | int   | tuple   | distributive         |
| tuple | float | tuple   | distributive         |
| tuple | str   | tuple   | distributive         |

TypeError raised on all other combinations
"""
    if x == None: return None if y == None else poly_div(matching_default(y), y)
    if y == None: return poly_div(x, matching_default(x))
    override = math_overrides.get((type(x), type(y)))
    return override(poly_div, x, y) if override else x / y

def poly_vfdiv(x: Any, *args): return reduce(poly_fdiv, args, x)
def poly_fdiv(x: Any, y: Any) -> Any:
    """Polymorphic floor division function.

| x     | y     | returns | operation             |
|-------|-------|---------|-----------------------|
| int   | int   | float   | x // y                |
| int   | float | float   | x // y                |
| int   | str   | float   | x // float(y)         |
| float | int   | float   | x // y                |
| float | float | float   | x // y                |
| float | str   | float   | x // float(y)         |
| str   | int   | float   | float(x) // y         |
| str   | float | float   | float(x) // y         |
| str   | str   | float   | float(x) // float(y)  |
| list  | int   | list    | distributive          |
| list  | float | list    | distributive          |
| list  | str   | list    | distributive          |
| tuple | int   | tuple   | distributive          |
| tuple | float | tuple   | distributive          |
| tuple | str   | tuple   | distributive          |

TypeError raised on all other combinations
"""
    if x == None: return None if y == None else poly_fdiv(matching_default(y), y)
    if y == None: return poly_fdiv(x, matching_default(x))
    override = math_overrides.get((type(x), type(y)))
    return override(poly_fdiv, x, y) if override else x // y

def div_test():
    cases = [
        (0, 2),
        (5, 2),
        (5, 2.0),
        (5, ' +2 '),
        (5.0, 2),
        (5.0, 2.0),
        (5.0, '2'),
        ('5.0', 2),
        ('5.0', 2.0),
        ('5.0', '2.0'),
        ([5, 10, 15], 2),
        ([5, 10, 15], 2.0),
        ([5, 10, 15], '2'),
        ((5, 10, 15), 2),
        ((5, 10, 15), 2.0),
        ((5, 10, 15), '2'),
        (None, 5),
        #(5, None), #ZeroDivisionError
        (None, None),
    ]
    time_test(poly_div, cases,1)
    time_test(poly_fdiv, cases, 1)

if __name__ == "__main__": div_test()
