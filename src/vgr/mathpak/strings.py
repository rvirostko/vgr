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

#---------------------------------------------

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

* StrLen(_value_)
* _value_.StrLen()

If _value_ is of any type except string, _None_ is returned.

```vgr
"foo".StrLen() → 3
7.StrLen() → None
["cat", "kitten"].StrLen() → [3, 6]
```

Also see `Length()`
"""
    return _exec_str_op(x, 'StrLen', poly_strlen, str.__len__) if isinstance(x, (str, list, tuple, dict)) else None

def poly_strrev(x: Any) -> Any:
    """
**Returns the characters of the string in reverse order**

* StrRev(_value_)
* _value_.StrRev()

```vgr
None.StrRev() → None
123.StrRev() → 123
"abc".StrRev() → cba
["abc", "xyz"].StrRev() → ["cba", "zyx"]
```
"""
    return _exec_str_op(x, 'StrRev', poly_strrev, lambda s: s[::-1])

def poly_capitalize(x: Any) -> Any:
    """
**Return the capitalized version of a string**

* Capitalize(_value_)
* _value_.Capitalize()

```vgr
None.Capitalize() → None
"abc".Capitalize() → "Abc"
"the title".Capitalize() → "The title"
"the TITLE".Capitalize() → "The title"
["abc", "xyz"].Capitalize() → ["Abc", "Xyz"]
123.Capitalize() → 123
```
"""
    return _exec_str_op(x, 'Capitalize', poly_capitalize, str.capitalize)

def poly_casefold(x: Any) -> Any:
    """
**Return a caseless version of a string**

* Casefold(_value_)
* _value_.Casefold()

```vgr
None.Casefold() → None
"aBc".Casefold() → "abc"
"The Title".Casefold() → "the title"
"the TITLE".Casefold() → "the title"
["Abc", "Xyz"].Casefold() → ["abc", "xyz"]
123.Casefold() → 123
```
"""
    return _exec_str_op(x, 'Casefold', poly_casefold, str.casefold)

def poly_lower(x: Any) -> Any:
    """
**Return a lowercase version of a string**

* Lower(_value_)
* _value_.Lower()

```vgr
None.Lower() → None
"aBc".Lower() → "abc"
"The Title".Lower() → "the title"
"the TITLE".Lower() → "the title"
["Abc", "Xyz"].Lower() → ["abc", "xyz"]
123.Lower() → 123
```
"""
    return _exec_str_op(x, 'Lower', poly_lower, str.lower)

def poly_swapcase(x: Any) -> Any:
    """
**Return a string with upper and lower case characters swapped**

* SwapCase(_value_)
* _value_.SwapCase()

```vgr
None.SwapCase() → None
"aBc".SwapCase() → "AbC"
"The Title".SwapCase() → "tHE tITLE"
"the TITLE".SwapCase() → "THE title"
["Abc", "Xyz"].SwapCase() → ["aBC", "xYZ"]
123.SwapCase() → 123
```
"""
    return _exec_str_op(x, 'SwapCase', poly_swapcase, str.swapcase)

def poly_title(x: Any) -> Any:
    """
**Title-case words in a string**

* TitleCase(_value_)
* _value_.TitleCase()

```vgr
None.TitleCase() → None
"aBc".TitleCase() → "Abc"
"The title".TitleCase() → "The Title"
"the TITLE".TitleCase() → "The Title"
["Abc", "Xyz"].TitleCase() → ["Abc", "Xyz"]
123.TitleCase() → 123
```
"""
    return _exec_str_op(x, 'TitleCase', poly_title, str.title)

def poly_upper(x: Any) -> Any:
    """
**Return an upper case version of a string**

* Upper(_value_)
* _value_.Upper()

```vgr
None.Upper() → None
"aBc".Upper() → "ABC"
"The title".Upper() → "THE TITLE"
"the TITLE".Upper() → "THE TITLE"
["Abc", "Xyz"].Upper() → ["ABC", "XYZ"]
123.Upper() → 123
```
"""
    return _exec_str_op(x, 'Upper', poly_upper, str.upper)

#---------------------------------------------

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

* IsAlphaNumeric(_value_)
* _value_.IsAlphaNumeric()

A string is alpha-numeric if all characters in the string are
alpha-numeric and there is at least one character in the string.
This is equivalent to `IsAlpha()` or-ed with `IsDigit()` on a
character-by-character basis.

```vgr
"FooBar".IsAlphaNumeric() → True
"Foo123".IsAlphaNumeric() → True
"Foo 123".IsAlphaNumeric() → False
```
Also see `IsAlpha()` and `IsNumeric()`
"""
    return _exec_bool_op(x, 'IsAlphaNnumeric', poly_isalnum, str.isalnum)

def poly_isalpha(x: Any) -> Any:
    """
**Returns _True_ if value is an alphabetic string**

* IsAlpha(_value_)
* _value_.IsAlpha()

A string is alphabetic if all characters in the string
are alphabetic and there is at least one character in the string.

```vgr
"FooBar".IsAlpha() → True
"Foo Bar".IsAlpha() → False
["Hello", "Gruezi", "Olá"].IsAlpha() → [True, True, True]
```
"""
    return _exec_bool_op(x, 'IsAlpha', poly_isalpha, str.isalpha)

def poly_isascii(x: Any) -> Any:
    """
**Returns _True_ if value is a string composed of all ASCII character**

* IsAscii(_value_)
* _value_.IsAscii()

ASCII characters are those in the range U+0000 to U+007F.
Additionally, an empty string considers ASCII.

```vgr
"Foo\nBar".IsAscii() → True
"".IsAscii() → True
None.IsAscii() → False
["Hello", "Gruezi", "Olá"].IsAscii() → [True, True, False]
```

Also see `IsPrintable()`
"""
    return _exec_bool_op(x, 'IsAscii', poly_isascii, str.isascii)

