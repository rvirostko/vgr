#! /usr/bin/python3

from .common import dist_list, dist_tuple, time_test
from functools import reduce
from typing import Any
import itertools

def poly_vmul(x: Any, *args): return reduce(poly_mul, args, x)
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
    if x == None or y == None: return None
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

def mul_test():
    cases = [
        ( 2, 4 ),
        ( 2, 4.0 ),
        ( 2, "x" ),
        ( 2, [2, 4] ),
        ( 2, (2, 4) ),
        ( 3.1, 4 ),
        ( 3.1, 4.0 ),
        ( 3.1, "x" ),
        ( 3.1, [2, 4] ),
        ( 3.1, (2, 4) ),
        ( "y", 3 ),
        ( "y", 3.1 ),
        ( "y", "x" ),
        ( "y", [2, 4] ),
        ( "y", (2, 4) ),
        ( [3, 6], 2 ),
        ( [3, 6], 2.0 ),
        ( [3, 6], "z" ),
        ( [3, 6], [2, 4] ),
        ( [3, 6], [2, 4] ),
        ( [], (2, 4) ),
        ( [1], (2, 4) ),
        ( (4, 8), 2 ),
        ( (4, 8), 2.0 ),
        ( (4, 8), "z" ),
        ( (4, 8), [2, 4] ),
        ( (4, 8), (2, 4) ),
        ( tuple(), (2, 4) ),
        ( (1,), (2, 4) ),
        ( None, 5 ),
        ( None, [5] ),
        ( 5, None ),
        ( [5], None ),
        ( None, None)
    ]
    time_test(poly_mul, cases)

if __name__ == "__main__": mul_test()
