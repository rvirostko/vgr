from typing import Any

from .common import str_to_number, str_to_bool, str_to_int, _TRUE_STRS, _FALSE_STRS

def coerce_value(value: Any) -> Any:
    """
    Coerce a string value to None, int, float, or bool.
    Falls back to the original string.
    This is for only the most naive of conversions.
    """
    if isinstance(value, str):
        v = value.strip().lower()
        if v.strip().lower() == 'none': return None
        if v in _TRUE_STRS: return True
        if v in _FALSE_STRS: return False
        try:
            return poly_number(value)
        except ValueError:
            pass
    return value

def poly_bool(x: Any) -> bool:
    if x is None: return False
    if poly_isbool(x): return x
    if poly_isnumber(x): return bool(x)
    if poly_isstr(x): return str_to_bool(x)
    if isinstance(x, list): return [poly_bool(x1) for x1 in x]
    if isinstance(x, tuple): return tuple(poly_bool(x1) for x1 in x)
    return True

def poly_isbool(x: Any) -> bool:
    return isinstance(x, bool)

def poly_float(x: Any) -> float:
    if x is None: return None
    if poly_isnumber(x): return float(x)
    if poly_isstr(x):
        n = str_to_number(x)
        return None if n is None else float(n)
    if isinstance(x, list): return [poly_float(x1) for x1 in x]
    if isinstance(x, tuple): return tuple(poly_float(x1) for x1 in x)
    return None

def poly_isfloat(x: Any) -> bool:
    return isinstance(x, float)

def poly_int(x: Any) -> int:
    if x is None: return None
    if poly_isnumber(x): return int(x)
    if poly_isstr(x): return str_to_int(x)
    if isinstance(x, list): return [poly_int(x1) for x1 in x]
    if isinstance(x, tuple): return tuple(poly_int(x1) for x1 in x)
    return None

def poly_isint(x: Any) -> bool:
    """Is the item an integer?"""
    return isinstance(x, int)

def poly_number(x: Any) -> Any:
    if x is None: return None
    if poly_isnumber(x): return x
    if poly_isstr(x): return str_to_number(x)
    if isinstance(x, list): return [poly_number(x1) for x1 in x]
    if isinstance(x, tuple): return tuple(poly_number(x1) for x1 in x)
    return None

def poly_isnumber(x: Any) -> bool:
    """Is the item a number?"""
    return isinstance(x, (int, float))

def poly_str(x: Any) -> str:
    """
    Convert the item to it's string representation.
    None is left as None, not converted to 'None'.
    """
    if x is None: return None
    if isinstance(x, list): return [poly_str(x1) for x1 in x]
    if isinstance(x, tuple): return tuple(poly_str(x1) for x1 in x)
    return str(x)

def poly_isstr(x: Any) -> bool:
    """Is the item a string?"""
    return isinstance(x, str)

def poly_islist(x: Any) -> bool:
    """Is the item a collection?"""
    return isinstance(x, (list, tuple))

def poly_list(x: Any) -> Any:
    if poly_islist(x): return x
    if isinstance(x, dict): return [(key, x[key]) for key in sorted(x)]
    return None if x is None else [x]
