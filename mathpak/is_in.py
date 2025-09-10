"""
Implementations of an "in", "not in", "contains any" and "contains all" functions.
These can work on collections, dictionaries, strings and to some extent
scalar values.
"""

from typing import Any

from .common import NoneType, bound_ops, type_str

# Impl def and testing req
#   * If x is a collection, should it be distributive (not use all)
#     ["a", "b"] in "a" -> True or [True, False]
#   * If reversed...
#     "a" in ["a", "b"] -> True
#   * If combined...
#     ["a", "b"] in ["c", "a"] -> True or [[False, False], [False, True]]
#   * For "In" and "Not In" the comma in X should be read as "Or"
#   * "In" is read as "any X in Y", so 'Any "a" or "b" in ["c", "a"]'
#   * "ContainsAny" is a reversal of "In"
#     ["c", "a"] Contains ["a", "b"] -> True
#     Read as "Does ["c", "a"] Contain Either "a" or "b"
#   * "ContainsAll" reads as
#     Read as "Does ["c", "a"] Contain Both "a" and "b"
#   * We should have var args for contains to make things easier
#     Print my_coll.ContainsAny("a", "c")
#   * We could introduce an "either use a single array or multiple scalars" for the y value

@bound_ops("In", "Is-In")
def poly_in(x: Any, y: Any) -> Any:
    return _is_in(x, y, False)

@bound_ops("Not-In", "Is-Not-In")
def poly_not_in(x: Any, y: Any) -> Any:
    if isinstance(x, (list, tuple)):
        return all(poly_not_in(x1, y) for x1 in x)
    if not isinstance(x, (NoneType, bool, int, str, float)):
        raise TypeError(f'Cannot use {type_str(x)} with an in/contains operation')
    if isinstance(y, str):
        return not (isinstance(x, str) and x in y)
    if isinstance(y, (list, tuple)):
        return x not in y
    if isinstance(y, dict):
        return x not in y.keys()
    # try a scalar comparison
    return not (isinstance(x, type(y)) and x == y)

@bound_ops("Contains")
def poly_contains_any(x: Any, y: Any) -> Any:
    return _is_in(y, x, False)

@bound_ops("Contains-All")
def poly_contains_all(x: Any, y: Any) -> Any:
    return _is_in(y, x, True)

def _is_in(x: Any, y: Any, do_all: bool) -> Any:
    if isinstance(x, (list, tuple)):
        t = (_is_in(x1, y, do_all) for x1 in x)
        return all(t) if do_all else any(t)
    if not isinstance(x, (NoneType, bool, int, str, float)):
        raise TypeError(f'Cannot use {type_str(x)} with an in/contains operation')
    if isinstance(y, str):
        return isinstance(x, str) and x in y
    if isinstance(y, (list, tuple)):
        return x in y
    if isinstance(y, dict):
        return x in y.keys()
    # try a scalar comparison
    return isinstance(x, type(y)) and x == y
