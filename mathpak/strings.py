#! /usr/bin/env python3

from .common import str_to_number
from functools import reduce
from typing import Any, Callable, Type, Iterable

# TODO just inline...
_STR_TYPE = str
_INT_TYPE = int
_FLOAT_TYPE = float

def poly_capitalize(x: Any) -> Any: return x.capitalize() if isinstance(x, str) else _apply(poly_capitalize, x)

def poly_casefold(x: Any) -> Any: return x.casefold() if isinstance(x, str) else _apply(poly_casefold, x)

def poly_isalnum(x: Any) -> bool: return _apply_bool(poly_isalnum, str.isalnum, _STR_TYPE, x)

def poly_isalpha(x: Any) -> bool: return _apply_bool(poly_isalpha, str.isalpha, _STR_TYPE, x)

def poly_isascii(x: Any) -> bool: return _apply_bool(poly_isascii, str.isascii, _STR_TYPE, x)

def poly_isdecimal(x: Any) -> bool: return _apply_bool(poly_isdecimal, str.isdecimal, _STR_TYPE, x)

def poly_isdigit(x: Any) -> bool: return _apply_bool(poly_isdigit, str.isdigit, _STR_TYPE, x)

def poly_isidentifier(x: Any) -> bool: return _apply_bool(poly_isidentifier, str.isidentifier, _STR_TYPE, x)

def poly_islower(x: Any) -> bool: return _apply_bool(poly_islower, str.islower, _STR_TYPE, x)

def poly_isnumeric(x: Any) -> bool: return _apply_bool(poly_isnumeric, str.isnumeric, _STR_TYPE, x)

def poly_isprintable(x: Any) -> bool: return _apply_bool(poly_isprintable, str.isprintable, _STR_TYPE, x)

def poly_isspace(x: Any) -> bool: return _apply_bool(poly_isspace, str.isspace, _STR_TYPE, x)

def poly_istitle(x: Any) -> bool: return _apply_bool(poly_istitle, str.istitle, _STR_TYPE, x)

def poly_isupper(x: Any) -> bool: return _apply_bool(poly_isupper, str.isupper, _STR_TYPE, x)

def poly_lower(x: Any) -> Any: return x.lower() if isinstance(x, str) else _apply(poly_lower, x)

def poly_lstrip(x: Any, chars: Any=None) -> Any: return _apply_arg(poly_lstrip, str.lstrip, _STR_TYPE, x, _STR_TYPE, chars)

def poly_swapcase(x: Any) -> Any: return x.swapcase() if isinstance(x, str) else _apply(poly_swapcase, x)

def poly_title(x: Any) -> Any: return x.title() if isinstance(x, str) else _apply(poly_title, x)

def poly_upper(x: Any) -> Any: return x.upper() if isinstance(x, str) else _apply(poly_upper, x)

def poly_endswith(x: Any, suffix: Any) -> bool: return _all_true(_apply_arg(poly_endswith, _endswith, _STR_TYPE, x, _STR_TYPE, suffix))

def poly_expandtabs(x: Any, tabsize: Any=None) -> Any: return _apply_arg(poly_expandtabs, _expandtabs, _STR_TYPE, x, _INT_TYPE, tabsize)

def poly_removeprefix(x: Any, prefix: Any) -> Any: return _apply_arg(poly_removeprefix, _removeprefix, _STR_TYPE, x, _STR_TYPE, prefix)

def poly_removesuffix(x: Any, suffix: Any) -> Any: return _apply_arg(poly_removesuffix, _removesuffix, _STR_TYPE, x, _STR_TYPE, suffix)

def poly_rstrip(x: Any, chars: Any=None) -> Any: return _apply_arg(poly_rstrip, str.rstrip, _STR_TYPE, x, _STR_TYPE, chars)

def poly_startswith(x: Any, prefix: Any) -> bool: return _all_true(_apply_arg(poly_startswith, _startswith, _STR_TYPE, x, _STR_TYPE, prefix))

def poly_strip(x: Any, chars: Any=None) -> Any: return _apply_arg(poly_strip, str.strip, _STR_TYPE, x, _STR_TYPE, chars)

def poly_leftstr(x: Any, length: Any) -> Any: return _apply_arg(poly_leftstr, _leftstr, _STR_TYPE, x, _INT_TYPE, length)

def poly_rightstr(x: Any, length: Any) -> Any: return _apply_arg(poly_rightstr, _rightstr, _STR_TYPE, x, _INT_TYPE, length)

