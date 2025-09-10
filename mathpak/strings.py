"""
Various string manipulation functions using either the string class or regular expressions
"""

from functools import reduce
from typing import Any, Callable
import re

from .common import (
    bool_arg,
    int_arg,
    NoneType,
    str_arg,
    type_str,
    X_None_Op,
    Y_Coll_Op,
)
from .reg_ex import poly_regex_replace
from .types import poly_str

def _exec_x_op(x: Any, name: str, op: Callable[[Any], Any], string_op, op_table) -> Any:
    """General purpose string operation execution for no-args methods on str"""
    operation = op_table.get(type(x))
    if operation is None: raise ValueError(f'{name}() on {type_str(x)} not possible')
    return operation(op, x, string_op)

####

# For no-args string methods that return a string, e.q. "x.Upper()"
# These are transformational on string items, but idempotent on others
_str_operations = {
    NoneType: lambda _op, _x, _sm: None,
    bool:  lambda _op,  x, _sm: x,
    int:   lambda _op,  x, _sm: x,
    float: lambda _op,  x, _sm: x,
    str:   lambda _op,  x,  sm: sm(x),
    list:  lambda  op,  x, _sm: [op(x1) for x1 in x ],
    tuple: lambda  op,  x, _sm: tuple(op(x1) for x1 in x),
    dict:  lambda  op,  x, _sm: {key: op(value) for key, value in x.items()}
}

def _exec_str_op(x: Any, name: str, op: Callable[[Any], Any], string_op) -> Any:
    return _exec_x_op(x, name, op, string_op, _str_operations)

def poly_strlen(x: Any) -> Any:
    """
**Return the length of a string**

* _value_.StrLen()

If _value_ is of any type except string, _None_ is returned.

`"foo".StrLen()` → `3`

`7.StrLen()` → `None`

`["cat", "kitten"].StrLen()` -> `[3, 6]`

Also see *Len()*
"""
    return _exec_str_op(x, 'StrLen', poly_strlen, str.__len__) if isinstance(x, (str, list, tuple, dict)) else None

def poly_strrev(x: Any) -> Any:
    """
**TODO**
"""
    return _exec_str_op(x, 'StringRev', poly_strrev, lambda s: s[::-1])

def poly_capitalize(x: Any) -> Any:
    """
**TODO**
"""
    return _exec_str_op(x, 'Capitalize', poly_capitalize, str.capitalize)

def poly_casefold(x: Any) -> Any:
    """
**TODO**
"""
    return _exec_str_op(x, 'Casefold', poly_casefold, str.casefold)

def poly_lower(x: Any) -> Any:
    """
**TODO**
"""
    return _exec_str_op(x, 'Lower', poly_lower, str.lower)

def poly_swapcase(x: Any) -> Any:
    """
**TODO**
"""
    return _exec_str_op(x, 'SwapCase', poly_swapcase, str.swapcase)

def poly_title(x: Any) -> Any:
    """
**TODO**
"""
    return _exec_str_op(x, 'Title', poly_title, str.title)

def poly_upper(x: Any) -> Any:
    """
**TODO**
"""
    return _exec_str_op(x, 'Upper', poly_upper, str.upper)

####

# For no-args string method that returns a bool, e.g. "x.IsUpper()"
_bool_operations = {
    NoneType: lambda _op, _x, _sm: False,
    bool:  lambda _op, _x, _sm: False,
    int:   lambda _op, _x, _sm: False,
    float: lambda _op, _x, _sm: False,
    str:   lambda _op,  x,  sm: sm(x),
    list:  lambda  op,  x, _sm: [op(x1) for x1 in x],
    tuple: lambda  op,  x, _sm: tuple(op(x1) for x1 in x),
    dict:  lambda  op,  x, _sm: {key: op(value) for key, value in x.items() if isinstance(value, (str, list, tuple, dict))}
}

def _exec_bool_op(x: Any, name: str, op: Callable[[Any], Any], string_op) -> Any:
    return _exec_x_op(x, name, op, string_op, _bool_operations)

