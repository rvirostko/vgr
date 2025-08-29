"""
Various string manipulation functions using either the string class or regular expressions
"""

from functools import reduce
from typing import Any, Callable
import re

from .common import X_None_Op, NoneType, Y_Coll_Op, str_arg, int_arg, type_str, bool_arg
from .reg_ex import poly_regex_replace
from .types import poly_str

# No-args string method that returns a string, e.q. "x.upper()"
# This is transformational on string items, but idempotent on others
# ["bob", 27, True].upper() -> ["BOB", 27, True]
string_operations = {
    NoneType: lambda _op, _x, _sm: None,
    bool:  lambda _op,  x, _sm: x,
    int:   lambda _op,  x, _sm: x,
    float: lambda _op,  x, _sm: x,
    str:   lambda _op,  x,  sm: sm(x),
    list:  lambda  op,  x, _sm: [op(x1) for x1 in x ],
    tuple: lambda  op,  x, _sm: tuple(op(x1) for x1 in x),
    dict:  lambda  op,  x, _sm: {key: op(value) for key, value in x.items()}
}

# No-args string method that returns a bool, e.q. "x.isupper()"
# This is a conversion to bool on string items, but returning None for others
# ["BOB", 27, True].upper() -> [True, None, None]
bool_operations = {
    NoneType: lambda _op, _x, _sm: None,
    bool:  lambda _op, _x, _sm: None,
    int:   lambda _op, _x, _sm: None,
    float: lambda _op, _x, _sm: None,
    str:   lambda _op,  x,  sm: sm(x),
    list:  lambda  op,  x, _sm: [op(x1) for x1 in x ],
    tuple: lambda  op,  x, _sm: tuple(op(x1) for x1 in x),
    dict:  lambda  op,  x, _sm: {key: op(value) for key, value in x.items() if isinstance(value, (str, list, tuple, dict))}
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

def poly_strlen(x: Any) -> Any:
    return exec_str_op(x, 'StringLen', poly_strlen, str.__len__)

def poly_strrev(x: Any) -> Any:
    return exec_str_op(x, 'StringRev', poly_strrev, lambda s: s[::-1])

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
    X_None_Op    : lambda _op, _x, _y, _sm: None,
    Y_Coll_Op    : lambda  op,  x,  y, _sm: reduce(op, y, x),
    (str, str)   : lambda _op,  x,  y,  sm: sm(x, y),
    (list, str)  : lambda  op,  x,  y, _sm: [op(x1, y) for x1 in x],
    (tuple, str) : lambda  op,  x,  y, _sm: tuple(op(x1, y) for x1 in x),
    (dict, str)  : lambda  op,  x,  y, _sm: {key: op(value, y) for key, value in x.items()},
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

def poly_strip(x: Any, *args) -> Any:
    if isinstance(x, (NoneType, bool, int, float)): return x
    if not args: return _strip(x)
    return reduce(_strip, args, x)

def poly_lstrip(x: Any, *args) -> Any:
    if isinstance(x, (NoneType, bool, int, float)): return x
    if not args: return _lstrip(x)
    return reduce(_lstrip, args, x)

def poly_rstrip(x: Any, *args) -> Any:
    if isinstance(x, (NoneType, bool, int, float)): return x
    if not args: return _rstrip(x)
    return reduce(_rstrip, args, x)

def poly_removeprefix(x: Any, *args) -> Any:
    if not args or isinstance(x, (NoneType, bool, int, float)): return x
    return reduce(_removeprefix, args, x)

def poly_removesuffix(x: Any, *args) -> Any:
    if not args or isinstance(x, (NoneType, bool, int, float)): return x
    return reduce(_removesuffix, args, x)

def _strip(x: Any, chars: Any=None) -> Any:
    return exec_str_str_op(x, chars, 'Strip', _strip, str.strip)

def _lstrip(x: Any, chars: Any=None) -> Any:
    return exec_str_str_op(x, chars, 'LeftStrip', _lstrip, str.lstrip)

def _rstrip(x: Any, chars: Any=None) -> Any:
    return exec_str_str_op(x, chars, 'RightStrip', _rstrip, str.rstrip)

def _removeprefix(x: Any, prefix: Any) -> Any:
    return x if prefix is None else exec_str_str_op(x, prefix, 'RemovePrefix', _removeprefix, str.removeprefix)

def _removesuffix(x: Any, suffix: Any) -> Any:
    return x if suffix is None else exec_str_str_op(x, suffix, 'RemoveSuffix', _removesuffix, str.removesuffix)

# ["xFoo", None, 27, True].StartsWith("y") -> [False, None, None, None]
# ["xFoo", None, 27, True].StartsWith("x") -> [True, None, None, None]
_bool_string_ops = {
    (str, str)   : lambda _, x, y, sm: sm(x, y),
    (list, str)  : lambda op, x, y, _: [op(x1, y) for x1 in x],
    (tuple, str) : lambda op, x, y, _: tuple(op(x1, y) for x1 in x),
    (dict, str)  : lambda op, x, y, _: {key: op(value, y) for key, value in x.items() if isinstance(value, (str, list, tuple, dict))},
}

def exec_bool_str_op(x: Any, y: Any, name: str, op: Callable[[Any, Any], Any], string_op) -> Any:
    # For these types, the operation is indeterminent
    if isinstance(x, (NoneType, bool, int, float)): return None
    return exec_x_y_op(x, y, name, op, string_op, _bool_string_ops)

####
# str/str that return bools

def poly_startswith(x: Any, prefix: Any) -> Any:
    if prefix is None: return x is None
    return exec_bool_str_op(x, prefix, "StartsWith", poly_startswith, str.startswith)

def poly_endswith(x: Any, suffix: Any) -> bool:
    if suffix is None: return x is None
    return exec_bool_str_op(x, suffix, "EndsWith", poly_endswith, str.endswith)

# "abc".LeftStr(2) -> "ab"
# 2.LeftStr(2).LeftStr(2) -> 2
# ["abc", 2].LeftStr(2) -> ["ab", 2]
_string_int_ops = {
    (str, int)   : lambda _op, x, y,  sm: sm(x, y),
    (list, int)  : lambda  op, x, y, _sm: [op(x1, y) for x1 in x],
    (tuple, int) : lambda  op, x, y, _sm: tuple(op(x1, y) for x1 in x),
    (dict, int)  : lambda  op, x, y, _sm: {key: op(value, y) for key, value in x.items()},
}

def exec_str_int_op(x: Any, y: Any, name: str, op: Callable[[Any, Any], Any], string_op) -> Any:
    # For these types, the operation is idempotent
    if isinstance(x, (NoneType, bool, int, float)): return x
    return exec_x_y_op(x, y, name, op, string_op, _string_int_ops)

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

_string_loc_ops = {
    (str, str)   : lambda _op, x, y,  sm: sm(x, y),
    (list, str)  : lambda  op, x, y, _sm: [op(x1, y) for x1 in x],
    (tuple, str) : lambda  op, x, y, _sm: tuple(op(x1, y) for x1 in x),
    (dict, str)  : lambda  op, x, y, _sm: {key: op(value, y) for key, value in x.items() if isinstance(value, (str, list, tuple, dict))},
}

def poly_count(x: Any, sub: Any=None) -> Any:
    # For these types, the operation is indeterminant
    if isinstance(x, (NoneType, bool, int, float)): return None
    return exec_x_y_op(x, str_arg(sub, 'Sub'), 'Count', poly_count, str.count, _string_loc_ops)

def poly_index(x: Any, sub: Any=None) -> Any:
    # For these types, the operation is indeterminant
    if isinstance(x, (NoneType, bool, int, float)): return None
    sub = str_arg(sub, 'Sub')
    return exec_x_y_op(x, sub, 'Index', poly_index, str.index, _string_loc_ops)

def poly_rindex(x: Any, sub: Any=None) -> Any:
    # For these types, the operation is indeterminant
    if isinstance(x, (NoneType, bool, int, float)): return None
    sub = str_arg(sub, 'Sub')
    return exec_x_y_op(x, sub, 'RIndex', poly_rindex, str.rindex, _string_loc_ops)

def poly_find(x: Any, sub: Any=None) -> Any:
    # For these types, the operation is indeterminant
    if isinstance(x, (NoneType, bool, int, float)): return None
    sub = str_arg(sub, 'Sub')
    return exec_x_y_op(x, sub, 'Find', poly_find, str.find, _string_loc_ops)

def poly_rfind(x: Any, sub: Any=None) -> Any:
    # For these types, the operation is indeterminant
    if isinstance(x, (NoneType, bool, int, float)): return None
    sub = str_arg(sub, 'Sub')
    return exec_x_y_op(x, sub, 'RFind', poly_rfind, str.rfind, _string_loc_ops)

###

def _layout_opt(x: Any, width: int, fillchar: str, op, str_op) -> Any:
    width = 0 if width is None else min(max(0, int_arg(width, "Width")), 256)
    fillchar = ' ' if fillchar is None else str_arg(fillchar, "Fillchar")[0]
    if x is None: return fillchar * width
    if isinstance(x, (list, tuple)): return type(x)(op(x1, width, fillchar) for x1 in x)
    if isinstance(x, (bool, int, float, dict)): x = poly_str(x)
    return str_op(x, width, fillchar)

def poly_center(x: Any, width: int, fillchar: str=' ') -> Any:
    """
**Create a centered string of the given width**

* _value_.Center(_width_)
* _value_.Center(_width_, _pad_)

If the _value_ to be centered is _None_, it is treated as an empty string.
The _width_ argument is interpreted as a numeric value. If _None_, zero is assumed.
The _pad_ argument, if provided, is interpreted as a string value. Only the first character is used.
If not provided, the default is a space.

Also see JustifyLeft() and JustifyRight()
"""
    return _layout_opt(x, width, fillchar, poly_center, str.center)

def poly_ljust(x: Any, width: int, fillchar: str=' ') -> Any:
    """
**Create a string of the given width with contents left aligned**

* _value_.LeftJustify(_width_)
* _value_.LeftJustify(_width_, _pad_)

If the _value_ to be centered is _None_, it is treated as an empty string.
The _width_ argument is interpreted as a numeric value. If _None_, zero is assumed.
The _pad_ argument, if provided, is interpreted as a string value. Only the first character is used.
If not provided, the default is a space.

Also see Center() and JustifyRight()
"""
    return _layout_opt(x, width, fillchar, poly_ljust, str.ljust)

def poly_rjust(x: Any, width: int, fillchar: str=' ') -> Any:
    """
**Create a string of the given width with contents right aligned**

* _value_.RightJustify(_width_)
* _value_.RightJustify(_width_, _pad_)

If the _value_ to be centered is _None_, it is treated as an empty string.
The _width_ argument is interpreted as a numeric value. If _None_, zero is assumed.
The _pad_ argument, if provided, is interpreted as a string value. Only the first character is used.
If not provided, the default is a space.

Also see Center() and JustifyLeft()
"""
    return _layout_opt(x, width, fillchar, poly_rjust, str.rjust)

def poly_zfill(x: Any, width: int) -> Any:
    """
**Create a string of the given width with contents right aligned, padded with zeroes**

* _value_.ZeroFill(_width_)

If the _value_ to be centered is _None_, it is treated as an empty string.
The _width_ argument is interpreted as a numeric value. If _None_, zero is assumed.

Also see JustifyRight()
"""
    return poly_rjust(x, width, '0')

###

def poly_shorten(x: str, length: int, placeholder: str="\u2026") -> str:
    """
**Shorten a string's length, optionally adding a placeholder**

* _value_.ShortenStr(_length_)
* _value_.ShortenStr(_length_, _placeholder_)

If the _value_ is _None_, it is treated as an empty string.
The _length_ argument is interpreted as a numeric value. If _None_, zero is assumed.
The default _placeholder_ is an ellipses, and is added when the string
is truncated. A value of _None_ omits the placeholder.
"""
    length = 0 if length is None else max(0, int_arg(length, "Length"))
    placeholder = '' if placeholder is None else str_arg(placeholder, "Placeholder")
    if x is None: return ''
    if isinstance(x, (list, tuple)): return type(x)(poly_shorten(x1, length, placeholder) for x1 in x)
    if isinstance(x, (bool, int, float, dict)): x = poly_str(x)
    # No adjustment required
    if len(x) <= length: return x
    # No placeholder, so simple truncation
    if not placeholder:  return x[:length]
    pl_len = len(placeholder)
    # If the placeholder overflows the length...
    if pl_len >= length: return placeholder[:length]
    # Truncate to length, adjusting for the addition of the placeholder
    return x[:length - pl_len] + placeholder

###

def poly_append(x: Any, *args) -> Any:
    return reduce(_append, args, x)

def poly_prepend(x: Any, *args) -> Any:
    return reduce(_prepend, args, x)

def poly_replace(x: Any, *args) -> Any:
    """
The operation is skipped if x is None or a non-string scalar.
The operation is skipped in old in None, otherwise it must be a non-empty string, a list, or a tuple.
If old is a list/tuple, it specifies multiple values to be replaced, but always with
the same new value.
Simple stringification is performed on scalars used for old and new.
"""
    if not args: return x
    if isinstance(args[0], re.Pattern): return poly_regex_replace(x, args)
    if len(args) == 1: return _replace(x, args[0]) # old, default new
    if len(args) == 2: return _replace(x, args[0], args[1]) # old and new
    return _replace(x, args[:-1], args[-1]) # old is a list, single new

def _append(x: Any, y: Any) -> Any:
    # For these types, the operation is idempotent
    if isinstance(x, (NoneType, bool, int, float)) or y is None: return x
    if isinstance(x, (list, tuple)): return type(x)(_append(x1, y) for x1 in x)
    if isinstance(x, dict): return  {key: _append(value, y) for key, value in x.items()}
    if isinstance(x, str):
        if isinstance(y, (list, tuple)): return reduce(_append, y, x)
        if isinstance(y, (bool, int, float)): return x + str(y)
        if isinstance(y, str): return x + y
    raise TypeError(f'Concatenation between {type_str(x)} and {type_str(y)} not supported')

def _prepend(x: Any, y: Any) -> Any:
    # For these types, the operation is idempotent
    if isinstance(x, (NoneType, bool, int, float)) or y is None: return x
    if isinstance(x, (list, tuple)): return type(x)(_prepend(x1, y) for x1 in x)
    if isinstance(x, dict): return  {key: _prepend(value, y) for key, value in x.items()}
    if isinstance(x, str):
        if isinstance(y, (list, tuple)): return reduce(_prepend, y, x)
        if isinstance(y, (bool, int, float)): return str(y) + x
        if isinstance(y, str): return y + x
    raise TypeError(f'Concatenation between {type_str(x)} and {type_str(y)} not supported')

def _replace(x: Any, old: Any, new: Any=None) -> Any:
    # For these types, the operation is idempotent
    if isinstance(x, (NoneType, bool, int, float)): return x
    if isinstance(x, re.Pattern): return poly_regex_replace(x, old, new)
    if old is None: return x
    if not isinstance(new, str):
        if new is None:
            new = ''
        else:
            if isinstance(new, (bool, int, float)):
                new = str(new)
            else:
                # at this point, it is just going to raise an error
                str_arg(new, 'New')
    # In this case, old is a list of items to be replaced
    # e.g. poly_replace(my_string, ["a", "e", "i", "o", "u"], "-") to replace all vowels
    if isinstance(old, (list, tuple)): return reduce(lambda x, old1: _replace(x, old1, new), old, x)
    # old needs to be a non-empty, non-None string
    old = str(old) if isinstance(old, (bool, int, float)) else str_arg(old, 'Old')
    if isinstance(x, str): return x.replace(old, new)
    if isinstance(x, (list, tuple)): return type(x)(_replace(x1, old, new) for x1 in x)
    if isinstance(x, dict): return {key: _replace(value, old, new) for key, value in x.items()}
    raise TypeError(f'Replacement of {type_str(x)} not supported')

def poly_split(x: Any, sep:str =None, maxsplit: int=-1) -> Any:
    # For these types, the operation is idempotent
    if isinstance(x, (NoneType, bool, int, float)): return x
    sep = None if sep is None else str_arg(sep, 'Sep')
    maxsplit = -1 if maxsplit is None else max(-1, int_arg(maxsplit, 'Maxsplit'))
    if isinstance(x, str): return x.split(sep, maxsplit)
    if isinstance(x, (list, tuple)): return type(x)(poly_split(x1, sep, maxsplit) for x1 in x)
    if isinstance(x, dict): return {key: poly_split(value, sep, maxsplit) for key, value in x.items()}
    raise TypeError(f'Split of {type_str(x)} not supported')

def poly_rsplit(x: Any, sep:str =None, maxsplit: int=-1) -> Any:
    # For these types, the operation is idempotent
    if isinstance(x, (NoneType, bool, int, float)): return x
    sep = None if sep is None else str_arg(sep, 'Sep')
    maxsplit = -1 if maxsplit is None else max(-1, int_arg(maxsplit, 'Maxsplit'))
    if isinstance(x, str): return x.rsplit(sep, maxsplit)
    if isinstance(x, (list, tuple)): return type(x)(poly_rsplit(x1, sep, maxsplit) for x1 in x)
    if isinstance(x, dict): return {key: poly_rsplit(value, sep, maxsplit) for key, value in x.items()}
    raise TypeError(f'Split of {type_str(x)} not supported')

def poly_splitlines(x: Any, keepends: bool=False) -> Any:
    if isinstance(x, (NoneType, bool, int, float)): return x
    keepends = bool_arg(keepends, "KeepEnds")
    if isinstance(x, str): return x.splitlines(keepends)
    if isinstance(x, (list, tuple)): return type(x)(poly_splitlines(x1, keepends) for x1 in x)
    raise TypeError(f'Splitlines with {type_str(x)} not supported')

def poly_join(x: Any, separator: str=None) -> Any:
    """
**Join together the elements of a list as strings**

* _value_.Join()
* _value_.Join(_seperator_)

The _separator_ argument is the separator between the strings.
It defaults to an empty string.

If _value_is a list, the items in it are converted to strings and concatenated
using _separator_. Items in the list that are _None_ are ignored.

If _value_ is an ordinal, it is converted to a string, and
_separator_ is not used. With a _value_ of _None_ or for an empty list and
empty string is returned.

"""
    if x is None: return ""
    if isinstance(x, (bool, int, float, str)): return poly_str(x)
    separator = '' if separator is None else str_arg(separator, 'Separator', False)
    if isinstance(x, (list, tuple)): return separator.join([poly_str(x1) for x1 in x if x1 is not None])
    raise TypeError(f'Join of {type_str(x)} not supported')

def poly_format(format_string: Any, *args) -> str:
    """
**Format values into a string**

Formatting syntax is that used in [Python's str.format()](https://docs.python.org/3/library/string.html#formatstrings)
    """
    if format_string is None: return None
    format_string = str(format_string)
    return format_string.format(*args)

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

def poly_ord(x:Any) -> Any:
    """
**Convert a string to its ordinal values**

* _value_.Ord()

If _value_ is a single character, the ordinal is returned; for an multi-character
string, an array of ordinals are returned.
The operation is distributed across lists and dictionaries.

Also see Chr()
"""
    if x is None: return None
    if isinstance(x, (int, float)): return int(x) if 0 <= x <= 0x10FFFF else x
    if isinstance(x, str): return ord(x) if len(x) == 1 else [poly_ord(x1) for x1 in x]
    if isinstance(x, (bytes, bytearray)): return list(x)
    if isinstance(x, (list, tuple)): return type(x)(poly_ord(el) for el in x)
    if isinstance(x, dict): return {k: poly_ord(v) for k, v in x.items()}
    return x


def poly_chr(x: Any ) -> Any:
    """
**Convert a number to single character string**

* _value_.Chr()

If _value_ is a value for a Unicode character a single character string
is returned.
The operation is distributed across lists and dictionaries.

Also see Ord().
"""
    if x is None: return None
    if isinstance(x, (int, float)): return chr(int(x)) if 0 <= x <= 0x10FFFF else x
    if isinstance(x, (bytes, bytearray)): return ''.join(chr(b) for b in x)
    if isinstance(x, (list, tuple)): return type(x)(poly_chr(x1) for x1 in x)
    if isinstance(x, dict): return {k: poly_chr(v) for k, v in x.items()}
    return x

####

def _maketrans(from_str: str, to_str: str=''):
    return str.maketrans({from_str[i]: to_str[i] if i < len(to_str) else None for i in range(len(from_str))})
