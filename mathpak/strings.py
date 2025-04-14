"""
Various string manipulation functions using either the string class or regular expressions
"""

from functools import reduce
from typing import Any, Callable
import re

from .common import X_None_Op, NoneType, Y_Coll_Op, str_arg, int_arg, type_str
from .general import poly_isempty
from .reg_ex import poly_regex_replace, poly_vregex_replace
from .types import poly_str

TNone = type(None)
# No-args string method that returns a string, e.q. "x.upper()"
# This is transformational on string items, but idempotent on others
# ["bob", 27, True].upper() -> ["BOB", 27, True]
string_operations = {
    TNone: lambda _, __, ___: None,
    bool:  lambda _, x, __: x,
    int:   lambda _, x, __: x,
    float: lambda _, x, __: x,
    str:   lambda _, x, sm: sm(x),
    list:  lambda op, x, _: [op(x1) for x1 in x ],
    tuple: lambda op, x, _: tuple(op(x1) for x1 in x),
    dict:  lambda op, x, _: {key: op(value) for key, value in x.items()}
}

# No-args string method that returns a bool, e.q. "x.isupper()"
# This is a conversion to bool on string items, but returning None for others
# ["BOB", 27, True].upper() -> [True, None, None]
bool_operations = {
    TNone: lambda _, __, ___: None,
    bool:  lambda _, x, __: None,
    int:   lambda _, x, __: None,
    float: lambda _, x, __: None,
    str:   lambda _, x, sm: sm(x),
    list:  lambda op, x, _: [op(x1) for x1 in x ],
    tuple: lambda op, x, _: tuple(op(x1) for x1 in x),
    dict:  lambda op, x, _: {key: op(value) for key, value in x.items() if isinstance(value, (str, list, tuple, dict))}
}

def exec_x_op(x: Any, name: str, op: Callable[[Any], Any], string_op, op_table) -> Any:
    """General purpose string operation execution for no-args methods on str"""
    operation = op_table.get(type(x))
    if operation is None: raise ValueError(f'{name}() on {type_str(x)} not possible')
    return operation(op, x, string_op)

def exec_str_op(x: Any, name: str, op: Callable[[Any], Any], string_op) -> Any:
    return exec_x_op(x, name, op, string_op, string_operations)

def exec_bool_op(x: Any, name: str, op: Callable[[Any], Any], string_op) -> Any:
    return exec_x_op(x, name, op, string_op, bool_operations)

def poly_capitalize(x: Any) -> Any:
    return exec_str_op(x, 'Capitalize', poly_capitalize, str.capitalize)

def poly_casefold(x: Any) -> Any:
    return exec_str_op(x, 'Casefold', poly_casefold, str.casefold)

def poly_lower(x: Any) -> Any:
    return exec_str_op(x, 'Lower', poly_lower, str.lower)

def poly_swapcase(x: Any) -> Any:
    return exec_str_op(x, 'SwapCase', poly_swapcase, str.swapcase)

def poly_title(x: Any) -> Any:
    return exec_str_op(x, 'Title', poly_title, str.title)

def poly_upper(x: Any) -> Any:
    return exec_str_op(x, 'Upper', poly_upper, str.upper)

def poly_isalnum(x: Any) -> Any:
    return exec_bool_op(x, 'IsAlnum', poly_isalnum, str.isalnum)

def poly_isalpha(x: Any) -> Any:
    return exec_bool_op(x, 'IsAlpha', poly_isalpha, str.isalpha)

def poly_isascii(x: Any) -> Any:
    return exec_bool_op(x, 'IsAscii', poly_isascii, str.isascii)

def poly_isdecimal(x: Any) -> Any:
    return exec_bool_op(x, 'IsDecimal', poly_isdecimal, str.isdecimal)

def poly_isdigit(x: Any) -> Any:
    return exec_bool_op(x, 'IsDigit', poly_isdigit, str.isdigit)

def poly_isidentifier(x: Any) -> Any:
    return exec_bool_op(x, 'IsIdentifier', poly_isidentifier, str.isidentifier)

def poly_islower(x: Any) -> Any:
    return exec_bool_op(x, 'IsLower', poly_islower, str.islower)

def poly_isnumeric(x: Any) -> Any:
    return exec_bool_op(x, 'IsNumeric', poly_isnumeric, str.isnumeric)