def poly_isalnum(x: Any) -> Any:
    """
**Returns _True_ if the value is an alpha-numeric string**

* _value_.IsAlphaNumeric()

A string is alpha-numeric if all characters in the string are
alpha-numeric and there is at least one character in the string.
This is equivalent to *IsAlpha()* or-ed with *IsDigit()* on a
character-by-character basis.

`"FooBar".IsAlphaNumeric()` → `True`

`"Foo123".IsAlphaNumeric()` → `True`

`"Foo 123".IsAlphaNumeric()` → `False`

Also see *IsAlpha()* and *IsNumeric()*
"""
    return _exec_bool_op(x, 'IsAlphaNnumeric', poly_isalnum, str.isalnum)

def poly_isalpha(x: Any) -> Any:
    """
**Returns _True_ if value is an alphabetic string**

* _value_.IsAlpha()

A string is alphabetic if all characters in the string
are alphabetic and there is at least one character in the string.

`"FooBar".IsAlpha()` → `True`

`"Foo Bar".IsAlpha()` → `False`

`["Hello", "Gruezi", "Olá"].IsAlpha()` → `[True, True, True]`
"""
    return _exec_bool_op(x, 'IsAlpha', poly_isalpha, str.isalpha)

def poly_isascii(x: Any) -> Any:
    """
**Returns _True_ if value is a string composed of all ASCII character**

* _value_.IsAscii()

ASCII characters are those in the range U+0000 to U+007F.
Additionally, an empty string considers ASCII.

`"Foo\nBar".IsAscii()` → `True`

`"".IsAscii()` → `True`

`None.IsAscii()` → `False`

`["Hello", "Gruezi", "Olá"].IsAscii()` → `[True, True, False]`

Also see *IsPrintable()*
"""
    return _exec_bool_op(x, 'IsAscii', poly_isascii, str.isascii)

def poly_isdecimal(x: Any) -> Any:
    """
**Returns _True_ if the value is a decimal string**

* _value_.IsDecimal()

A string is a decimal string if all characters in the string
are decimal and there is at least one character in the string.
Decimal characters are the digits 0–9 or Unicode characters
from the _Nd_ (Decimal Number) category.

This is the most restrictive of the number related tests.

`"123".IsDecimal()` → `True`

`"1 2 3".IsDecimal()` → `False`

`["", None].IsDecimal()` → `[False, False]`

Also see *IsDigit()* and *IsNumeric()*
"""
    return _exec_bool_op(x, 'IsDecimal', poly_isdecimal, str.isdecimal)

def poly_isdigit(x: Any) -> Any:
    """
**Returns _True_ if the value is a digit string**

* _value_.IsDigit()

A string is a digit string if all characters in the string
are digits and there is at least one character in the string.
Digit characters include non-ASCII digits, but not special
characters such as circled numbers.

`"123".IsDigit()` → `True`

`"1 2 3".IsDigit()` → `False`

`["", None].IsDigit()` → `[False, False]`

Also see *IsDecimal()* and *IsNumeric()*

"""
    return _exec_bool_op(x, 'IsDigit', poly_isdigit, str.isdigit)

def poly_islower(x: Any) -> Any:
    """
**Returns _True_ if the value is a lowercase string**

* _value_.IsLower()

A string is lowercase if all cased characters in the string
are lowercase and there is at least one cased character in the string.

`"foo-bar".IsLower()` → `True`

`"Foo-Bar".IsLower()` → `False`

`["3.1415", ""].IsLower()` → `[False, False]`
"""
    "".islower()
    return _exec_bool_op(x, 'IsLower', poly_islower, str.islower)

def poly_isnumeric(x: Any) -> Any:
    """
**Returns _True_ if the value is a numeric string**

* _value_.IsNumeric()

A string is numeric if all characters in the string are
numeric and there is at least one character in the string.
Numeric characters include special characters such as
Roman numerals and super/subscripted numbers.

This is the most permissive of the number related tests.

`"17".IsNumeric()` → `True`

`"17.2".IsNumeric()` → `False`

`["", None].IsNumeric()` → `[False, False]`

Also see *IsDecimal()* and *IsDigit()*
"""
    return _exec_bool_op(x, 'IsNumeric', poly_isnumeric, str.isnumeric)

def poly_isprintable(x: Any) -> Any:
    """
**Returns _True_ if the value is a string and is printable**

* _value_.IsPrintable()

A string is printable if all of its characters are considered printable
–generally characters which are not control characters or undefined–
or if it is empty.

`"foo bar".IsPrintable()` → `True`

`"foo\nbar".IsPrintable()` → `False`
"""
    "".isprintable()
    return _exec_bool_op(x, 'IsPrintable', poly_isprintable, str.isprintable)