def poly_isdecimal(x: Any) -> Any:
    """
**Returns _True_ if the value is a decimal string**

* IsDecimal(_value_)
* _value_.IsDecimal()

A string is a decimal string if all characters in the string
are decimal and there is at least one character in the string.
Decimal characters are the digits 0–9 or Unicode characters
from the _Nd_ (Decimal Number) category.

This is the most restrictive of the number related tests.

```vgr
"123".IsDecimal() → True
"1 2 3".IsDecimal() → False
["", None].IsDecimal() → [False, False]
```

Also see `IsDigit()` and `IsNumeric()`
"""
    return _exec_bool_op(x, 'IsDecimal', poly_isdecimal, str.isdecimal)

def poly_isdigit(x: Any) -> Any:
    """
**Returns _True_ if the value is a digit string**

* IsDigit(_value_)
* _value_.IsDigit()

A string is a digit string if all characters in the string
are digits and there is at least one character in the string.
Digit characters include non-ASCII digits, but not special
characters such as circled numbers.

```vgr
"123".IsDigit() → True
"1 2 3".IsDigit() → False
["", None].IsDigit() → [False, False]
```

Also see `IsDecimal()` and `IsNumeric()`
"""
    return _exec_bool_op(x, 'IsDigit', poly_isdigit, str.isdigit)

def poly_islower(x: Any) -> Any:
    """
**Returns _True_ if the value is a lowercase string**

* IsLower(_value_)
* _value_.IsLower()

A string is lowercase if all cased characters in the string
are lowercase and there is at least one cased character in the string.

```vgr
"foo-bar".IsLower() → True
"Foo-Bar".IsLower() → False
["3.1415", ""].IsLower() → [False, False]
```
"""
    return _exec_bool_op(x, 'IsLower', poly_islower, str.islower)

def poly_isnumeric(x: Any) -> Any:
    """
**Returns _True_ if the value is a numeric string**

* IsNumeric(_value_)
* _value_.IsNumeric()

A string is numeric if all characters in the string are
numeric and there is at least one character in the string.
Numeric characters include special characters such as
Roman numerals and super/subscripted numbers.

This is the most permissive of the number related tests.

```vgr
"17".IsNumeric() → True
"17.2".IsNumeric() → False
["", None].IsNumeric() → [False, False]
```

Also see `IsDecimal()` and `IsDigit()`
"""
    return _exec_bool_op(x, 'IsNumeric', poly_isnumeric, str.isnumeric)

def poly_isprintable(x: Any) -> Any:
    """
**Returns _True_ if the value is a string and is printable**

* IsPrintable(_value_)
* _value_.IsPrintable()

A string is printable if all of its characters are considered printable
–generally characters which are not control characters or undefined–
or if it is empty.

```vgr
"foo bar".IsPrintable() → True
"foo\nbar".IsPrintable() → False
```
"""
    return _exec_bool_op(x, 'IsPrintable', poly_isprintable, str.isprintable)

def poly_isspace(x: Any) -> Any:
    """
**Returns _True_ if the value is a whitespace string**

* IsSpace(_value_)
* _value_.IsSpace()

A string is whitespace if all characters in the string are whitespace
and there is at least one character in the string.

```vgr
"".IsSpace() → False
"Foo".IsSpace() → False
["\\t\\n ", None].IsSpace() → [True, False]
```
"""
    return _exec_bool_op(x, 'IsSpace', poly_isspace, str.isspace)

def poly_istitle(x: Any) -> Any:
    """
**Returns _True_ if the value is a title-case string**

* IsTitle(_value_)
* _value_.IsTitle()

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

```vgr
"Foo".IsTitle() → True
"foo".IsTitle() → False
["aA","Bb"].IsTitle() → [False, True]
```
"""
    return _exec_bool_op(x, 'IsTitle', poly_istitle, str.istitle)

def poly_isupper(x: Any) -> Any:
    """
**Returns _True_ if the value is an uppercase string**

* IsUpper(_value_)
* _value_.IsUpper()

A string is uppercase if all cased characters in the string are uppercase
and there is at least one cased character in the string.

```vgr
"foo".IsUpper() → False
"FOO".IsUpper() → True
["FOO-BAR", "Foo Bar"].IsUpper() → [True, False]
```
"""
    return _exec_bool_op(x, 'IsUpper', poly_isupper, str.isupper)

#---------------------------------------------

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

#---------------------------------------------

def poly_strip(x: Any, *args) -> Any:
    """
**Remove leading and trailing characters from a string**

* Strip(_value_)
* Strip(_value_, _expression_...)
* _value_.Strip()
* _value_.Strip(_expression_...)

Without an argument, whitespace is removed. When arguments are provided
they specify the characters to be removed. Note that the removal is
performed in the order provided.

```vgr
None.Strip() → None
" aBc ".Strip() → "aBc"
"The title".Strip("Tt") → "he title"
"the TITLE".Strip("aeiou", "AEIOU") → "the TITL"
["Abc", "Xyz"].Strip(string.ascii_uppercase) → ["bc", "yz"]
123.Strip() → 123
```

Also see `LeftStrip()` and `RightStrip()`
"""
    def _strip(x: Any, chars: Any=None) -> Any:
        return _exec_str_str_op(x, chars, 'Strip', _strip, str.strip)
    if isinstance(x, (NoneType, bool, int, float)): return x
    return _strip(x) if not args else reduce(_strip, args, x)

def poly_lstrip(x: Any, *args) -> Any:
    """
**Remove leading characters from a string**

* LeftStrip(_value_)
* LeftStrip(_value_, _expression_...)
* _value_.LeftStrip()
* _value_.LeftStrip(_expression_...)

```vgr
None.LeftStrip() → None
" aBc ".LeftStrip() → "aBc "
"The title".LeftStrip("Tt") → "he title"
"the TITLE".LeftStrip("aeiou", "AEIOU") → "the TITLE"
["Abc", "Xyz"].LeftStrip(string.ascii_uppercase) → ["bc", "yz"]
123.LeftStrip() → 123
```

Also see `Strip()` and `RightStrip()`
"""
    def _lstrip(x: Any, chars: Any=None) -> Any:
        return _exec_str_str_op(x, chars, 'LeftStrip', _lstrip, str.lstrip)
    if isinstance(x, (NoneType, bool, int, float)): return x
    return _lstrip(x) if not args else reduce(_lstrip, args, x)

