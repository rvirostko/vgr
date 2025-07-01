from functools import reduce
from typing import Any, Callable
import math

from .common import str_to_number, type_str, dist_x

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
    if isinstance(x, str): return poly_trunc(str_to_number(x))
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
        raise TypeError(f'Unsupported precision type: {type_str(precision)}')
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
    if isinstance(x, (list, tuple)): return dist_x(poly_floor, x, precision)
    raise TypeError(f'Unsupported type for floor: {type_str(x)}')

def poly_round(x: Any, ndigits: int=0) -> Any:
    if x is None: return None
    if isinstance(x, str):
        x = str_to_number(x)
    if isinstance(ndigits, (int, float)):
        ndigits = int(ndigits)
    else:
        if isinstance(ndigits, str): return poly_round(x, str_to_number(ndigits))
        if isinstance(ndigits, (list, tuple)): return reduce(poly_round, ndigits, x)
        raise TypeError(f'Unsupported type for ndigits: {type_str(ndigits)}')
    if hasattr(x, '__round__'): return round(x, ndigits)
    if isinstance(x, (list, tuple)): return dist_x(poly_round,  x, ndigits)
    return x

def poly_round_multiple(x: Any, multiple) -> Any:
    if isinstance(x, str): x = str_to_number(x)
    if not isinstance(multiple, (int, float)):
        if isinstance(multiple, str): return poly_round_multiple(x, str_to_number(multiple))
        if isinstance(multiple, (list, tuple)): return reduce(poly_round_multiple, multiple, x)
        raise TypeError(f'Unsupported type for multiple: {type_str(multiple)}')
    if isinstance(x, (int, float)): return 0 if multiple == 0 else multiple * round(x / multiple)
    if isinstance(x, (list, tuple)): return dist_x(poly_round_multiple,  x, multiple)
    return None

def poly_floor_multiple(x: Any, multiple) -> Any:
    if isinstance(x, str): x = str_to_number(x)
    if not isinstance(multiple, (int, float)):
        if isinstance(multiple, str): return poly_floor_multiple(x, str_to_number(multiple))
        if isinstance(multiple, (list, tuple)): return reduce(poly_floor_multiple, multiple, x)
        raise TypeError(f'Unsupported type for multiple: {type_str(multiple)}')
    if isinstance(x, (int, float)): return 0 if multiple == 0 else multiple * math.floor(x / multiple)
    if isinstance(x, (list, tuple)): return dist_x(poly_floor_multiple,  x, multiple)
    return None

def poly_ceil_multiple(x: Any, multiple) -> Any:
    if isinstance(x, str): x = str_to_number(x)
    if not isinstance(multiple, (int, float)):
        if isinstance(multiple, str): return poly_ceil_multiple(x, str_to_number(multiple))
        if isinstance(multiple, (list, tuple)): return reduce(poly_ceil_multiple, multiple, x)
        raise TypeError(f'Unsupported type for multiple: {type_str(multiple)}')
    if isinstance(x, (int, float)): return 0 if multiple == 0 else multiple * math.ceil(x / multiple)
    if isinstance(x, (list, tuple)): return dist_x(poly_ceil_multiple,  x, multiple)
    return None

def _dist(op: Callable[[Any], Any], x: Any) -> Any:
    if x is None: return None
    # Distribute the operation over the collection
    return type(x)(op(x1) for x1 in x) if isinstance(x, (list, tuple)) else x
