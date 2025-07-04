"""
Operators that match part or all of a regular expression.
Includes case independent variations.
"""

from typing import Any
import re

from .common import NoneType, bool_arg, type_str

def poly_matches(x: Any, *args) -> Any:
    if not args: return x
    if len(args) == 1: return _matches(x, args[0])
    return _matches(x, [*args])

def _matches(x: Any, y: Any, ci: bool=False) -> Any:
    return _do_match(x, y, ci, False)

def poly_matches_all(x: Any, *args) -> Any:
    if not args: return x
    if len(args) == 1: return _matches_all(x, args[0])
    return _matches_all(x, [*args])

def _matches_all(x: Any, y: Any, ci: bool=False) -> Any:
    return _do_match(x, y, ci, True)

def poly_not_matches(x: Any, y: Any, ci: bool=False) -> Any:
    return not _matches(x, y, ci)

def poly_imatches(x: Any, y: Any) -> Any:
    return _matches(x, y, True)

def poly_not_imatches(x: Any, y: Any) -> Any:
    return not _matches(x, y, True)

def _do_match(x: Any, y: Any, ci: bool, do_all: bool) -> Any:
    ci = bool_arg(ci, "Case Independent")
    # None Matches <Any> and None Matches None
    if x is None: return y is None
    # <Any> Matches None
    if y is None: return False
    # ["aaa", "bb"] Matches "^(a|b)+$" -> True
    if isinstance(x, (list, tuple)):
        return all(_do_match(x1, y, ci, do_all) for x1 in x)
    # 27 Matches 27.0 -> True
    if isinstance(x, (NoneType, bool, int, float)):
        if isinstance(y, (NoneType, bool, int, float)): return x == y
    # a_dictionary Matches "abc" -> Exception
    if not isinstance(x, str):
        raise TypeError(f'Cannot perform Match on {type_str(x)}')
    if isinstance(y, str):
        try:
            y = re.compile(y, re.IGNORECASE if ci else 0)
        except Exception as e:
            raise ValueError(f'Match Pattern error: {repr(y)}') from e
    # "Ziggy" Matches "^Z" -> True
    if isinstance(y, re.Pattern):
        return re.search(y, x) is not None
    # "Bobby" Matches ["Rob", "Bob"] -> True
    if isinstance(y, (list, tuple)):
        if do_all: return all(_do_match(x, y1, ci, do_all) for y1 in y)
        return any(_do_match(x, y1, ci, do_all) for y1 in y)
    raise TypeError(f'Cannot use {type_str(y)} as a Pattern with Match')