def poly_substr(x: Any, start: Any, length: Any=1) -> Any:
    if x is None: return None
    start = _cast_arg(_INT_TYPE, start)
    length = _cast_arg(_INT_TYPE, length)
    if isinstance(start, int) and isinstance(length, int):
        if isinstance(x, str): return _leftstr(_rightstr(x, len(x) - start), length)
        if isinstance(x, list): return [poly_substr(x1, start, len) for x1 in x]
        if isinstance(x, tuple): return tuple(poly_substr(x1, start, len) for x1 in x)
    return x

# TODO count/index/rindex dont work well when sub is a collection
# It should act like other distributed ops and return an collection of lengths/pos
# The reason is that the return type (generally) doesn't match the input type
# Needs a diff wrapper than _apply_arg()
def poly_count(x: Any, sub: Any=None) -> Any: return _apply_arg(poly_count, _count, _STR_TYPE, x, _STR_TYPE, sub)

def poly_index(x: Any, sub: Any=None) -> Any: return _apply_arg(poly_index, _index, _STR_TYPE, x, _STR_TYPE, sub)

def poly_rindex(x: Any, sub: Any=None) -> Any: return _apply_arg(poly_rindex, _rindex, _STR_TYPE, x, _STR_TYPE, sub)

def poly_vappend(x: Any, *args) -> Any: return reduce(poly_append, args, x)

def poly_append(x: Any, y: Any) -> Any:
    if x == None: return None if y == None else poly_append('', y)
    if y == None: return poly_append(x, '')
    # NB: non-string like behavior
    if isinstance(x, (list, tuple)) and isinstance(y, (list, tuple)): return type(x)(x + y)
    if isinstance(x, str) and isinstance(y, str): return x + y
    if isinstance(x, (int, float)): return poly_append(str(x), y)
    if isinstance(y, (int, float)): return poly_append(x, str(y))
    if isinstance(x, list): return [poly_append(x1, y) for x1 in x]
    if isinstance(x, tuple): return (poly_append(x1, y) for x1 in x)
    if isinstance(y, (list, tuple)): return reduce(poly_append, y, x)
    raise TypeError(f'Concatenation between {type(x)} and {type(y)} not supported')

def poly_vprepend(x: Any, *args) -> Any: return reduce(poly_prepend, args, x)

def poly_prepend(x: Any, y: Any) -> Any:
    if x == None: return None if y == None else poly_prepend('', y)
    if y == None: return poly_prepend(x, '')
    # NB: non-string like behavior
    if isinstance(x, (list, tuple)) and isinstance(y, (list, tuple)): return type(x)(y + x)
    if isinstance(x, str) and isinstance(y, str): return y + x
    if isinstance(x, (int, float)): return poly_prepend(str(x), y)
    if isinstance(y, (int, float)): return poly_prepend(x, str(y))
    if isinstance(x, list): return [poly_prepend(x1, y) for x1 in x]
    if isinstance(x, tuple): return (poly_prepend(x1, y) for x1 in x)
    if isinstance(y, (list, tuple)): return reduce(poly_prepend, y, x)
    raise TypeError(f'Concatenation between {type(x)} and {type(y)} not supported')

def poly_replace(x: Any, old: Any, new: Any=None) -> Any:
    if x != None and old != None:
        if isinstance(x, str):
            if isinstance(old, (int, float)): return poly_replace(x, str(old), new)
            if isinstance(old, str):
                if new == None: new = ''
                if isinstance(new, (int, float)): new = str(new)
                if isinstance(new, str): return x.replace(old, new)
                if isinstance(new, (list, tuple)): return poly_replace(x, (old,), new)
            if isinstance(old, (list, tuple)):
                if new == None: new = ''
                if isinstance(new, (int, float)): new = str(new)
                if isinstance(new, (str, list, tuple)):
                    return reduce(lambda t, args: t.replace(args[0], args[1]), zip(old, _create_new_list(len(old), new)), x)
        else:
            if isinstance(x, (int, float)): return poly_replace(str(x), old, new)
            if isinstance(x, list): return [poly_replace(x1, old, new) for x1 in x]
            if isinstance(x, tuple): return (poly_replace(x1, old, new) for x1 in x)
    return x

def poly_translate(x: Any, from_str: Any, to_str: Any=None) -> Any:
    if x != None and from_str != None:
        if isinstance(x, str):
            # A lot of assumptions here, but we'll try to use it as requested
            # This would be a good case for somebody to make a JSON object (or save it)
            # and do a Load-From into a top-level object
            if isinstance(from_str, dict): return x.translate(from_str)
            if isinstance(from_str, (int, float)): return poly_translate(x, str(from_str), to_str)
            if isinstance(from_str, str):
                if to_str == None: to_str = ''
                if isinstance(to_str, (int, float)): new = str(to_str)
                if isinstance(to_str, str): return x.translate(_maketrans(from_str, to_str))
        else:
            if isinstance(x, (int, float)): return poly_translate(str(x), from_str, to_str)
            if isinstance(x, list): return [poly_translate(x1, from_str, to_str) for x1 in x]
            if isinstance(x, tuple): return (poly_translate(x1, from_str, to_str) for x1 in x)
    return x

