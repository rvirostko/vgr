#! /usr/bin/env python3

from typing import Any

from .common import str_to_number

TRUE_STRS = ('true', 't', 'yes', 'y')

def poly_bool(x: Any) -> bool:
    if x is None: return False
    if poly_isnumber(x): return bool(x)
    if poly_isstr(x):
        if x.strip().lower() in TRUE_STRS: return True
        try: return bool(str_to_number(x))
        except Exception: return True
    return True

def poly_isbool(x: Any) -> bool: return isinstance(x, bool)

def poly_float(x: Any) -> float:
    x = poly_number(x)
    return float(x) if x is not None else None

def poly_isfloat(x: Any) -> bool: return isinstance(x, float)

def poly_int(x: Any) -> int:
    x = poly_number(x)
    return int(x) if x is not None else None

def poly_isint(x: Any) -> bool: return isinstance(x, int)

def poly_number(x: Any) -> Any:
    if x is None: return None
    if poly_isnumber(x): return int(x)
    if poly_isstr(x): return str_to_number(x)
    if isinstance(x, (list, tuple)) and len(x) > 0: return poly_number(x[0])
    return None

def poly_isnumber(x: Any) -> bool: return isinstance(x, (int, float))

def poly_str(x: Any) -> str:
    return str(x) if x is not None else None

def poly_isstr(x: Any) -> bool: return isinstance(x, str)
