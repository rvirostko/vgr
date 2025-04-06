"""
Functions using regular expressions
"""

from functools import reduce
from typing import Any
import re

from .common import NoneType

def compile_pattern(x: Any, flags: int=0) -> Any:
    if isinstance(x, (NoneType, re.Pattern)): return x
    if isinstance(x, str):
        try:
            return re.compile(x, flags)
        except Exception as e:
            raise ValueError(f'Pattern error: {repr(x)}') from e
    if isinstance(x, (list, tuple)):
        return type(x)(compile_pattern(x1, flags) for x1 in x)
    raise ValueError(f'Cannot Compile {repr(type(x).__name__)} to a Pattern')

def poly_vregex_replace(x: Any, *args) -> Any:
    if not args: return x
    if len(args) == 1: return poly_regex_replace(x, args[0], '')
    if len(args) == 2: return poly_regex_replace(x, args[0], args[1]) # pattern and replacement
    return poly_regex_replace(x, args[:-1], args[-1]) # pattern is a list, single replacement

def poly_regex_replace(x: Any, pattern: Any, replacement: Any=None) -> Any:
    """
    The input value can be a string, list, tuple, or dictionary.
    Replacement is distributed over list and tuple, and the values of the dictionary.
    The pattern can be a string or a colleciton of strings. For the latter, the patterns all
    applied in order, all using the same replacement.
    Replacement must be a string, but can be empty or None, which results in deletion.
    The pattern can start with (?i) for case indepenent replacement, (?m) for multiline replacement,
    or combined as (?im) for both. Capture groups can be referenced in the replacement.
    """
    # For these types, the operation is idempotent
    if isinstance(x, (NoneType, bool, int, float)) or pattern is None: return x
    if replacement is None:
        replacement = ''
    else:
        if not isinstance(replacement, str):
            raise ValueError(f'RegEx Replacement argument must be a string, found {repr(type(replacement).__name__)}')
    if isinstance(pattern, (list, tuple)):
        return reduce(lambda x, pattern1: poly_regex_replace(x, pattern1, replacement), pattern, x)
    # in case we are going to loop, pre-compile the pattern
    if not isinstance(pattern, re.Pattern):
        if not isinstance(pattern, str):
            raise TypeError(f'Unexpected type for RegEx pattern {type(pattern).__name__}')
        pattern = re.compile(pattern)
    if isinstance(x, str): return re.sub(pattern, replacement, x)
    if isinstance(x, (list, tuple)): return type(x)(poly_regex_replace(x1, pattern, replacement) for x1 in x)
    if isinstance(x, dict): return {key: poly_regex_replace(value, pattern, replacement) for key, value in x.items() }
    raise TypeError(f'RegEx replacement on {type(x).__name__} not supported')