def poly_rstrip(x: Any, *args) -> Any:
    """
**Remove trailing characters from a string**

* RightStrip(_value_)
* RightStrip(_value_, _expression_...)
* _value_.RightStrip()
* _value_.RightStrip(_expression_...)

```vgr
None.RightStrip() → None
" aBc ".RightStrip() → " aBc"
"The title".RightStrip("Tt") → "The title"
"the TITLE".RightStrip("aeiou", "AEIOU") → "the TITL"
["Abc", "Xyz"].RightStrip(string.ascii_uppercase) → ["Abc", "Xyz"]
123.RightStrip() → 123
```

Also see `Strip()` and `LeftStrip()`
"""
    def _rstrip(x: Any, chars: Any=None) -> Any:
        return _exec_str_str_op(x, chars, 'RightStrip', _rstrip, str.rstrip)
    if isinstance(x, (NoneType, bool, int, float)): return x
    return _rstrip(x) if not args else reduce(_rstrip, args, x)

def poly_removeprefix(x: Any, *args) -> Any:
    """
**Remove a prefix from a string if present**

* RemovePrefix(_value_)
* RemovePrefix(_value_, _prefix_...)
* _value_.RemovePrefix()
* _value_.RemovePrefix(_prefix_...)

```vgr
None.RemovePrefix() → None
"http://example.com".RemovePrefix() → "http://example.com"
"http://example.com".RemovePrefix("http://") → "example.com"
"http://example.com".RemovePrefix("http://", "https://") → "example.com"
"http://example.com".RemovePrefix(["http://", "https://"]) → "example.com"
["a/file.txt","b/file.txt"].RemovePrefix("a/", "b/") → ["file.txt", "file.txt"]
1234.RemovePrefix(12) → "34"
```

Also see `RemoveSuffix()`
"""
    def _removeprefix(x: Any, prefix: Any) -> Any:
        if prefix is None: return x
        if isinstance(prefix, (bool, int, float)): prefix = str(prefix)
        return _exec_str_str_op(x, prefix, 'RemovePrefix', _removeprefix, str.removeprefix)
    if x is None: return None
    if not args: return x
    if isinstance(x, (bool, int, float)): x = str(x)
    return reduce(_removeprefix, args, x)

def poly_removesuffix(x: Any, *args) -> Any:
    """
**Remvoe a suffix from a string if present**

* RemoveSuffix(_value_)
* RemoveSuffix(_value_, _prefix_...)
* _value_.RemoveSuffix()
* _value_.RemoveSuffix(_prefix_...)

```vgr
None.RemoveSuffix() → None
"http://example.com".RemoveSuffix() → "http://example.com"
"http://example.com".RemoveSuffix(".com") → "http://example"
"http://example.com".RemoveSuffix(".net", ".com") → "http://example"
"http://example.com".RemoveSuffix([".net", ".com"]) → "http://example"
["file.txt","file.md"].RemoveSuffix(".md", ".txt") → ["file", "file"]
1234.RemoveSuffix(34) → "12"
```

Also see `RemovePrefix()`
"""
    def _removesuffix(x: Any, suffix: Any) -> Any:
        if suffix is None: return x
        if isinstance(suffix, (bool, int, float)): suffix = str(suffix)
        return _exec_str_str_op(x, suffix, 'RemoveSuffix', _removesuffix, str.removesuffix)
    if x is None: return None
    if not args: return x
    if isinstance(x, (bool, int, float)): x = str(x)
    return reduce(_removesuffix, args, x)

#---------------------------------------------

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

* StartsWith(_value_, _prefix_...)
* _value_.StartsWith(_prefix_...)

The _prefix_ argument must be either a string or a list of strings. Lists and individual strings
may be intermixed.

If _value_ is a list, the operation is distributed over the values in the list.
If _value_ is a dictionary, the operation is distributed over all keys that are strings.
If _value_ is neither a list, dictionary, or string, _False_ is returned.

```vgr
"foo".StartsWith("f") → True
["foo", "bar", "cat", 7].StartsWith("a", ["b", "c"]) → [False, True, True, False]
{"one": "a", "two": "d", "three": 3}.StartsWith("a", "b", "c") → {"one": True, "two": False}
```

Also see `EndsWith()`
"""
    return _exec_bool_str_op(x, prefixes, "StartsWith", poly_startswith, str.startswith)

def poly_endswith(x: Any, *suffixes: Any) -> bool:
    """
**Returns _True_ if a string value ends with the specified suffix**

* EndsWith(_value_, _suffix_...)
* _value_.EndsWith(_suffix_...)

The _suffix_ argument must be either a string or a list of strings. Lists and individual strings
may be intermixed.

If _value_ is a list, the operation is distributed over the values in the list.
If _value_ is a dictionary, the operation is distributed over all keys that are strings.
If _value_ is neither a list, dictionary, or string, _False_ is returned.

```vgr
"foo".EndsWith("oo") → True
"foo".EndsWith("a", "e", "i", "o", "u") → True
["foo", "bar"].EndsWith("o") → [True, False]
"foo".EndsWith(["a", "e"], ["i", "o", "u"]) → True
```

Also see `StartsWith()`
"""
    return _exec_bool_str_op(x, suffixes, "EndsWith", poly_endswith, str.endswith)

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

def poly_expandtabs(x: Any, tabsize: Any=8) -> Any:
    """
**Converts tabs in a string into spaces**

* ExpandTabs(_value_)
* ExpandTabs(_value_, _tabsize_)
* _value_.ExpandTabs()
* _value_.ExpandTabs(_tabsize_)