def poly_isspace(x: Any) -> Any:
    """
**Returns _True_ if the value is a whitespace string**

* _value_.IsSpace()

A string is whitespace if all characters in the string are whitespace
and there is at least one character in the string.

`"".IsSpace()` → `False`

`"Foo".IsSpace()` → `False`

`["\\t\\n ", None].IsSpace()` → `[True, False]`
"""
    return _exec_bool_op(x, 'IsSpace', poly_isspace, str.isspace)

def poly_istitle(x: Any) -> Any:
    """
**Returns _True_ if the value is a title-case string**

* _value_.IsTitle()

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

`"Foo".IsTitle()` → `True`

`"foo".IsTitle()` → `False`

`["aA","Bb"].IsTitle()` → `[False, True]`
"""
    return _exec_bool_op(x, 'IsTitle', poly_istitle, str.istitle)

def poly_isupper(x: Any) -> Any:
    """
**Returns _True_ if the value is an uppercase string**

* _value_.IsUpper()

A string is uppercase if all cased characters in the string are uppercase
and there is at least one cased character in the string.

`"foo".IsUpper()` → `False`

`"FOO".IsUpper()` → `True`

`["FOO-BAR", "Foo Bar"].IsUpper()` → `[True, False]`
"""
    return _exec_bool_op(x, 'IsUpper', poly_isupper, str.isupper)

####

# For two arg functions : e.g. x.Strip(y)/(None)
# [" xFoo ", None, 27, True].strip() -> ["xFoo", None, 27, True]
# ["xFoo", None, 27, True].strip("x") -> ["Foo", None, 27, True]
# [" xFoo ", None, 27, True].strip([None, "x"]) -> ["Foo", None, 27, True]
_str_str_operations = {
    X_None_Op    : lambda _op, _x, _y, _sm: None,
    Y_Coll_Op    : lambda  op,  x,  y, _sm: reduce(op, y, x),
    (str, str)   : lambda _op,  x,  y,  sm: sm(x, y),
    (list, str)  : lambda  op,  x,  y, _sm: [op(x1, y) for x1 in x],
    (tuple, str) : lambda  op,  x,  y, _sm: tuple(op(x1, y) for x1 in x),
    (dict, str)  : lambda  op,  x,  y, _sm: {key: op(value, y) for key, value in x.items()},
}

def _exec_x_y_op(x: Any, y: Any, name: str, op: Callable[[Any, Any], Any], string_op, op_table) -> Any:
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

def _exec_str_str_op(x: Any, y: Any, name: str, op: Callable[[Any, Any], Any], string_op) -> Any:
    """For str/str transformational methods that are idempoten on non-string ordinals"""
    if isinstance(x, (NoneType, bool, int, float)): return x
    return _exec_x_y_op(x, y, name, op, string_op, _str_str_operations)

####

def poly_strip(x: Any, *args) -> Any:
    """
**TODO**
"""
    def _strip(x: Any, chars: Any=None) -> Any:
        return _exec_str_str_op(x, chars, 'Strip', _strip, str.strip)
    if isinstance(x, (NoneType, bool, int, float)): return x
    return _strip(x) if not args else reduce(_strip, args, x)

def poly_lstrip(x: Any, *args) -> Any:
    """
**TODO**
"""
    def _lstrip(x: Any, chars: Any=None) -> Any:
        return _exec_str_str_op(x, chars, 'LeftStrip', _lstrip, str.lstrip)
    if isinstance(x, (NoneType, bool, int, float)): return x
    return _lstrip(x) if not args else reduce(_lstrip, args, x)

def poly_rstrip(x: Any, *args) -> Any:
    """
**TODO**
"""
    def _rstrip(x: Any, chars: Any=None) -> Any:
        return _exec_str_str_op(x, chars, 'RightStrip', _rstrip, str.rstrip)
    if isinstance(x, (NoneType, bool, int, float)): return x
    return _rstrip(x) if not args else reduce(_rstrip, args, x)