# Shim methods to deal with "None" and mismatched arguments

def _expandtabs(x: str, tabsize: int) -> str: return x.expandtabs() if tabsize == None else x.expandtabs(tabsize)

def _removeprefix(x: str, prefix: str) -> str: return x if prefix == None else x.removeprefix(prefix)

def _removesuffix(x: str, suffix: str) -> str: return x if suffix == None else x.removesuffix(suffix)

def _startswith(x: str, prefix: str) -> bool: return False if prefix == None else x.startswith(prefix)

def _endswith(x: str, suffix: str) -> bool: return False if suffix == None else x.endswith(suffix)

def _count(x: str, sub: str) -> int: return 0 if not sub else x.count(sub)

def _index(x: str, sub: str) -> int:
    try: return -1 if not sub else x.index(sub)
    except ValueError: return -1

def _rindex(x: str, sub: str) -> int:
    try: return -1 if not sub else x.rindex(sub)
    except ValueError: return -1

def _maketrans(from_str: str, to_str: str=''):
    return str.maketrans({from_str[i]: to_str[i] if i < len(to_str) else None for i in range(len(from_str))})

def _leftstr(x: str, length: int) -> str: return x if not x or length == None else '' if length <= 0 else x[:max(0, min(length, len(x)))]

def _rightstr(x: str, length: int) -> str: return x if not x or length == None else '' if length <= 0 else x[-min(length, len(x)):]

def _create_new_list(length: int, new: Any):
    if isinstance(new, str): return (new,) * length
    # Either chop to length or pad with empty entries
    if isinstance(new, (list, tuple)): return tuple(new[:length]) + ('',) * max(0, length - len(new))
    raise TypeError(f'Type {type(new).__name__} not supported for string replace')

def _cast_arg(y_type: Type, y: Any) -> Any:
    if y is None: return None
    if y_type == _STR_TYPE: return str(y)
    if y_type == _FLOAT_TYPE:
        if isinstance(y, (float, int)): return float(y)
        if isinstance(y, str): return float(str_to_number(y))
    if y_type == _INT_TYPE:
        if isinstance(y, (float, int)): return int(y)
        if isinstance(y, str): return int(str_to_number(y))
    return y

def _apply(op: Callable[[Any], Any], x: Any) -> Any:
    if x is None: return None
    # Distribute the operation over the collection
    if isinstance(x, list): return [op(x1) for x1 in x]
    if isinstance(x, tuple): return tuple(op(x) for x1 in x)
    return x

def _apply_arg(op: Callable[[Any, Any], Any], x_method: Callable[[str, str], str], x_type: Type, x: Any, y_type: Type, y: Any) -> Any:
    if x is None: return None
    y = _cast_arg(y_type, y)
    if isinstance(x, x_type):
        return x_method(x, y) if y == None or isinstance(y, y_type) else _iterate_arg(op, x, y)
    if isinstance(x, list): return [op(x1, y) for x1 in x]
    if isinstance(x, tuple): return tuple(op(x1, y) for x1 in x)
    return x

def _iterate_arg(op: Callable[[Any, Any], Any], x: Any, y: Any) -> Any:
    # if the second operand is a collection, repeatedly apply it to the first operand
    if isinstance(y, (list, tuple)):
        for y1 in y: x = op(x, y1)
    return x

def _all_true(x: Any) -> bool:
    if isinstance(x, bool): return x
    if isinstance(x, Iterable) and not isinstance(x, (str, bytes)): return all(_all_true(item) for item in x)
    return False

def _apply_bool(op: Callable[[Any, Any], Any], x_method: Callable[[str], bool], x_type: list[Type], x: Any) -> bool:
    return _all_true(x_method(x) if isinstance(x, x_type) else _apply(op, x))

#   1.	center(width, fillchar=' ')
#	7.	ljust(width, fillchar=' ')
#	15.	rjust(width, fillchar=' ')

#	5.	find(sub, start=0, end=len(string))
#	13.	rfind(sub, start=0, end=len(string))

#	9.	partition(sep)
#	16.	rpartition(sep)

#	18.	split(sep=None, maxsplit=-1)
#	19.	splitlines(keepends=False)
