"""
"""

from typing import Any

from .types import poly_bool

def poly_and(x: Any, y: Any) -> Any:
    return poly_bool(x) and poly_bool(y)

def poly_or(x: Any, y: Any) -> Any:
    return poly_bool(x) or poly_bool(y)

def poly_not(x: Any) -> Any:
    return not poly_bool(x)