def poly_isprintable(x: Any) -> Any:
    return exec_bool_op(x, 'IsPrintable', poly_isprintable, str.isprintable)

def poly_isspace(x: Any) -> Any:
    return exec_bool_op(x, 'IsSpace', poly_isspace, str.isspace)

def poly_istitle(x: Any) -> Any:
    return exec_bool_op(x, 'IsTitle', poly_istitle, str.istitle)

def poly_isupper(x: Any) -> Any:
    return exec_bool_op(x, 'IsUpper', poly_isupper, str.isupper)

####

# For two arg functions : e.g. x.strip(y)/(None)
# [" xFoo ", None, 27, True].strip() -> ["xFoo", None, 27, True]
# ["xFoo", None, 27, True].strip("x") -> ["Foo", None, 27, True]
# [" xFoo ", None, 27, True].strip([None, "x"]) -> ["Foo", None, 27, True]
string_string_operations = {
    X_None_Op    : lambda _, __, ___, ____: None,
    Y_Coll_Op    : lambda op, x, y, _: reduce(op, y, x),
    (str, str)   : lambda _, x, y, sm: sm(x, y),
    (list, str)  : lambda op, x, y, _: [op(x1, y) for x1 in x],
    (tuple, str) : lambda op, x, y, _: tuple(op(x1, y) for x1 in x),
    (dict, str)  : lambda op, x, y, _: {key: op(value, y) for key, value in x.items()},
}

def exec_x_y_op(x: Any, y: Any, name: str, op: Callable[[Any, Any], Any], string_op, op_table) -> Any:
    """General purpose string operation execution for methods on str that take a single str arg"""
    operation = None
    if x is None:
        operation = op_table.get(X_None_Op)
    else:
        if isinstance(y, (list, tuple)):
            operation = op_table.get(Y_Coll_Op)
        else:
            # May ops will accept a None for their arg and take default action
            # So we use the same as if it was a string
            operation = op_table.get((type(x), str if y is None else type(y)))
    if operation is None: raise ValueError(f'{name}() between {type_str(x)} and {type_str(y)} not possible')
    return operation(op, x, y, string_op)

def exec_str_str_op(x: Any, y: Any, name: str, op: Callable[[Any, Any], Any], string_op) -> Any:
    # For these types, the operation is idempotent
    if isinstance(x, (NoneType, bool, int, float)): return x
    return exec_x_y_op(x, y, name, op, string_op, string_string_operations)

####
# str/str transformational

def poly_vstrip(x: Any, *args) -> Any:
    if isinstance(x, (NoneType, bool, int, float)): return x
    if not args: return poly_strip(x)
    return reduce(poly_strip, args, x)

def poly_strip(x: Any, chars: Any=None) -> Any:
    return exec_str_str_op(x, chars, 'Strip', poly_strip, str.strip)

def poly_vlstrip(x: Any, *args) -> Any:
    if isinstance(x, (NoneType, bool, int, float)): return x
    if not args: return poly_lstrip(x)
    return reduce(poly_lstrip, args, x)

def poly_lstrip(x: Any, chars: Any=None) -> Any:
    return exec_str_str_op(x, chars, 'LeftStrip', poly_lstrip, str.lstrip)

def poly_vrstrip(x: Any, *args) -> Any:
    if isinstance(x, (NoneType, bool, int, float)): return x
    if not args: return poly_rstrip(x)
    return reduce(poly_rstrip, args, x)

def poly_rstrip(x: Any, chars: Any=None) -> Any:
    return exec_str_str_op(x, chars, 'RightStrip', poly_rstrip, str.rstrip)

def poly_vremoveprefix(x: Any, *args) -> Any:
    if not args or isinstance(x, (NoneType, bool, int, float)): return x
    return reduce(poly_removeprefix, args, x)

def poly_removeprefix(x: Any, prefix: Any) -> Any:
    if prefix is None: return x
    return exec_str_str_op(x, prefix, 'RemovePrefix', poly_removeprefix, str.removeprefix)

def poly_vremovesuffix(x: Any, *args) -> Any:
    if not args or isinstance(x, (NoneType, bool, int, float)): return x
    return reduce(poly_removesuffix, args, x)

