#! /usr/bin/env python3

from typing import Any

from .common import str_to_number

TRUE_STRS = ('true', 't', 'yes', 'y', 'on')
FALSE_STRS = ('false', 'f', 'no', 'n', 'off')

def coerce_value(value: Any) -> Any:
    """
    Coerce the string value to None, int, float, or bool.
    Falls back to the original string.
    This is for only the most naive of conversions.
    """
    if value is None or isinstance(value, (bool, int, float, dict, list, tuple)): return value
    if value.strip().lower() in ('true', 'false'): return poly_bool(value)
    try:
        return poly_number(value)
    except TypeError:
        return None if value.strip().lower() == 'none' else value

def poly_bool(x: Any) -> bool:
    if x is None: return False
    if poly_isnumber(x): return bool(x)
    if poly_isstr(x):
        x = x.strip().lower()
        if x in TRUE_STRS: return True
        if x in FALSE_STRS: return False
        try: return bool(str_to_number(x))
        except Exception: return True
    return True

def poly_isbool(x: Any) -> bool:
    return isinstance(x, bool)

def poly_float(x: Any) -> float:
    x = poly_number(x)
    return float(x) if x is not None else None

def poly_isfloat(x: Any) -> bool:
    return isinstance(x, float)

def poly_int(x: Any) -> int:
    x = poly_number(x)
    return int(x) if x is not None else None

def poly_isint(x: Any) -> bool:
    return isinstance(x, int)

def poly_number(x: Any) -> Any:
    if x is None: return None
    if poly_isnumber(x): return int(x)
    if poly_isstr(x): return str_to_number(x)
    if isinstance(x, (list, tuple)) and len(x) > 0: return poly_number(x[0])
    return None

def poly_isnumber(x: Any) -> bool:
    return isinstance(x, (int, float))

def poly_str(x: Any) -> str:
    return str(x) if x is not None else None

def poly_isstr(x: Any) -> bool:
    return isinstance(x, str)