Tabsize defaults to 8 and is limited from 0 to 64.

```vgr
None.ExpandTabs() → None
"\\taBc\\t".ExpandTabs() → "        aBc     "
"\\taBc\\t".ExpandTabs(2) → "  aBc "
["A\\tbc", "X\\tyz"].ExpandTabs(0) → ["Abc", "Xyz"]
123.ExpandTabs() → 123
```
"""
    return exec_str_int_op(x, min(max(0, int_arg(tabsize, 'Tabsize')), 64), "ExpandTabs", poly_expandtabs, str.expandtabs)

def poly_leftstr(x: Any, length: Any=1) -> Any:
    """
**Returns the leftmost characters of a string**

* LeftStr(_value_)
* LeftStr(_value_, _length_)
* _value_.LeftStr()
* _value_.LeftStr(_length_)

Without a _length_ argument a single character is returned.

```vgr
None.LeftStr() → None
"aBc".LeftStr() → "a"
"aBc".LeftStr(2) → "aB"
"The title".LeftStr(3) → "The"
["Abc", "Xyz"].LeftStr(2) → ["Ab", "Xy"]
123.LeftStr(2) → 123
```

Also see `RightStr()` and `SubStr()`
"""
    return exec_str_int_op(x, max(1, int_arg(length, 'Length')), "LeftStr", poly_leftstr, lambda x, length: x[:length])

def poly_rightstr(x: Any, length: Any=1) -> Any:
    """
**Retunrs the rightmost characters of a string**

* RightStr(_value_)
* RightStr(_value_, _length_)
* _value_.RightStr()
* _value_.RightStr(_length_)

Without a _length_ argument a single character is returned.

```vgr
None.RightStr() → None
"aBc".RightStr() → "c"
"aBc".RightStr(2) → "Bc"
"The title".RightStr(5) → "title"
["Abc", "Xyz"].RightStr(2) → ["bc", "yz"]
123.RightStr(2) → 123
```

Also see `LeftStr()` and `SubStr()`
"""
    return exec_str_int_op(x, max(0, int_arg(length, 'Length')), "RightStr", poly_rightstr, lambda x, length: x[-length:])

#---------------------------------------------

def poly_substr(x: Any, start: Any=0, length: Any=1) -> Any:
    """
**Return a portion of a string**

* SubStr(_value_)
* SubStr(_value_, _start_)
* SubStr(_value_, _start_, _length_)
* _value_.SubStr()
* _value_.SubStr(_start_)
* _value_.SubStr(_start_, _length_)

If not provided, _start_ defaults to zero and _length_ to one.
The _start_ index is zero based.

```vgr
None.SubStr() → None
"aBc".SubStr() → "a"
"aBc".SubStr(1, 2) → "Bc"
"The title".SubStr(4, 5) → "title"
["Abc", "Xyz"].SubStr(1) → ["b", "y"]
123.SubStr(2, 1) → 123
```

Also see `LeftStr()` and `RightStr()`
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
**Return the count of non-overlapping occurrences of one string in another**

* CountOf(_value_, _substr_)
* _value_.CountOf(_substr_)

```vgr
None.CountOf("a") → None
"aaaBc".CountOf("") → 6
"aaaBc".CountOf("a") → 3
"aaaBc".CountOf("aa") → 1
["A.b.c", "X.y.z"].CountOf(".") → [2, 2]
123.CountOf("1") → 123
```
"""
    if isinstance(x, (NoneType, bool, int, float)): return x
    return _exec_x_y_op(x, str_arg(sub, 'Substr', False) or '', 'CountOf', poly_count, str.count, _string_loc_ops)

def poly_index(x: Any, sub: Any=None) -> Any:
    """
**Returns the _lowest_ index of one string in another**

* IndexOf(_value_, _substr_)
* _value_.IndexOf(_substr_)

The returned index is zero based.

If _substr_ cannot be found, an error is raised: use `FindStr()`
as an alternative that returns -1 on an error.

```vgr
None.IndexOf("a") → None
"aaaBc".IndexOf("") → 0
"aaaBc".IndexOf("z") → Substring not found
"aaaBc".IndexOf("aB") → 2
["Abc.", ".Xyz"].IndexOf(".") → [3, 0]
123.IndexOf("1") → 123
```

Also see `RIndexOf()` and `FindStr()`
"""
    if isinstance(x, (NoneType, bool, int, float)): return x
    return _exec_x_y_op(x, str_arg(sub, 'Substr', False) or '', 'IndexOf', poly_index, str.index, _string_loc_ops)

def poly_rindex(x: Any, sub: Any=None) -> Any:
    """
**Returns the _highest_ index of one string in another**

* RIndexOf(_value_, _substr_)
* _value_.RIndexOf(_substr_)

The returned index is zero based.

If _substr_ cannot be found, an error is raised: use `RFindStr()`
as an alternative that returns -1 on an error.

```vgr
None.RIndexOf("a") → None
"aaaBc".RIndexOf("") → 5
"aaaBc".RIndexOf("z") → Substring not found
"aaaBc".RIndexOf("a") → 2
["A.b.c", "X.y.z"].RIndexOf(".") → [3, 3]
123.RIndexOf("1") → 123
```

Also see `IndexOf()` and `RFindStr()`
"""
    if isinstance(x, (NoneType, bool, int, float)): return x
    return _exec_x_y_op(x, str_arg(sub, 'Substr', False) or '', 'RIndexOf', poly_rindex, str.rindex, _string_loc_ops)

def poly_find(x: Any, sub: Any=None) -> Any:
    """
**Returns the _lowest_ index of one string in another**

* FindStr(_value_, _substr_)
* _value_.FindStr(_substr_)

The returned index is zero based.

If _substr_ cannot be found, -1 is returned.

```vgr
None.FindStr("a") → None
"aaaBc".FindStr("") → 0
"aaaBc".FindStr("z") → -1
"aaaBc".FindStr("a") → 0
["A.b.c", "X.y.z"].FindStr(".") → [1, 1]
123.FindStr("1") → 123
```

