"""
"""

from functools import reduce
from typing import Any

# TODO should use poly_bool?

def poly_vand(x: Any, *args):
    """Varargs version of poly_and"""
    return reduce(poly_and, args, x)

def poly_and(x: Any, y: Any) -> Any:
    return bool(x) and bool(y)

def poly_vor(x: Any, *args):
    """Varargs version of poly_or"""
    return reduce(poly_or, args, x)

def poly_or(x: Any, y: Any) -> Any:
    return bool(x) or bool(y)

def poly_not(x: Any) -> Any:
    return not bool(x)
