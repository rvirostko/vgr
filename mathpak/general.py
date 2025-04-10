from functools import cmp_to_key
from typing import Any
import sys

from .common import str_to_number, type_str, bool_arg, dist_x
from .inequ import poly_lt, poly_gt, poly_eq, poly_ne

def poly_hash(x: Any) -> int:
    return hash(x)

def poly_repr(x: Any) -> str:
    return repr(x)

def poly_type(x: Any) -> str:
    return type(x).__name__

def poly_len(x: Any) -> bool:
    return len(x) if hasattr(x, '__len__') else None

def poly_sort(x: Any, unique: bool=False, reverse: bool=False) -> Any:
    """
    Sort with unique and reverse
    """
    unique = False if unique is None else bool_arg(unique, 'Unique')
    reverse = False if reverse is None else bool_arg(reverse, 'Reverse')
    if isinstance(x, str): return poly_sort(x.encode(), unique, reverse).decode()
    if isinstance(x, (list, tuple)):
        rc = type(x)(sorted(x, key=cmp_to_key(_cmp_to_key_asc), reverse=reverse))
        return _unique_sorted(rc) if unique else rc
    return x

def poly_isempty(x: Any) -> bool:
    if isinstance(x, str): return x is None or len(x) == 0 or x.isspace()
    return x is None or not x

def poly_sizeof(x: Any) -> int:
    """Recursively calculates the size of an object and all its contents"""
    base: int = sys.getsizeof(x)
    if isinstance(x, (list, tuple, set, dict)): return base + sum(poly_sizeof(x1) for x1 in x)
    if isinstance(x, dict): return base + sum(poly_sizeof(key) + poly_sizeof(value) for key, value in x.items())
    return base

def poly_getitem(x:Any, index: Any) -> Any:
    if x is None or isinstance(x, (int, float, str)): return x
    if isinstance(x, (list, tuple)):
        if isinstance(index, (list, tuple)): return dist_x(poly_getitem, x, index)
        i: int = int(index) if isinstance(index, (int, float)) else str_to_number(index) if isinstance(index, str) else None
        return x[i] if i is not None and i >= 0 and i < len(x) else None
    if isinstance(x, dict):
        # TODO look up by keys?
        return None
    raise TypeError(f'Unsupported type: {type_str(x)}')

def poly_firstitem(x: Any) -> Any:
    return poly_getitem(x, 0)

def poly_lastitem(x: Any) -> Any:
    if x is None or isinstance(x, (int, float, str)): return x
    if isinstance(x, (list, tuple)): return x[-1] if len(x) > 0 else None
    if isinstance(x, dict): return None
    raise TypeError(f'Unsupported type: {type_str(x)}')

def poly_unique(x: Any) -> Any:
    """A unique that can work with unsorted items"""
    if isinstance(x, str): return poly_unique(x.encode()).decode()
    if isinstance(x, (list, tuple)):
        unique = []
        for x1 in x:
            if not any(poly_eq(x1, existing) for existing in unique):
                unique.append(x1)
        return unique if isinstance(x, list) else tuple(unique)
    return x

def dsort(data: dict, keys: list[str], ascending: list[bool], unique: bool, unique_cols: list[str]) -> list:
    """
    Sort by fields in a list of dictionary
    Also unique support
    """
    keys = _check_keys(keys, 'Sort Key')
    if ascending is None or len(ascending) == 0:
        ascending = [True] * len(keys)
    else:
        ascending = _check_sort_dir(ascending)
        if len(ascending) != len(keys):
            raise ValueError('Length of Ascending and Keys must match')
    unique = bool_arg(unique, 'Unique')
    unique_cols = _check_keys(unique_cols, 'Unique Key') if unique else []
    def compare_keys(x: dict, y: dict):
        for key, asc in zip(keys, ascending):
            vx, vy = x.get(key), y.get(key)
            if not asc: vx, vy = vy, vx
            rc = _cmp_to_key_asc(vx, vy)
            if rc != 0: return rc
        return 0
    rc = sorted(data, key=cmp_to_key(compare_keys))
    return _unique_sorted_dict(rc, unique_cols) if unique else rc

def _check_keys(keys: list[str], name: str):
    if keys is None or not keys:
        raise ValueError(f'{name} may not be empty')
    if not isinstance(keys, (list, tuple)):
        raise TypeError(f'For {name} expected list, found {type_str(keys)}')
    for i, s in enumerate(keys):
        if not isinstance(s, str):
            raise TypeError(f'{name}[{i}]: expected string, found {type_str(s)}')
        s = s.strip()
        if not s:
            raise ValueError(f'{name}[{i}]: expected string, found blank')
    return keys

def _check_sort_dir(lst: list[bool]) -> list[bool]:
    if not isinstance(lst, (list, tuple)):
        raise TypeError(f'Sort Direction: expected list, found {type_str(lst)}')
    result = []
    for i, val in enumerate(lst):
        if val is None:
            result.append(False)
        elif isinstance(val, bool):
            result.append(val)
        else:
            raise TypeError(f"Sort Direction[{i}]: expected boolean, found {type_str(val)}")
    return result

def _cmp_to_key_asc(x: Any, y: Any):
    """For ascending comparisons; reverse x/y for descending"""
    return -1 if poly_lt(x, y) else (1 if poly_gt(x, y) else 0)

def _unique_sorted(x: list):
    """Special pupose unique for a sorted iterable"""
    if not x : return x
    unique = [x[0]]
    for curr in x[1:]:
        if poly_ne(curr, unique[-1]):
            unique.append(curr)
    return unique if isinstance(x, list) else type(x)(unique)

def _unique_sorted_dict(x: list, keys: list) -> list:
    """Special pupose unique for a sorted iterable or dictionaries"""
    if not x: return x
    unique = [x[0]]
    for curr in x[1:]:
        prev = unique[-1]
        if any(poly_ne(curr[key], prev[key]) for key in keys):
            unique.append(curr)
    return unique