Also see `RFindStr()` and `IndexOf()`
"""
    if isinstance(x, (NoneType, bool, int, float)): return x
    return _exec_x_y_op(x, str_arg(sub, 'Substr', False) or '', 'FindStr', poly_find, str.find, _string_loc_ops)

def poly_rfind(x: Any, sub: Any=None) -> Any:
    """
**Returns the _highest_ index of one string in another**

* RFindStr(_value_, _substr_)
* _value_.RFindStr(_substr_)

The returned index is zero based.

If _substr_ cannot be found, -1 is returned.

```vgr
None.RFindStr("a") → None
"aaaBc".RFindStr("") → 5
"aaaBc".RFindStr("z") → -1
"aaaBc".RFindStr("a") → 2
["A.b.c", "X.y.z"].RFindStr(".") → [3, 3]
123.RFindStr("1") → 123
```
Also see `FindStr()` and `RIndexOf()`
"""
    if isinstance(x, (NoneType, bool, int, float)): return x
    return _exec_x_y_op(x, str_arg(sub, 'Substr', False) or '', 'RFindStr', poly_rfind, str.rfind, _string_loc_ops)

#---------------------------------------------

def _layout_opt(x: Any, width: int, fillchar: str, op, str_op) -> Any:
    width = 0 if width is None else min(max(0, int_arg(width, "Width")), 256)
    fillchar = ' ' if fillchar is None else str_arg(fillchar, "Fillchar")[0]
    if x is None: return fillchar * width
    if isinstance(x, (list, tuple)): return type(x)(op(x1, width, fillchar) for x1 in x)
    if isinstance(x, (bool, int, float, dict)): x = poly_str(x)
    return str_op(x, width, fillchar)

def poly_center(x: Any, width: int=0, fillchar: str=' ') -> Any:
    """
**Create a centered string of the given width**

* Center(_value_, _width_)
* Center(_value_, _width_, _pad_)
* _value_.Center(_width_)
* _value_.Center(_width_, _pad_)

If the _value_ to be centered is _None_, it is treated as an empty string.
The _width_ argument is interpreted as a numeric value. If _None_, zero is assumed.
The _pad_ argument, if provided, is interpreted as a string value. Only the first character is used.
If not provided, the default is a space.

```vgr
None.Center(3) → "   "
"aaaBc".Center(3) → "aaaBc"
"aaaBc".Center(7) → " aaaBc "
"aaaBc".Center(8) → " aaaBc  "
"aaaBc".Center(7, "-") → "-aaaBc-"
"aaaBc".Center(9, "-=") → "--aaaBc--"
["A.b.c", "X.y.z"].Center(7, ".") → [".A.b.c.", ".X.y.z."]
123.Center(5, "0") → "01230"
```

Also see `LeftJustify()` and `RightJustify()`
"""
    return _layout_opt(x, width, fillchar, poly_center, str.center)

def poly_ljust(x: Any, width: int=0, fillchar: str=' ') -> Any:
    """
**Create a string of the given width with contents left aligned**

* LeftJustify(_value_, _width_)
* LeftJustify(_value_, _width_, _pad_)
* _value_.LeftJustify(_width_)
* _value_.LeftJustify(_width_, _pad_)

If the _value_ to be centered is _None_, it is treated as an empty string.
The _width_ argument is interpreted as a numeric value. If _None_, zero is assumed.
The _pad_ argument, if provided, is interpreted as a string value. Only the first character is used.
If not provided, the default is a space.

```vgr
None.LeftJustify(3) → "   "
"aaaBc".LeftJustify(3) → "aaaBc"
"aaaBc".LeftJustify(7) → "aaaBc  "
"aaaBc".LeftJustify(8) → "aaaBc   "
"aaaBc".LeftJustify(7, "-") → "aaaBc--"
"aaaBc".LeftJustify(9, "-=") → "aaaBc----"
["A.b.c", "X.y.z"].LeftJustify(7, ".") → ["A.b.c..", "X.y.z.."]
123.LeftJustify(5, "0") → "12300"
```

Also see `Center()` and `RightJustify()`
"""
    return _layout_opt(x, width, fillchar, poly_ljust, str.ljust)

def poly_rjust(x: Any, width: int=0, fillchar: str=' ') -> Any:
    """
**Create a string of the given width with contents right aligned**

* RightJustify(_value_, _width_)
* RightJustify(_value_, _width_, _pad_)
* _value_.RightJustify(_width_)
* _value_.RightJustify(_width_, _pad_)

If the _value_ to be centered is _None_, it is treated as an empty string.
The _width_ argument is interpreted as a numeric value. If _None_, zero is assumed.
The _pad_ argument, if provided, is interpreted as a string value. Only the first character is used.
If not provided, the default is a space.

```vgr
None.RightJustify(3) → "   "
"aaaBc".RightJustify(3) → "aaaBc"
"aaaBc".RightJustify(7) → "  aaaBc"
"aaaBc".RightJustify(8) → "   aaaBc"
"aaaBc".RightJustify(7, "-") → "--aaaBc"
"aaaBc".RightJustify(9, "-=") → "----aaaBc"
["A.b.c", "X.y.z"].RightJustify(7, ".") → ["..A.b.c", "..X.y.z"]
123.RightJustify(5, "0") → "00123"
```

Also see `Center()` and `LeftJustify()`
"""
    return _layout_opt(x, width, fillchar, poly_rjust, str.rjust)

def poly_zfill(x: Any, width: int=0) -> Any:
    """
**Create a string of the given width with contents right aligned, padded with zeroes**

* ZeroFill(_value_, _width_)
* _value_.ZeroFill(_width_)

If the _value_ to be centered is _None_, it is treated as an empty string.
The _width_ argument is interpreted as a numeric value. If _None_, zero is assumed.