def poly_removesuffix(x: Any, suffix: Any) -> Any:
    if suffix is None: return x
    return exec_str_str_op(x, suffix, 'RemoveSuffix', poly_removesuffix, str.removesuffix)

# [" xFoo ", None, 27, True].startswith("x") -> [False, None, None, None]
# ["xFoo", None, 27, True].startwith("x") -> [True, None, None, None]
bool_string_operations = {
    (str, str)   : lambda _, x, y, sm: sm(x, y),
    (list, str)  : lambda op, x, y, _: [op(x1, y) for x1 in x],
    (tuple, str) : lambda op, x, y, _: tuple(op(x1, y) for x1 in x),
    (dict, str)  : lambda op, x, y, _: {key: op(value, y) for key, value in x.items() if isinstance(value, (str, list, tuple, dict))},
}

def exec_bool_str_op(x: Any, y: Any, name: str, op: Callable[[Any, Any], Any], string_op) -> Any:
    # For these types, the operation is indeterminent
    if isinstance(x, (NoneType, bool, int, float)): return None
    return exec_x_y_op(x, y, name, op, string_op, bool_string_operations)

####
# str/str that return bools

def poly_startswith(x: Any, prefix: Any) -> Any:
    if prefix is None: return x is None
    return exec_bool_str_op(x, prefix, "StartsWith", poly_startswith, str.startswith)

def poly_endswith(x: Any, suffix: Any) -> bool:
    if suffix is None: return x is None
    return exec_bool_str_op(x, suffix, "EndsWith", poly_endswith, str.endswith)

# "abc".leftstr(2) -> "ab"
# 2.leftstr(2).leftstr(2) -> 2
# ["abc", 2].leftstr(2) -> ["ab", 2]
string_int_operations = {
    (str, int)   : lambda _, x, y, sm: sm(x, y),
    (list, int)  : lambda op, x, y, _: [op(x1, y) for x1 in x],
    (tuple, int) : lambda op, x, y, _: tuple(op(x1, y) for x1 in x),
    (dict, int)  : lambda op, x, y, _: {key: op(value, y) for key, value in x.items()},
}

def exec_str_int_op(x: Any, y: Any, name: str, op: Callable[[Any, Any], Any], string_op) -> Any:
    # For these types, the operation is idempotent
    if isinstance(x, (NoneType, bool, int, float)): return x
    return exec_x_y_op(x, y, name, op, string_op, string_int_operations)

def poly_expandtabs(x: Any, tabsize: Any=None) -> Any:
    return exec_str_int_op(x, min(max(1, int_arg(tabsize, 'Tabsize')), 16), "ExpandTabs", poly_expandtabs, str.expandtabs)

def poly_leftstr(x: Any, length: Any) -> Any:
    return exec_str_int_op(x, max(0, int_arg(length, 'Length')), "LeftStr", poly_leftstr, lambda x, length: x[:length])

def poly_rightstr(x: Any, length: Any) -> Any:
    return exec_str_int_op(x, max(0, int_arg(length, 'Length')), "RightStr", poly_rightstr, lambda x, length: x[-length:])

####

def poly_substr(x: Any, start: Any, length: Any=1) -> Any:
    # For these types, the operation is idempotent
    if isinstance(x, (NoneType, bool, int, float)): return x
    start = max(0, int_arg(start, 'Start'))
    length = 1 if length is None else max(0, int_arg(length, 'Length'))
    if isinstance(x, str): return x[start:start + length]
    if isinstance(x, (list, tuple)): return type(x)(poly_substr(x1, start, length) for x1 in x)
    if isinstance(x, dict): return {key: poly_substr(value, start, length) for key, value in x.items()}
    raise ValueError(f'SubStr() on {type_str(x)} not possible')

string_loc_operations = {
    (str, str)   : lambda _, x, y, sm: sm(x, y),
    (list, str)  : lambda op, x, y, _: [op(x1, y) for x1 in x],
    (tuple, str) : lambda op, x, y, _: tuple(op(x1, y) for x1 in x),
    (dict, str)  : lambda op, x, y, _: {key: op(value, y) for key, value in x.items() if isinstance(value, (str, list, tuple, dict))},
}

def poly_count(x: Any, sub: Any=None) -> Any:
    # For these types, the operation is indeterminant
    if isinstance(x, (NoneType, bool, int, float)): return None
    return exec_x_y_op(x, str_arg(sub, 'Sub'), 'Count', poly_count, str.count, string_loc_operations)

