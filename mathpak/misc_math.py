from functools import reduce
from typing import Any, Callable
import math

from .common import str_to_number

def poly_abs(x: Any) -> Any:
    if x is None: return None
    if isinstance(x, str): return poly_abs(str_to_number(x))
    return abs(x) if hasattr(x, '__abs__') else _dist(poly_abs, x)

def poly_ceil(x: Any) -> Any:
    if x is None: return None
    if isinstance(x, str): return poly_ceil(str_to_number(x))
    return math.ceil(x) if hasattr(x, '__ceil__') else _dist(poly_ceil, x)

def poly_trunc(x: Any) -> Any:
    if x is None: return None
    if isinstance(x, str): return poly_abs(str_to_number(x))
    return math.trunc(x) if hasattr(x, '__trunc__') else _dist(poly_trunc, x)

def poly_floor(x: Any, precision: float=0) -> Any:
    if isinstance(x, str):
        x = str_to_number(x)
    if x is None: return None
    if precision is None:
        precision = 0
    elif isinstance(precision, (int, float)):
        precision = float(precision)
    elif isinstance(precision, str):
        precision = str_to_number(precision)
    else:
        raise TypeError(f'Unsupported precision type: {repr(type(precision).__name__)}')
    if not 0 < precision < 1:
        precision = 0
    if isinstance(x, (int, float)):
        if x == 0:
            return x
        if precision == 0:
            return math.floor(x)
        int_part = int(x)
        fractional_part = x - int_part
        if fractional_part == 0:
            return int_part
        return int_part + (fractional_part // precision) * precision
    if isinstance(x, str): return poly_floor(str_to_number(x), precision)
    # Distribute the operation over the collection
    if isinstance(x, list): return [poly_floor(x1, precision) for x1 in x]
    if isinstance(x, tuple): return tuple(poly_floor(x1, precision) for x1 in x)
    raise TypeError(f'Unsupported type for floor: {repr(type(x).__name__)}')

def poly_round(x: Any, ndigits: int=0) -> Any:
    if isinstance(x, str):
        x = str_to_number(x)
    if x is None: return None
    if isinstance(ndigits, (int, float)):
        ndigits = int(ndigits)
    else:
        if isinstance(ndigits, str): return poly_round(str_to_number(ndigits))
        if isinstance(ndigits, (list, tuple)): return reduce(poly_round, ndigits, x)
        raise TypeError(f'Unsupported type: {type(ndigits).__name__}')
    if hasattr(x, '__round__'): return round(x, ndigits)
    # Distribute the operation over the collection
    if isinstance(x, list): return [poly_round(x1, ndigits) for x1 in x]
    if isinstance(x, tuple): return tuple(poly_round(x1, ndigits) for x1 in x)
    return x

def _dist(op: Callable[[Any], Any], x: Any) -> Any:
    if x is None: return None
    # Distribute the operation over the collection
    if isinstance(x, list): return [op(x1) for x1 in x]
    if isinstance(x, tuple): return tuple(op(x1) for x1 in x)
    return x