```vgr
None.ZeroFill(3) → "000"
"aaaBc".ZeroFill(3) → "aaaBc"
"aaaBc".ZeroFill(7) → "00aaaBc"
"aaaBc".ZeroFill(8) → "000aaaBc"
["A.b.c", "X.y.z"].ZeroFill(7) → ["00A.b.c", "00X.y.z"]
123.ZeroFill(5) → "00123"
```

Also see `RightJustify()`
"""
    return poly_rjust(x, width, '0')

#---------------------------------------------

def poly_shorten(x: str, length: int=32, placeholder: str="\u2026") -> str:
    """
**Shorten a string's length, optionally adding a placeholder**

* ShortenStr(_value_, _length_)
* ShortenStr(_value_, _length_, _placeholder_)
* _value_.ShortenStr(_length_)
* _value_.ShortenStr(_length_, _placeholder_)

If the _value_ is _None_, it is treated as an empty string.
The _length_ argument is interpreted as a numeric value. If _None_, 32 is assumed.
The default _placeholder_ is an ellipses, and is added when the string
is truncated. A value of _None_ omits the placeholder.

```vgr
None.ShortenStr(3) → ""
string.digits.ShortenStr(3) → "01…"
string.digits.ShortenStr(7) → "012345…"
string.digits.ShortenStr(7, " etc") → "012 etc"
[string.octdigits, string.hexdigits].ShortenStr(7) → ["012345…", "012345…"]
123.ShortenStr(5) → "123"
```
"""
    length = 32 if length is None else max(0, int_arg(length, "Length"))
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

#---------------------------------------------

def poly_append(x: Any, *args) -> Any:
    """
**Concatenate strings**

* AppendStr(_value_)
* AppendStr(_value_, _arg_...)
* _value_.AppendStr()
* _value_.AppendStr(_arg_...)

The argument values are concatenated to end of _value_.

```vgr
None.AppendStr() → None
None.AppendStr("") → ""
"left".AppendStr(":right") → "left:right"
"left".AppendStr(":", "right") → "left:right"
"L".AppendStr(["-", "R"], " end") → "L-R end"
["L", "R"].AppendStr("-end") → ["L-end", "R-end"]
123.AppendStr("5") → "1235"
```

Also see `PrependStr()`
"""
    return reduce(_append, args, x)

def poly_prepend(x: Any, *args) -> Any:
    """
**Concatenate string placing values at the beginning of the string**

* PrependStr(_value_)
* PrependStr(_value_, _arg_...)
* _value_.PrependStr()
* _value_.PrependStr(_arg_...)

The argument values are concatenated to end of _value_.

```vgr
None.PrependStr() → None
None.PrependStr("") → ""
"right".PrependStr("left:") → "left:right"
"right".PrependStr(":", "left") → "left:right"
"R".PrependStr(["L", "-"], "start") → "start-LR"
["L", "R"].PrependStr("start-") → ["start-L", "start-R"]
123.PrependStr("5") → "5123"
```

Also see `AppendStr()`
"""
    return reduce(_prepend, args, x)

def poly_replace(x: Any, *args) -> Any:
    """
**Replace or delete values in a string**

* ReplaceStr(_value_)
* ReplaceStr(_value_, _old_)
* ReplaceStr(_value_, _old_, _new_)
* ReplaceStr(_value_, _old_..., _new_)
* _value_.ReplaceStr()
* _value_.ReplaceStr(_old_)
* _value_.ReplaceStr(_old_, _new_)
* _value_.ReplaceStr(_old_..., _new_)

String conversion is performed on _value_, _old_, and _new_ as
required. The value for _old_ may be a compiled regular expression.

```vgr
None.ReplaceStr() → None
None.ReplaceStr("") → ""
"Hello".ReplaceStr("") → "Hello"
"Hello".ReplaceStr("e", "o") → "Hollo"
"Hello".ReplaceStr("e", "o", "*") → "H*ll*"
"Hello".ReplaceStr(["e", "o"], "-*-") → "H-*-ll-*-"
["Hello", "Goodbye"].ReplaceStr("e", "o", "*") → ["H*ll*", "G**dby*"]
"Goodbye".ReplaceStr("[aeiou]+".CompilePattern(), "*") → "G*dby*"
print 1234.ReplaceStr(2, 4, 0) → "1030"
```

Also see `RegexReplace()` and `CompilePattern()`
"""
    if not args: return x
    if len(args) == 1: return _replace(x, args[0]) # old, default new
    if len(args) == 2: return _replace(x, args[0], args[1]) # old and new
    return _replace(x, args[:-1], args[-1]) # old is a list, single new

def _append(x: Any, y: Any) -> Any:
    if y is None: return x
    if isinstance(x, (list, tuple)): return type(x)(_append(x1, y) for x1 in x)
    if isinstance(x, dict): return  {key: _append(value, y) for key, value in x.items()}
    if x is None: x = ''
    if isinstance(x, (bool, int, float)): x = str(x)
    if isinstance(x, str):
        if isinstance(y, (list, tuple)): return reduce(_append, y, x)
        if isinstance(y, (bool, int, float)): return x + str(y)
        if isinstance(y, str): return x + y
    raise TypeError(f'Concatenation between {type_str(x)} and {type_str(y)} not supported')

def _prepend(x: Any, y: Any) -> Any:
    if y is None: return x
    if isinstance(x, (list, tuple)): return type(x)(_prepend(x1, y) for x1 in x)
    if isinstance(x, dict): return  {key: _prepend(value, y) for key, value in x.items()}
    if x is None: x = ''
    if isinstance(x, (bool, int, float)): x = str(x)
    if isinstance(x, str):
        if isinstance(y, (list, tuple)): return reduce(_prepend, y, x)
        if isinstance(y, (bool, int, float)): return str(y) + x
        if isinstance(y, str): return y + x
    raise TypeError(f'Concatenation between {type_str(x)} and {type_str(y)} not supported')

def _replace(x: Any, old: Any, new: Any=None) -> Any:
    if isinstance(old, re.Pattern): return poly_regex_replace(x, old, new)
    if old is None: return x
    if x is None: x = ''
    if isinstance(x, (bool, int, float)): x = str(x)

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
    # e.g. poly_replace(my_string, ["a", "e", "i", "o", "u"], "-")
    if isinstance(old, (list, tuple)): return reduce(lambda x, old1: _replace(x, old1, new), old, x)
    old = str(old) if isinstance(old, (bool, int, float)) else str_arg(old, 'Old', False) or ''
    if isinstance(x, str): return x.replace(old, new)
    if isinstance(x, (list, tuple)): return type(x)(_replace(x1, old, new) for x1 in x)
    if isinstance(x, dict): return {key: _replace(value, old, new) for key, value in x.items()}
    raise TypeError(f'Replacement of {type_str(x)} not supported')

def poly_split(x: Any, sep: str=None, maxsplit: int=-1) -> Any:
    """
