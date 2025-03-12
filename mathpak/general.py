#! /usr/bin/python3

from .common import str_to_number
from collections.abc import Iterable
from typing import Any, Callable
import sys

def poly_hash(x: Any) -> int: return hash(x)
def poly_repr(x: Any) -> str: return repr(x)
def poly_class(x: Any) -> str: return None if x is None else x.__class__.__name__
def poly_type(x: Any) -> str: return type(x).__name__
def poly_len(x: Any) -> bool: return len(x) if hasattr(x, '__len__') else None

def poly_sort(x: Any) -> Any: return _sorted(x, False)
def poly_rsort(x: Any) -> Any: return _sorted(x, True)

def poly_isempty(x: Any) -> bool:
    if isinstance(x, str): return not x or not x.strip()
    return x == None or not x

def poly_sizeof(x: Any) -> int:
    """Recursively calculates the size of an object and all its contents"""
    base: int = sys.getsizeof(x)
    if isinstance(x, (list, tuple, set, dict)): return base + sum(poly_sizeof(x1) for x1 in x)
    if isinstance(x, dict): return base + sum(poly_sizeof(key) + poly_sizeof(value) for key, value in x.items())
    return base

def poly_getitem(x:Any, index: Any) -> Any:
    if x == None or isinstance(x, (int, float, str)): return x
    if isinstance(x, (list, tuple)):
        if isinstance(index, list): return _dist_list(poly_getitem, x, index)
        if isinstance(index, tuple): return _dist_tuple(poly_getitem, x, index)
        i: int = int(index) if isinstance(index, (int, float)) else str_to_number(index) if isinstance(index, str) else None
        return x[i] if i != None and i >= 0 and i < len(x) else None
    if isinstance(x, dict):
        # TODO look up by keys?
        return None
    raise TypeError(f'Unsupported type: {type(x)}')

def poly_firstitem(x: Any) -> Any: return poly_getitem(x, 0)

def poly_lastitem(x: Any) -> Any:
    if x == None or isinstance(x, (int, float, str)): return x
    if isinstance(x, (list, tuple)): return x[-1] if len(x) > 0 else None
    if isinstance(x, dict): return None
    raise TypeError(f'Unsupported type: {type(x)}')

def poly_unique(x: Any) -> Any:
    if isinstance(x, str): return poly_unique(x.encode()).decode()
    if not _is_iterable(x): return x
    unique: set = set()
    # By iterating over the collection, we preserve order in the original collection
    # If we've not seen it before, we add to the return
    return type(x)(x1 for x1 in x if x1 not in unique and not unique.add(x1))

def _dist_list(op: Callable[[Any, Any], Any], x: Any, y: list) -> list: return [op(x, y1) for y1 in y]
def _dist_tuple(op: Callable[[Any, Any], Any], x: Any, y: list) -> tuple: return tuple(op(x, y1) for y1 in y)
def _is_iterable(x: Any) -> bool: return isinstance(x, Iterable) and not isinstance(x, str)
def _sorted(x:Any, reverse: bool) -> Any:
    if isinstance(x, str): return _sorted(x.encode(), reverse).decode()
    return type(x)(sorted(x, reverse=reverse)) if _is_iterable(x) else x
