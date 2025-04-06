"""
Implementations of an "in", "not in", "contains any" and "contains all" functions.
These can work on collections, dictionaries, strings and to some extent
scalar values.
"""

from typing import Any

from .common import NoneType

def poly_in(x: Any, y: Any) -> Any:
    return _is_in(x, y, False)

def poly_not_in(x: Any, y: Any) -> Any:
    if isinstance(x, (list, tuple)):
        return all(poly_not_in(x1, y) for x1 in x)
    if not isinstance(x, (NoneType, bool, int, str, float)):
        raise TypeError(f'Cannot use {type(x)} with an in/contains operation')
    if isinstance(y, str):
        return not (isinstance(x, str) and x in y)
    if isinstance(y, (list, tuple)):
        return x not in y
    if isinstance(y, dict):
        return x not in y.keys()
    # try a scalar comparison
    return not (isinstance(x, type(y)) and x == y)

def poly_contains_any(x: Any, y: Any) -> Any:
    return _is_in(y, x, False)

def poly_contains_all(x: Any, y: Any) -> Any:
    return _is_in(y, x, True)

def _is_in(x: Any, y: Any, do_all: bool) -> Any:
    print(f'_is_in({repr(x)}, {repr(y)})') # TODO
    if isinstance(x, (list, tuple)):
        if do_all: return all(_is_in(x1, y, do_all) for x1 in x)
        return any(_is_in(x1, y, do_all) for x1 in x)
    if not isinstance(x, (NoneType, bool, int, str, float)):
        raise TypeError(f'Cannot use {type(x)} with an in/contains operation')
    if isinstance(y, str):
        return isinstance(x, str) and x in y
    if isinstance(y, (list, tuple)):
        return x in y
    if isinstance(y, dict):
        return x in y.keys()
    # try a scalar comparison
    return isinstance(x, type(y)) and x == y