def poly_removeprefix(x: Any, *args) -> Any:
    """
**TODO**
"""
    def _removeprefix(x: Any, prefix: Any) -> Any:
        return x if prefix is None else _exec_str_str_op(x, prefix, 'RemovePrefix', _removeprefix, str.removeprefix)
    return x if not args or isinstance(x, (NoneType, bool, int, float)) else reduce(_removeprefix, args, x)

def poly_removesuffix(x: Any, *args) -> Any:
    """
**TODO**
"""
    def _removesuffix(x: Any, suffix: Any) -> Any:
        return x if suffix is None else _exec_str_str_op(x, suffix, 'RemoveSuffix', _removesuffix, str.removesuffix)
    return x if not args or isinstance(x, (NoneType, bool, int, float)) else reduce(_removesuffix, args, x)

####

def _exec_bool_str_op(x: Any, y: Any, name: str, op: Callable[[Any, Any], Any], string_op) -> Any:
    """For str/str functions that return a bool"""
    def flatten(arg):
        return (y for a in arg for y in (flatten(a) if isinstance(a, (list, tuple)) else (a,)))
    if isinstance(x, (list, tuple)): return type(x)(op(x1, y) for x1 in x)
    if isinstance(x, dict): return {key: op(value, y) for key, value in x.items() if isinstance(value, str)}
    if isinstance(x, str):
        for y1 in flatten(y):
            if y1 is None: continue
            if not isinstance(y1, str):
                raise ValueError(f'{name}() between {type_str(x)} and {type_str(y1)} not possible')
            if y1 and string_op(x, y1): return True
    return False

def poly_startswith(x: Any, *prefixes: Any) -> Any:
    """
**Returns _True_ if a string value starts with the specified prefix**

* _value_.StartsWith(_prefix_)
* _value_.StartsWith(_prefix_, ...)

The _prefix_ argument must be either a string or a list of strings. Lists and individual strings
may be intermixed.

If _value_ is a list, the operation is distributed over the values in the list.
If _value_ is a dictionary, the operation is distributed over all keys that are strings.
If _value_ is neither a list, dictionary, or string, _False_ is returned.

`"foo".StartsWith("f")` → `True`

`["foo", "bar", "cat", 7].StartsWith("a", ["b", "c"])` → `[False, True, True, False]`

`{"one": "a", "two": "d", "three": 3}.StartsWith("a", "b", "c")` → `{"one": True, "two": False}`

Also see *EndsWith()*
"""
    return _exec_bool_str_op(x, prefixes, "StartsWith", poly_startswith, str.startswith)

def poly_endswith(x: Any, *suffixes: Any) -> bool:
    """
**Returns _True_ if a string value ends with the specified suffix**

* _value_.EndsWith(_suffix_)
* _value_.EndsWith(_suffix_, ...)

The _suffix_ argument must be either a string or a list of strings. Lists and individual strings
may be intermixed.

If _value_ is a list, the operation is distributed over the values in the list.
If _value_ is a dictionary, the operation is distributed over all keys that are strings.
If _value_ is neither a list, dictionary, or string, _False_ is returned.

`"foo".EndsWith("oo")` → `True`

Also see *StartsWith()*
"""
    return _exec_bool_str_op(x, suffixes, "EndsWith", poly_endswith, str.endswith)

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
    return _exec_x_y_op(x, y, name, op, string_op, _string_int_ops)

def poly_expandtabs(x: Any, tabsize: Any=None) -> Any:
    """
**TODO**
"""
    return exec_str_int_op(x, min(max(1, int_arg(tabsize, 'Tabsize')), 16), "ExpandTabs", poly_expandtabs, str.expandtabs)

def poly_leftstr(x: Any, length: Any) -> Any:
    """
**TODO**
"""
    return exec_str_int_op(x, max(0, int_arg(length, 'Length')), "LeftStr", poly_leftstr, lambda x, length: x[:length])

def poly_rightstr(x: Any, length: Any) -> Any:
    """
**TODO**
"""
    return exec_str_int_op(x, max(0, int_arg(length, 'Length')), "RightStr", poly_rightstr, lambda x, length: x[-length:])

####

def poly_substr(x: Any, start: Any, length: Any=1) -> Any:
    """
**TODO**
"""
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
    """
**TODO**
"""
    # For these types, the operation is indeterminant
    if isinstance(x, (NoneType, bool, int, float)): return None
    return _exec_x_y_op(x, str_arg(sub, 'Sub'), 'Count', poly_count, str.count, _string_loc_ops)