# TODO replace "indexof" which suxs
#	5.	find(sub, start=0, end=len(string))
#	13.	rfind(sub, start=0, end=len(string))


def poly_index(x: Any, sub: Any=None) -> Any:
    # For these types, the operation is indeterminant
    if isinstance(x, (NoneType, bool, int, float)): return None
    sub = str_arg(sub, 'Sub')
    try:
        return exec_x_y_op(x, sub, 'Index', poly_index, str.index, string_loc_operations)
    except ValueError:
        return None

def poly_rindex(x: Any, sub: Any=None) -> Any:
    # For these types, the operation is indeterminant
    if isinstance(x, (NoneType, bool, int, float)): return None
    sub = str_arg(sub, 'Sub')
    try:
        return exec_x_y_op(x, sub, 'RIndex', poly_rindex, str.rindex, string_loc_operations)
    except ValueError:
        return None

###

def _layout_opt(x: Any, width: int, fillchar: str, op, str_op) -> Any:
    width = 0 if width is None else min(max(0, int_arg(x, "Width")), 256)
    fillchar = '' if fillchar is None else str_arg(fillchar, "Fillchar")[0]
    if x is None: return fillchar * width
    if isinstance(x, (list, tuple)): return type(x)(op(x1, width, fillchar) for x1 in x)
    if isinstance(x, (bool, int, float, dict)): x = poly_str(x)
    return str_op(x, width, fillchar)

def poly_center(x: Any, width: int, fillchar: str=' ') -> Any:
    return _layout_opt(x, width, fillchar, poly_center, str.center)

def poly_ljust(x: Any, width: int, fillchar: str=' ') -> Any:
    return _layout_opt(x, width, fillchar, poly_ljust, str.ljust)

def poly_rjust(x: Any, width: int, fillchar: str=' ') -> Any:
    return _layout_opt(x, width, fillchar, poly_rjust, str.rjust)

def poly_zfill(x: Any, width: int) -> Any:
    return poly_rjust(x, width, '0')

###

def poly_vappend(x: Any, *args) -> Any:
    return reduce(poly_append, args, x)

def poly_append(x: Any, y: Any) -> Any:
    # For these types, the operation is idempotent
    if isinstance(x, (NoneType, bool, int, float)) or y is None: return x
    if isinstance(x, (list, tuple)): return type(x)(poly_append(x1, y) for x1 in x)
    if isinstance(x, dict): return  {key: poly_append(value, y) for key, value in x.items()}
    if isinstance(x, str):
        if isinstance(y, (list, tuple)): return reduce(poly_append, y, x)
        if isinstance(y, (bool, int, float)): return x + str(y)
        if isinstance(y, str): return x + y
    raise TypeError(f'Concatenation between {type_str(x)} and {type_str(y)} not supported')

def poly_vprepend(x: Any, *args) -> Any:
    return reduce(poly_prepend, args, x)

def poly_prepend(x: Any, y: Any) -> Any:
    # For these types, the operation is idempotent
    if isinstance(x, (NoneType, bool, int, float)) or y is None: return x
    if isinstance(x, (list, tuple)): return type(x)(poly_prepend(x1, y) for x1 in x)
    if isinstance(x, dict): return  {key: poly_prepend(value, y) for key, value in x.items()}
    if isinstance(x, str):
        if isinstance(y, (list, tuple)): return reduce(poly_prepend, y, x)
        if isinstance(y, (bool, int, float)): return str(y) + x
        if isinstance(y, str): return y + x
    raise TypeError(f'Concatenation between {type_str(x)} and {type_str(y)} not supported')

def poly_vreplace(x: Any, *args) -> Any:
    if not args: return x
    if isinstance(args[0], re.Pattern): return poly_vregex_replace(x, args)
    if len(args) == 1: return poly_replace(x, args[0]) # old, default new
    if len(args) == 2: return poly_replace(x, args[0], args[1]) # old and new
    return poly_replace(x, args[:-1], args[-1]) # old is a list, single new