**Split a string based on a separator string**

* Split(_value_)
* Split(_value_, _sep_)
* Split(_value_, _sep_, _maxsplit_)
* _value_.Split()
* _value_.Split(_sep_)
* _value_.Split(_sep_, _maxsplit_)

If _sep_ is not specified, or is _None_ or a blank string, the
split is performed on any whitespace character, and empty entries
are omitted.

The _maxsplit_ argument is the maximum number of times a split will
occur. If less than zero then there is no limit.

```vgr
None.Split() → []
"a  b \\t c".Split() → ["a", "b", "c"]
"a".Split(",") → ["a"]
",".Split(",") → ["", ""]
"a,b".Split(",") → ["a", "b"]
"a,b,c".Split(",", 1) → ["a", "b,c"]
["Hello", "Goodbye"].Split("oo") → [["Hello"], ["G", "dbye"]]
1234.Split(2) → ["1", "34"]
```

Also see `RSplit()`
"""
    return _split('Split', poly_split, str.split, x, sep, maxsplit)

def poly_rsplit(x: Any, sep: str=None, maxsplit: int=-1) -> Any:
    """
**Split a string based on a separator string**

* RSplit(_value_)
* RSplit(_value_, _sep_)
* RSplit(_value_, _sep_, _maxsplit_)
* _value_.RSplit()
* _value_.RSplit(_sep_)
* _value_.RSplit(_sep_, _maxsplit_)

`RSplit()` is identical to `Split()` except that the splitting of
_value_ starts from the end of the string.

```vgr
None.RSplit() → []
"a  b \\t c".RSplit() → ["a", "b", "c"]
"a".RSplit(",") → ["a"]
",".RSplit(",") → ["", ""]
"a,b".RSplit(",") → ["a", "b"]
"a,b,c".RSplit(",", 1) → ["a,b", "c"] // different from Split()
["Hello", "Goodbye"].RSplit("oo") → [["Hello"], ["G", "dbye"]]
1234.RSplit(2) → ["1", "34"]
```

Also see `Split()`
"""
    return _split('RSplit', poly_rsplit, str.rsplit, x, sep, maxsplit)

def _split(name: str, p_op, str_op, x: Any, sep: str=None, maxsplit: int=-1):
    if sep is not None:
        if isinstance(sep, (bool, int, float)):
            sep = str(sep)
        else:
            sep = str_arg(sep, 'Sep', False)
            sep = None if sep is None or len(sep) == 0 else sep
    maxsplit = -1 if maxsplit is None else max(-1, int_arg(maxsplit, 'Maxsplit'))
    if isinstance(x, (bool, int, float)): x = str(x)
    if x is None: x = ''
    if isinstance(x, str): return str_op(x, sep, maxsplit)
    if isinstance(x, (list, tuple)): return type(x)(p_op(x1, sep, maxsplit) for x1 in x)
    if isinstance(x, dict): return {key: p_op(value, sep, maxsplit) for key, value in x.items()}
    raise TypeError(f'{name} of {type_str(x)} not supported')


def poly_splitlines(x: Any, keepends: bool=False) -> Any:
    """
**Split a string into multiple lines**

* SplitLines(_value_)
* SplitLines(_value_, _keepends_)
* _value_.SplitLines()
* _value_.SplitLines(_keepends_)

```vgr
None.SplitLines() → None
"".SplitLines() → []
"One\\nTwo".SplitLines() → ["One", "Two"]
"One\\nTwo".SplitLines(True) → ["One\\n", "Two"]
```
"""
    if x is None: return None
    keepends = bool_arg(keepends, "KeepEnds")
    if isinstance(x, (bool, int, float)): return str(x).splitlines(keepends)
    if isinstance(x, str): return x.splitlines(keepends)
    if isinstance(x, (list, tuple)): return type(x)(poly_splitlines(x1, keepends) for x1 in x)
    raise TypeError(f'Splitlines with {type_str(x)} not supported')

def poly_join(x: Any, sep: str=None) -> Any:
    """
**Join together the elements of a list as strings**

* Join(_value_, )
* Join(_value_, _sep_)
* _value_.Join()
* _value_.Join(_sep_)

The _sep_ argument is the separator between the strings.
It defaults to an empty string.

If _value_ is a list, the items in it are converted to strings and concatenated
using _sep_. Items in the list that are _None_ are ignored.

If _value_ is an ordinal, it is converted to a string, and
_sep_ is not used. With a _value_ of _None_ or for an empty list an
empty string is returned.

```vgr
None.Join() → ""
"a".Join() → "a"
[].Join() → ""
["a", "b"].Join(", ") → "a, b"
["a", ["b", "c"]].Join("-") → "a-b-c"
1234.Join(0) → "1234"
123.ToString().Ord().Chr().Join(0).ToInt() → 10203
```

Also see `Split()` and `RSplit()`
"""
    if x is None: return ''
    if isinstance(x, (bool, int, float, str)): return str(x)
    if isinstance(sep, (bool, int, float, str)): sep = str(sep)
    sep = '' if sep is None else str_arg(sep, 'Sep', False)
    if isinstance(x, (list, tuple)): return sep.join([poly_join(x1, sep) for x1 in x if x1 is not None])
    raise TypeError(f'Join of {type_str(x)} not supported')

def poly_format(format_string: Any, *args) -> str:
    """
