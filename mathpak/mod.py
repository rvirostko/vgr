#! /usr/bin/env python3

from typing import Any

from .common import math_overrides, matching_default

def poly_mod(x: Any, y: Any) -> Any:
    """Polymorphic modulus function.

| x     | y     | returns | operation            |
|-------|-------|---------|----------------------|
| int   | int   | float   | x % y                |
| int   | float | float   | x % y                |
| int   | str   | float   | x % float(y)         |
| float | int   | float   | x % y                |
| float | float | float   | x % y                |
| float | str   | float   | x % float(y)         |
| str   | int   | float   | float(x) % y         |
| str   | float | float   | float(x) % y         |
| str   | str   | float   | float(x) % float(y)  |
| list  | int   | list    | distributive         |
| list  | float | list    | distributive         |
| list  | str   | list    | distributive         |
| tuple | int   | tuple   | distributive         |
| tuple | float | tuple   | distributive         |
| tuple | str   | tuple   | distributive         |

TypeError raised on all other combinations
"""
    if x is None: return None if y is None else poly_mod(matching_default(y), y)
    if y is None: return poly_mod(x, matching_default(x))
    override = math_overrides.get((type(x), type(y)))
    return override(poly_mod, x, y) if override else x % y
