#! /usr/bin/env python3

from typing import Any

from .common import math_overrides, matching_default

# TODO rename "pow"
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
    if x is None: return None if y is None else poly_exp(matching_default(y), y)
    if y is None: return poly_exp(x, matching_default(x))
    override = math_overrides.get((type(x), type(y)))
    return override(poly_exp, x, y) if override else x ** y