**Format values into a string**

* Format(_format_, _expression_...)
* Format(format_, _expression_...)
* _format_.Format(_expression_...)
* _format_.Format(_expression_...)

Formatting syntax is that used in [Python's str.format()](https://docs.python.org/3/library/string.html#formatstrings)

**Formatting Cheat Sheet**

_*Basic usage*_
```vgr
"Hello, {}".Format("world")    → "Hello, world"
"{0} + {0} = {1}".Format(2, 4) → "2 + 2 = 4"
```

_*Number formatting*_
```vgr
"{:d}".Format(42)       → "42" // decimal
"{:b}".Format(42)       → "101010" // binary
"{:x}".Format(42)       → "2a" // hex, lowercase
"{:X}".Format(42)       → "2A" // hex, uppercase
"{:o}".Format(42)       → "52" // octal
"{:e}".Format(3.14)     → "3.140000e+00" // scientific
"{:.2f}".Format(3.1415) → "3.14" // fixed-point, 2 decimals
```

_*Alignment & width*_
```vgr
"{:<10}".Format("hi")  →  "hi        " // left align
"{:>10}".Format("hi")  →  "        hi" // right align
"{:^10}".Format("hi")  →  "    hi    " // center
"{:*^10}".Format("hi") →  "****hi****" // custom fill
```

_*Signs & numbers*_
```vgr
"{:+d}".Format(42)     → "+42"
"{:+d}".Format(-42)    → "-42"
"{: d}".Format(42)     → " 42" // space for positive
"{:,}".Format(1234567) → "1,234,567" // thousands sep
"{:_}".Format(1234567) → "1_234_567"
```

_*Accessing elements*_
```vgr
Set person To {"name": "Alice", "age": 25}
"{0[name]} is {0[age]}".Format(person) → "Alice is 25"
```

_*Format control*_
```vgr
"{0} {0!r} {0!s}".Format("hi") → "hi 'hi' hi" // raw vs str formatting
"{0:.{1}f}".Format(3.14159, 2) → "3.14" // precision via argument
```
"""
    # TODO: the syntax {0.x} is also defined, but when tested it can't seem to find the attribute
    if format_string is None: return None
    if isinstance(format_string, (bool, int, float)): return str(format_string)
    if isinstance(format_string, (list, tuple)):
        return ''.join(poly_format(f, *args) for f in format_string)
    if isinstance(format_string, str): return format_string.format(*args)
    raise TypeError(f'Format with {type_str(format_string)} not supported')

def poly_translate(x: Any, from_str: Any, to_str: Any=None) -> Any:
    """
**Perform character-by-character conversion or deletion**

* Translate(_value_, _expression_)
* Translate(_value_, _expression_, _expression_)
* _value_.Translate(_expression_)
* _value_.Translate(_expression_, _expression_)

If the two-arguments form is used, or the replacement string is empty or _None_,
the characters are deleted.

```vgr
"abc".Translate("b") → "ac"
"abc".Translate("b","*") → "a*c"
"dog".Translate(string.ascii_lowercase, string.ascii_uppercase) → "DOG"
["cat", "dog"].Translate("ao", "40") → ["c4t", "d0g"]
"cat".Translate({"c".Ord(): "r".Ord()}) → "rat"
```
"""
    if x is not None and from_str is not None:
        if isinstance(x, str):
            # A lot of assumptions here, but we'll try to use it as requested
            # This would be a good case for somebody to make a JSON object (or save it)
            # and do a Load-From into a top-level object
            # NB: this works ordinal-to-ordinal
            if isinstance(from_str, dict): return x.translate(from_str)
            if isinstance(from_str, (int, float)): return poly_translate(x, str(from_str), to_str)
            if isinstance(from_str, str) and len(from_str) > 0:
                if to_str is None: to_str = ''
                if isinstance(to_str, (int, float)): return str(to_str)
                if isinstance(to_str, str): return x.translate(_maketrans(from_str, to_str))
        else:
            if isinstance(x, (int, float)): return poly_translate(str(x), from_str, to_str)
            if isinstance(x, list): return [poly_translate(x1, from_str, to_str) for x1 in x]
            if isinstance(x, tuple): return (poly_translate(x1, from_str, to_str) for x1 in x)
    return x

#---------------------------------------------

def poly_ord(x:Any) -> Any:
    """
**Convert a string to its ordinal values**

* Ord(_value_)
* _value_.Ord()

If _value_ is a single character, the ordinal is returned; for an multi-character
string, an array of ordinals are returned.
The operation is distributed across lists and dictionaries.

```vgr
"5".Ord() → 53
5.Ord() → 5
"cat".Ord() → [99, 97, 116]
["cat", "dog"].Ord() → [[99, 97, 116], [100, 111, 103]]
```

Also see `Chr()`
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

* Chr(_value_)
* _value_.Chr()

If _value_ is a value for a Unicode character a single character string
is returned.
The operation is distributed across lists and dictionaries.

```vgr
99.Chr() → "c"
print [99, 97, 116].Chr() → ["c", "a", "t"]
```

Also see `Ord()`
"""
    if x is None: return None
    if isinstance(x, (int, float)): return chr(int(x)) if 0 <= x <= 0x10FFFF else x
    if isinstance(x, (bytes, bytearray)): return ''.join(chr(b) for b in x)
    if isinstance(x, (list, tuple)): return type(x)(poly_chr(x1) for x1 in x)
    if isinstance(x, dict): return {k: poly_chr(v) for k, v in x.items()}
    return x

#---------------------------------------------

def _maketrans(from_str: str, to_str: str=''):
    return str.maketrans({from_str[i]: to_str[i] if i < len(to_str) else None for i in range(len(from_str))})