def poly_index(x: Any, sub: Any=None) -> Any:
    """
**TODO**
"""
    # For these types, the operation is indeterminant
    if isinstance(x, (NoneType, bool, int, float)): return None
    sub = str_arg(sub, 'Sub')
    return _exec_x_y_op(x, sub, 'Index', poly_index, str.index, _string_loc_ops)

def poly_rindex(x: Any, sub: Any=None) -> Any:
    """
**TODO**
"""
    # For these types, the operation is indeterminant
    if isinstance(x, (NoneType, bool, int, float)): return None
    sub = str_arg(sub, 'Sub')
    return _exec_x_y_op(x, sub, 'RIndex', poly_rindex, str.rindex, _string_loc_ops)

def poly_find(x: Any, sub: Any=None) -> Any:
    """
**TODO**
"""
    # For these types, the operation is indeterminant
    if isinstance(x, (NoneType, bool, int, float)): return None
    sub = str_arg(sub, 'Sub')
    return _exec_x_y_op(x, sub, 'Find', poly_find, str.find, _string_loc_ops)

def poly_rfind(x: Any, sub: Any=None) -> Any:
    """
**TODO**
"""
    # For these types, the operation is indeterminant
    if isinstance(x, (NoneType, bool, int, float)): return None
    sub = str_arg(sub, 'Sub')
    return _exec_x_y_op(x, sub, 'RFind', poly_rfind, str.rfind, _string_loc_ops)

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

Also see *JustifyLeft()* and *JustifyRight()*
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

Also see *Center()* and *JustifyRight()*
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

Also see *Center()* and *JustifyLeft()*
"""
    return _layout_opt(x, width, fillchar, poly_rjust, str.rjust)

def poly_zfill(x: Any, width: int) -> Any:
    """
**Create a string of the given width with contents right aligned, padded with zeroes**

* _value_.ZeroFill(_width_)

If the _value_ to be centered is _None_, it is treated as an empty string.
The _width_ argument is interpreted as a numeric value. If _None_, zero is assumed.

Also see *JustifyRight()*
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
    """
**TODO**
"""
    return reduce(_append, args, x)

def poly_prepend(x: Any, *args) -> Any:
    """
**TODO**
"""
    return reduce(_prepend, args, x)

def poly_replace(x: Any, *args) -> Any:
    """
**TODO**
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
    """
**TODO**
"""
    # For these types, the operation is idempotent
    if isinstance(x, (NoneType, bool, int, float)): return x
    sep = None if sep is None else str_arg(sep, 'Sep')
    maxsplit = -1 if maxsplit is None else max(-1, int_arg(maxsplit, 'Maxsplit'))
    if isinstance(x, str): return x.split(sep, maxsplit)
    if isinstance(x, (list, tuple)): return type(x)(poly_split(x1, sep, maxsplit) for x1 in x)
    if isinstance(x, dict): return {key: poly_split(value, sep, maxsplit) for key, value in x.items()}
    raise TypeError(f'Split of {type_str(x)} not supported')

def poly_rsplit(x: Any, sep:str =None, maxsplit: int=-1) -> Any:
    """
**TODO**
"""
    # For these types, the operation is idempotent
    if isinstance(x, (NoneType, bool, int, float)): return x
    sep = None if sep is None else str_arg(sep, 'Sep')
    maxsplit = -1 if maxsplit is None else max(-1, int_arg(maxsplit, 'Maxsplit'))
    if isinstance(x, str): return x.rsplit(sep, maxsplit)
    if isinstance(x, (list, tuple)): return type(x)(poly_rsplit(x1, sep, maxsplit) for x1 in x)
    if isinstance(x, dict): return {key: poly_rsplit(value, sep, maxsplit) for key, value in x.items()}
    raise TypeError(f'Split of {type_str(x)} not supported')

def poly_splitlines(x: Any, keepends: bool=False) -> Any:
    """
**TODO**
"""
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

If _value_ is a list, the items in it are converted to strings and concatenated
using _separator_. Items in the list that are _None_ are ignored.

If _value_ is an ordinal, it is converted to a string, and
_separator_ is not used. With a _value_ of _None_ or for an empty list an
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
    """
**TODO**
"""
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

Also see *Chr()*
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

Also see *Ord()*
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