def poly_replace(x: Any, old: Any, new: Any=None) -> Any:
    """
    The operation is skipped if x is None or a non-string scalar.
    The operation is skipped in old in None, otherwise it must be a non-empty string, a list, or a tuple.
    If old is a list/tuple, it specifies multiple values to be replaced, but always with
    the same new value.
    Simple stringification is performed on scalars used for old and new.
    """
    # For these types, the operation is idempotent
    if isinstance(x, (NoneType, bool, int, float)): return x
    if isinstance(x, re.Pattern): return poly_regex_replace(x, old, new)
    if old is None: return x
    if new is None: new = ''
    new = str(new) if isinstance(new, (bool, int, float, str)) else str_arg(old, 'New')
    if isinstance(old, (list, tuple)): return reduce(lambda x, old1: poly_replace(x, old1, new), old, x)
    old = str(old) if isinstance(old, (bool, int, float)) else str_arg(old, 'Old')
    if isinstance(x, str): return x.replace(old, new)
    if isinstance(x, (list, tuple)): return type(x)(poly_replace(x1, old, new) for x1 in x)
    if isinstance(x, dict): return {key: poly_replace(value, old, new) for key, value in x.items()}
    raise TypeError(f'Replacement of {type_str(x)} not supported')

def poly_split(x: Any, sep=None, maxsplit=-1) -> Any:
    # For these types, the operation is idempotent
    if isinstance(x, (NoneType, bool, int, float)): return x
    sep = None if sep is None else str_arg(sep, 'Sep')
    maxsplit = -1 if maxsplit is None else max(-1, int_arg(maxsplit, 'Maxsplit'))
    if isinstance(x, str): return x.split(sep, maxsplit)
    if isinstance(x, (list, tuple)): return type(x)(poly_split(x1, sep, maxsplit) for x1 in x)
    if isinstance(x, dict): return {key: poly_split(value, sep, maxsplit) for key, value in x.items()}
    raise TypeError(f'Split of {type_str(x)} not supported')

def poly_rsplit(x: Any, sep=None, maxsplit=-1) -> Any:
    # For these types, the operation is idempotent
    if isinstance(x, (NoneType, bool, int, float)): return x
    sep = None if sep is None else str_arg(sep, 'Sep')
    maxsplit = -1 if maxsplit is None else max(-1, int_arg(maxsplit, 'Maxsplit'))
    if isinstance(x, str): return x.rsplit(sep, maxsplit)
    if isinstance(x, (list, tuple)): return type(x)(poly_rsplit(x1, sep, maxsplit) for x1 in x)
    if isinstance(x, dict): return {key: poly_rsplit(value, sep, maxsplit) for key, value in x.items()}
    raise TypeError(f'Split of {type_str(x)} not supported')

def poly_format(format_string: Any, *args) -> str:
    """
    Formatting syntax is that used in [Python's str.format()](https://docs.python.org/3/library/string.html#formatstrings)
    """
    if format_string is None: return None
    format_string = str(format_string)
    return format_string.format(*args) if not poly_isempty(format_string) else None

def poly_translate(x: Any, from_str: Any, to_str: Any=None) -> Any:
    if x is not None and from_str is not None:
        if isinstance(x, str):
            # A lot of assumptions here, but we'll try to use it as requested
            # This would be a good case for somebody to make a JSON object (or save it)
            # and do a Load-From into a top-level object
            if isinstance(from_str, dict): return x.translate(from_str)
            if isinstance(from_str, (int, float)): return poly_translate(x, str(from_str), to_str)
            if isinstance(from_str, str):
                if to_str is None: to_str = ''
                if isinstance(to_str, (int, float)): return str(to_str)
                if isinstance(to_str, str): return x.translate(_maketrans(from_str, to_str))
        else:
            if isinstance(x, (int, float)): return poly_translate(str(x), from_str, to_str)
            if isinstance(x, list): return [poly_translate(x1, from_str, to_str) for x1 in x]
            if isinstance(x, tuple): return (poly_translate(x1, from_str, to_str) for x1 in x)
    return x

####

def _maketrans(from_str: str, to_str: str=''):
    return str.maketrans({from_str[i]: to_str[i] if i < len(to_str) else None for i in range(len(from_str))})

# TODO candidate funcs
#   1.	center(width, fillchar=' ')
#	7.	ljust(width, fillchar=' ')
#	15.	rjust(width, fillchar=' ')
# zfill()

#	19.	splitlines(keepends=False)
# join
