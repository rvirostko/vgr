"""
Various string manipulation functions using either the string class or regular expressions
"""

from functools import reduce
from typing import Any, Callable
from re import Pattern
import re

from .common import (
    AnyType,
    bool_arg,
    int_arg,
    NoneType,
    str_arg,
    X_None_Op,
)
from .inequ import poly_eq
from .match import poly_matches_all, poly_matches
from .reg_ex import poly_regex_replace
from .type import poly_type
from .types import poly_str
from .registry import builtin

_NOT_FOUND = -1
_SCALAR_TYPES = (bool, int, float, str, Pattern)

# Operations table key for when Y value is a collection
Y_Coll_Op = (AnyType, list)

def _exec_x_op(x: Any, name: str, op: Callable[[Any], Any], string_op, op_table) -> Any:
    """General purpose string operation execution for no-args methods on str"""
    operation = op_table.get(type(x))
    if operation is None: raise ValueError(f'{name}() on {poly_type(x)!r} not possible')
    return operation(op, x, string_op)

#---------------------------------------------

# For no-args string methods that return a string, e.g. "x.Upper()"
# These are transformational on string items, but idempotent on others
_str_operations = {
    NoneType: lambda _op, _x, _sm: None,
    bool:     lambda _op,  x, _sm: x,
    int:      lambda _op,  x, _sm: x,
    float:    lambda _op,  x, _sm: x,
    str:      lambda _op,  x,  sm: sm(x),
    list:     lambda  op,  x, _sm: [op(x1) for x1 in x ],
    dict:     lambda  op,  x, _sm: {key: op(value) for key, value in x.items()},
    Pattern:  lambda _op,  x,  sm: sm(x.pattern),
}

def _exec_str_op(x: Any, name: str, op: Callable[[Any], Any], string_op) -> Any:
    return _exec_x_op(x, name, op, string_op, _str_operations)

@builtin("StringLen")
def poly_stringlen(x: Any=None) -> Any:
    """
**Return the length of a string**

* StringLen(*value*)
* *value*.StringLen()

If *value* is of any type except string, `None` is returned.

```vgr
"foo".StringLen() → 3
7.StringLen() → None
["cat", "kitten"].StringLen() → [3, 6]
```

Also see `Length()`
"""
    return _exec_str_op(x, 'StringLen', poly_stringlen, str.__len__)

@builtin("ReverseStr")
def poly_reversestr(x: Any=None) -> Any:
    """
**Returns the characters of the string in reverse order**

* ReverseStr(*value*)
* *value*.ReverseStr()

```vgr
None.ReverseStr() → None
123.ReverseStr() → 123
"abc".ReverseStr() → "cba"
["abc", "xyz"].ReverseStr() → ["cba", "zyx"]
```

Also see `Reverse()`
"""
    return _exec_str_op(x, 'ReverseStr', poly_reversestr, lambda s: s[::-1])

@builtin("Capitalize")
def poly_capitalize(x: Any=None) -> Any:
    """
**Return the capitalized version of a string**

* Capitalize(*value*)
* *value*.Capitalize()

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

@builtin("CaseFold")
def poly_casefold(x: Any=None) -> Any:
    """
**Return a caseless version of a string**

* CaseFold(*value*)
* *value*.CaseFold()

```vgr
None.CaseFold() → None
"aBc".CaseFold() → "abc"
"The Title".CaseFold() → "the title"
"the TITLE".CaseFold() → "the title"
["Abc", "Xyz"].CaseFold() → ["abc", "xyz"]
123.CaseFold() → 123
```
"""
    return _exec_str_op(x, 'CaseFold', poly_casefold, str.casefold)

@builtin("Lower")
def poly_lower(x: Any=None) -> Any:
    """
**Return a lowercase version of a string**

* Lower(*value*)
* *value*.Lower()

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

@builtin("SwapCase")
def poly_swapcase(x: Any=None) -> Any:
    """
**Return a string with upper and lower case characters swapped**

* SwapCase(*value*)
* *value*.SwapCase()

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

@builtin("TitleCase")
def poly_title(x: Any=None) -> Any:
    """
**Title-case words in a string**

* TitleCase(*value*)
* *value*.TitleCase()

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

@builtin("Upper")
def poly_upper(x: Any=None) -> Any:
    """
**Return an upper case version of a string**

* Upper(*value*)
* *value*.Upper()

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
    bool:     lambda _op, _x, _sm: False,
    int:      lambda _op, _x, _sm: False,
    float:    lambda _op, _x, _sm: False,
    str:      lambda _op,  x,  sm: sm(x),
    list:     lambda  op,  x, _sm: [op(x1) for x1 in x],
    dict:     lambda  op,  x, _sm: {key: op(value) for key, value in x.items() if isinstance(value, (str, list, dict))},
    Pattern:  lambda _op,  x,  sm: sm(x.pattern),
}

def _exec_bool_op(x: Any, name: str, op: Callable[[Any], Any], string_op) -> Any:
    return _exec_x_op(x, name, op, string_op, _bool_operations)

@builtin("IsAlphaNumeric")
def poly_is_alnum(x: Any=None) -> Any:
    """
**Is a value an alpha-numeric string**

* IsAlphaNumeric(*value*)
* *value*.IsAlphaNumeric()

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
    return _exec_bool_op(x, 'IsAlphaNnumeric', poly_is_alnum, str.isalnum)

@builtin("IsAlpha")
def poly_is_alpha(x: Any=None) -> Any:
    """
**Is a value an alphabetic string**

* IsAlpha(*value*)
* *value*.IsAlpha()

A string is alphabetic if all characters in the string
are alphabetic and there is at least one character in the string.

```vgr
"FooBar".IsAlpha() → True
"Foo Bar".IsAlpha() → False
["Hello", "Gruezi", "Olá"].IsAlpha() → [True, True, True]
```
"""
    return _exec_bool_op(x, 'IsAlpha', poly_is_alpha, str.isalpha)

@builtin("IsAscii")
def poly_is_ascii(x: Any=None) -> Any:
    """
**Is a value a string composed of all ASCII characters**

* IsAscii(*value*)
* *value*.IsAscii()

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
    return _exec_bool_op(x, 'IsAscii', poly_is_ascii, str.isascii)

@builtin("IsDecimal")
def poly_is_decimal(x: Any=None) -> Any:
    """
**Is the value a string of decimal characters**

* IsDecimal(*value*)
* *value*.IsDecimal()

A string is a decimal string if all characters in the string
are decimal and there is at least one character in the string.
Decimal characters are the digits 0–9 or Unicode characters
from the *Nd* (Decimal Number) category.

This is the most restrictive of the number related tests.

```vgr
"123".IsDecimal() → True
"1 2 3".IsDecimal() → False
["", None].IsDecimal() → [False, False]
```

Also see `IsDigit()` and `IsNumeric()`
"""
    return _exec_bool_op(x, 'IsDecimal', poly_is_decimal, str.isdecimal)

@builtin("IsDigit")
def poly_is_digit(x: Any=None) -> Any:
    """
**Is a value a string of digits**

* IsDigit(*value*)
* *value*.IsDigit()

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
    return _exec_bool_op(x, 'IsDigit', poly_is_digit, str.isdigit)

@builtin("IsLower")
def poly_is_lower(x: Any=None) -> Any:
    """
**Is a value a string of lowercase characters**

* IsLower(*value*)
* *value*.IsLower()

A string is lowercase if all cased characters in the string
are lowercase and there is at least one cased character in the string.

```vgr
"foo-bar".IsLower() → True
"Foo-Bar".IsLower() → False
["3.1415", ""].IsLower() → [False, False]
```
"""
    return _exec_bool_op(x, 'IsLower', poly_is_lower, str.islower)

@builtin("IsNumeric")
def poly_is_numeric(x: Any=None) -> Any:
    """
**Is a value a string of numeric characters**

* IsNumeric(*value*)
* *value*.IsNumeric()

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
    return _exec_bool_op(x, 'IsNumeric', poly_is_numeric, str.isnumeric)

@builtin("IsPrintable")
def poly_is_printable(x: Any=None) -> Any:
    """
**Is a value a string of printable characters**

* IsPrintable(*value*)
* *value*.IsPrintable()

A string is printable if all of its characters are considered printable
–generally characters which are not control characters or undefined–
or if it is empty.

```vgr
"foo bar".IsPrintable() → True
"foo\nbar".IsPrintable() → False
```
"""
    return _exec_bool_op(x, 'IsPrintable', poly_is_printable, str.isprintable)

@builtin("IsSpace")
def poly_is_space(x: Any=None) -> Any:
    """
**Is a value a string of whitespace characters**

* IsSpace(*value*)
* *value*.IsSpace()

A string is whitespace if all characters in the string are whitespace
and there is at least one character in the string.

```vgr
"".IsSpace() → False
"Foo".IsSpace() → False
["\\t\\n ", None].IsSpace() → [True, False]
```
"""
    return _exec_bool_op(x, 'IsSpace', poly_is_space, str.isspace)

@builtin("IsTitle")
def poly_is_title(x: Any=None) -> Any:
    """
**Is a value a string of title-case characters**

* IsTitle(*value*)
* *value*.IsTitle()

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

```vgr
"Foo".IsTitle() → True
"foo".IsTitle() → False
["aA","Bb"].IsTitle() → [False, True]
```
"""
    return _exec_bool_op(x, 'IsTitle', poly_is_title, str.istitle)

@builtin("IsUpper")
def poly_is_upper(x: Any=None) -> Any:
    """
**Is a value a string of uppercase characters**

* IsUpper(*value*)
* *value*.IsUpper()

A string is uppercase if all cased characters in the string are uppercase
and there is at least one cased character in the string.

```vgr
"foo".IsUpper() → False
"FOO".IsUpper() → True
["FOO-BAR", "Foo Bar"].IsUpper() → [True, False]
```
"""
    return _exec_bool_op(x, 'IsUpper', poly_is_upper, str.isupper)

#---------------------------------------------

# For two arg functions : e.g. x.Strip(y)/(None)
# [" xFoo ", None, 27, True].strip() -> ["xFoo", None, 27, True]
# ["xFoo", None, 27, True].strip("x") -> ["Foo", None, 27, True]
# [" xFoo ", None, 27, True].strip([None, "x"]) -> ["Foo", None, 27, True]
_str_str_operations = {
    X_None_Op:      lambda _op, _x, _y, _sm: None,
    Y_Coll_Op:      lambda  op,  x,  y, _sm: reduce(op, y, x),
    (str, str):     lambda _op,  x,  y,  sm: sm(x, y),
    (list, str):    lambda  op,  x,  y, _sm: [op(x1, y) for x1 in x],
    (dict, str):    lambda  op,  x,  y, _sm: {key: op(value, y) for key, value in x.items()},
}

def _exec_x_y_op(x: Any, y: Any, name: str, op: Callable[[Any, Any], Any], string_op, op_table) -> Any:
    """General purpose string operation execution for methods on str that take a single str arg"""
    operation = None
    if x is None:
        operation = op_table.get(X_None_Op)
    else:
        x = _as_str(x)
        if isinstance(y, list):
            operation = op_table.get(Y_Coll_Op)
        else:
            # Many ops will accept a None for their arg and take default action
            # So we use the same as if it was a string
            operation = op_table.get((type(x), str if y is None else type(y)))
    if operation is None: raise ValueError(f'{name}() between {poly_type(x)!r} and {poly_type(y)!r} not possible')
    return operation(op, x, y, string_op)

def _exec_str_str_op(x: Any, y: Any, name: str, op: Callable[[Any, Any], Any], string_op) -> Any:
    """For str/str transformational methods that are idempotent on non-string ordinals"""
    if isinstance(x, (NoneType, bool, int, float, Pattern)): return x
    return _exec_x_y_op(x, y, name, op, string_op, _str_str_operations)

#---------------------------------------------

@builtin("Strip")
def poly_strip(*args) -> Any:
    """
**Remove leading and trailing characters from a string**

* Strip(*value*)
* Strip(*value*, *expression*&hellip;)
* *value*.Strip()
* *value*.Strip(*expression*&hellip;)

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
        if isinstance(chars, Pattern):
            start = 0
            xlen = len(x)
            end = xlen + 1
            for m in re.finditer(chars, x):
                if m.start() == 0: start = m.end()
                if m.end() == xlen: end = m.start()
            return x[start:end]
        return _exec_str_str_op(x, chars, 'Strip', _strip, str.strip)
    if not args: return None
    x, *args = args
    if isinstance(x, (NoneType, bool, int, float, Pattern)): return x
    return _strip(x) if not args else reduce(_strip, args, x)

@builtin("LeftStrip")
def poly_lstrip(*args) -> Any:
    """
**Remove leading characters from a string**

* LeftStrip(*value*)
* LeftStrip(*value*, *expression*&hellip;)
* *value*.LeftStrip()
* *value*.LeftStrip(*expression*&hellip;)

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
        if isinstance(chars, Pattern):
            start = 0
            for m in re.finditer(chars, x):
                if m.start() == 0: start = m.end()
            return x[start:len(x) + 1]
        return _exec_str_str_op(x, chars, 'LeftStrip', _lstrip, str.lstrip)
    if not args: return None
    x, *args = args
    if isinstance(x, (NoneType, bool, int, float, Pattern)): return x
    return _lstrip(x) if not args else reduce(_lstrip, args, x)

@builtin("RightStrip")
def poly_rstrip(*args) -> Any:
    """
**Remove trailing characters from a string**

* RightStrip(*value*)
* RightStrip(*value*, *expression*&hellip;)
* *value*.RightStrip()
* *value*.RightStrip(*expression*&hellip;)

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
        if isinstance(chars, Pattern):
            xlen = len(x)
            end = xlen + 1
            for m in re.finditer(chars, x):
                if m.end() == xlen: end = m.start()
            return x[0:end]
        return _exec_str_str_op(x, chars, 'RightStrip', _rstrip, str.rstrip)
    if not args: return None
    x, *args = args
    if isinstance(x, (NoneType, bool, int, float, Pattern)): return x
    return _rstrip(x) if not args else reduce(_rstrip, args, x)

@builtin("RemovePrefix")
def poly_remove_prefix(*args) -> Any:
    """
**Remove a prefix from a string if present**

* RemovePrefix(*value*)
* RemovePrefix(*value*, *prefix*&hellip;)
* *value*.RemovePrefix()
* *value*.RemovePrefix(*prefix*&hellip;)

```vgr
None.RemovePrefix() → None
"http://example.com".RemovePrefix() → "http://example.com"
"http://example.com".RemovePrefix("http://") → "example.com"
"http://example.com".RemovePrefix("http://", "https://") → "example.com"
"http://example.com".RemovePrefix(["http://", "https://"]) → "example.com"
"http://example.com".RemovePrefix(r/https?:[/]{2}/i) → "example.com"
["a/file.txt","b/file.txt"].RemovePrefix("a/", "b/") → ["file.txt", "file.txt"]
1234.RemovePrefix(12) → "34"
```

Also see `RemoveSuffix()`
"""
    def _removeprefix(x: Any, prefix: Any) -> Any:
        if prefix is None: return x
        if isinstance(prefix, Pattern):
            start = 0
            for m in re.finditer(prefix, x):
                if m.start() == 0: start = m.end()
            return x[start:len(x) + 1]
        if isinstance(prefix, (bool, int, float)): prefix = str(prefix)
        return _exec_str_str_op(x, prefix, 'RemovePrefix', _removeprefix, str.removeprefix)
    if not args: return None
    x, *args = args
    if x is None or not args: return x
    x = _as_str(x)
    return reduce(_removeprefix, args, x)

@builtin("RemoveSuffix")
def poly_remove_suffix(*args) -> Any:
    """
**Remove a suffix from a string if present**

* RemoveSuffix(*value*)
* RemoveSuffix(*value*, *prefix*&hellip;)
* *value*.RemoveSuffix()
* *value*.RemoveSuffix(*prefix*&hellip;)

```vgr
None.RemoveSuffix() → None
"http://example.com".RemoveSuffix() → "http://example.com"
"http://example.com".RemoveSuffix(".com") → "http://example"
"http://example.com".RemoveSuffix(".net", ".com") → "http://example"
"http://example.com".RemoveSuffix([".net", ".com"]) → "http://example"
"http://example.com".RemoveSuffix(r/[.](com|org|net)/i) → "http://example"
["file.txt","file.md"].RemoveSuffix(".md", ".txt") → ["file", "file"]
1234.RemoveSuffix(34) → "12"
```

Also see `RemovePrefix()`
"""
    def _removesuffix(x: Any, suffix: Any) -> Any:
        if suffix is None: return x
        if isinstance(suffix, Pattern):
            xlen = len(x)
            end = xlen + 1
            for m in re.finditer(suffix, x):
                if m.end() == xlen: end = m.start()
            return x[0:end]
        if isinstance(suffix, (bool, int, float)): suffix = str(suffix)
        return _exec_str_str_op(x, suffix, 'RemoveSuffix', _removesuffix, str.removesuffix)
    if not args: return None
    x, *args = args
    if x is None or not args: return x
    x = _as_str(x)
    return reduce(_removesuffix, args, x)

#---------------------------------------------

def _exec_bool_str_op(x: Any, y: Any, name: str, op: Callable[[Any, Any], Any], string_op) -> Any:
    """For str/str functions that return a bool"""
    def flatten(arg):
        return list(y for a in arg for y in (flatten(a) if isinstance(a, list) else [a]))
    if isinstance(x, list): return list(op(x1, y) for x1 in x)
    if isinstance(x, dict): return {key: op(value, y) for key, value in x.items() if isinstance(value, str)}
    if isinstance(x, str):
        for y1 in flatten(y):
            if y1 is None: continue
            if isinstance(y1, Pattern):
                if string_op(x, y1): return True
            else:
                y1 = _as_str(y1)
                if isinstance(y1, str):
                    if y1 and string_op(x, y1): return True
                else:
                    raise ValueError(f'{name}() between {poly_type(x)!r} and {poly_type(y1)!r} not possible')
    return False

@builtin("StartsWith")
def poly_starts_with(*args: Any) -> Any:
    """
**Does a string start with one or more prefixes**

* StartsWith(*value*, *prefix*&hellip;)
* *value*.StartsWith(*prefix*&hellip;)

The *prefix* argument must be either a string or a list of strings. Lists and individual strings
may be intermixed.

If *value* is a list, the operation is distributed over the values in the list.
If *value* is a dictionary, the operation is distributed over all keys that are strings.
If *value* is neither a list, dictionary, or string, `False` is returned.

```vgr
"foo".StartsWith("f") → True
["foo", "bar", "cat", 7].StartsWith("a", ["b", "c"]) → [False, True, True, False]
{"one": "a", "two": "d", "three": 3}.StartsWith("a", "b", "c") → {"one": True, "two": False}
{"one": "a", "two": "d", "three": 3}.StartsWith(r/[abc]/) → {'one': True, 'two': False}
```

Also see `EndsWith()`
"""
    def _starts_with(s: str, prefix: Any) -> bool:
        if isinstance(prefix, str): return s.startswith(prefix)
        if isinstance(prefix, Pattern):
            m = re.match(prefix, s)
            return m is not None and m.start() == 0
    if not args: return False
    return _exec_bool_str_op(args[0], list(args[1:]), "StartsWith", poly_starts_with, _starts_with)

@builtin("EndsWith")
def poly_ends_with(*args: Any) -> bool:
    """
**Does a string end with one or more prefixes**

* EndsWith(*value*, *suffix*&hellip;)
* *value*.EndsWith(*suffix*&hellip;)

The *suffix* argument must be either a string or a list of strings. Lists and individual strings
may be intermixed.

If *value* is a list, the operation is distributed over the values in the list.
If *value* is a dictionary, the operation is distributed over all keys that are strings.
If *value* is neither a list, dictionary, or string, `False` is returned.

```vgr
"foo".EndsWith("oo") → True
"foo".EndsWith("a", "e", "i", "o", "u") → True
["foo", "bar"].EndsWith("o") → [True, False]
"foo".EndsWith(["a", "e"], ["i", "o", "u"]) → True
"foo".EndsWith(r/[aeiou]/) → True
```

Also see `StartsWith()`
"""
    def _ends_with(s: str, suffix: Any) -> bool:
        if isinstance(suffix, str): return s.endswith(suffix)
        if isinstance(suffix, Pattern):
            slen = len(s)
            for m in re.finditer(suffix, s):
                if m.end() == slen: return True
        return False
    if not args: return False
    return _exec_bool_str_op(args[0], list(args[1:]), "EndsWith", poly_ends_with, _ends_with)

_string_int_ops = {
    (str, int)   : lambda _op, x, y,  sm: sm(x, y),
    (list, int)  : lambda  op, x, y, _sm: [op(x1, y) for x1 in x],
    (dict, int)  : lambda  op, x, y, _sm: {key: op(value, y) for key, value in x.items()},
}

def exec_str_int_op(x: Any, y: Any, name: str, op: Callable[[Any, Any], Any], string_op) -> Any:
    # For these types, the operation is idempotent
    if isinstance(x, (NoneType, bool, int, float, Pattern)): return x
    return _exec_x_y_op(x, y, name, op, string_op, _string_int_ops)

@builtin("ExpandTabs")
def poly_expand_tabs(x: Any=None, tabsize: Any=8) -> Any:
    """
**Converts tabs in a string into spaces**

* ExpandTabs(*value*)
* ExpandTabs(*value*, *tabsize*)
* *value*.ExpandTabs()
* *value*.ExpandTabs(*tabsize*)

*tabsize* defaults to 8 and is limited from 0 to 64.

```vgr
None.ExpandTabs() → None
"\\taBc\\t".ExpandTabs() → "        aBc     "
"\\taBc\\t".ExpandTabs(2) → "  aBc "
["A\\tbc", "X\\tyz"].ExpandTabs(0) → ["Abc", "Xyz"]
123.ExpandTabs() → 123
```
"""
    return exec_str_int_op(x, min(max(0, int_arg(tabsize, 'Tabsize')), 64), "ExpandTabs", poly_expand_tabs, str.expandtabs)

@builtin("LeftStr")
def poly_leftstr(x: Any=None, length: Any=1) -> Any:
    """
**Returns the leftmost characters of a string**

* LeftStr(*value*)
* LeftStr(*value*, *length*)
* *value*.LeftStr()
* *value*.LeftStr(*length*)

Without a *length* argument a single character is returned.

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
    return exec_str_int_op(_as_str(x), max(1, int_arg(length, 'Length')), "LeftStr", poly_leftstr, lambda x, length: x[:length])

@builtin("RightStr")
def poly_rightstr(x: Any=None, length: Any=1) -> Any:
    """
**Retunrs the rightmost characters of a string**

* RightStr(*value*)
* RightStr(*value*, *length*)
* *value*.RightStr()
* *value*.RightStr(*length*)

Without a *length* argument a single character is returned.

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
    return exec_str_int_op(_as_str(x), max(0, int_arg(length, 'Length')), "RightStr", poly_rightstr, lambda x, length: x[-length:])

#---------------------------------------------

@builtin("SubStr")
def poly_substr(x: Any=None, start: Any=0, length: Any=1) -> Any:
    """
**Return a portion of a string**

* SubStr(*value*)
* SubStr(*value*, *start*)
* SubStr(*value*, *start*, *length*)
* *value*.SubStr()
* *value*.SubStr(*start*)
* *value*.SubStr(*start*, *length*)
* *value*[*index*]

If not provided, *start* defaults to zero and *length* to one.
The *start* index is zero based.

```vgr
None.SubStr() → None
"aBc".SubStr() → "a"
"aBc".SubStr(1, 2) → "Bc"
"The title".SubStr(4, 5) → "title"
["Abc", "Xyz"].SubStr(1) → ["b", "y"]
123.SubStr(2, 1) → 123
```

Also see `LeftStr()`, `RightStr()`, and `Slice()`
"""
    # For these types, the operation is idempotent
    if isinstance(x, (NoneType, bool, int, float)): return x
    start = int_arg(start, 'Start')
    length = 1 if length is None else max(0, int_arg(length, 'Length'))
    if isinstance(x, list): return list(poly_substr(x1, start, length) for x1 in x)
    if isinstance(x, dict): return {key: poly_substr(value, start, length) for key, value in x.items()}
    x = _as_str(x)
    if isinstance(x, str):
        start = start if start >= 0 else start + len(x)
        return x[start:start + length]
    raise ValueError(f'SubStr() on {poly_type(x)!r} not possible')

_string_loc_ops = {
    (str, str):     lambda _op, x, y,  sm: sm(x, y),
    (str, Pattern): lambda _op, x, y,  sm: sm(x, y),
    (list, str):    lambda  op, x, y, _sm: [op(x1, y) for x1 in x],
    (dict, str):    lambda  op, x, y, _sm: {
                                            key: op(value, y) for key, value in x.items()
                                                if isinstance(value, (str, list, dict))
                                          },
}

@builtin("CountOf")
def poly_count(x: Any=None, sub: Any=None) -> Any:
    """
**Return the count of a value in another**

* CountOf(*value*, *substr*)
* *value*.CountOf(*substr*)

```vgr
// General
None.CountOf("a") → 0
121.CountOf("2") → 1 // int converted to string

// With Strings
"".CountOf("x") → 0
"aaaBc".CountOf() → 5
"aaaBc".CountOf("") → 5
"aaaBc".CountOf(None) → 5
"aaaBc".CountOf("a") → 3
"aaaBc".CountOf("aa") → 1 // occurrences are non-overlapping
"aaabbaac".CountOf(r/a+/) → 2

// With Lists
Set fruits To ["apple", "banana", "apple", "orange", "apple"]
fruits.CountOf() → 5
fruits.CountOf("apple") → 3
fruits.CountOf("grape") → 0
fruits.CountOf(r/(an)+/) → 2 // banana and orange

// With Dictionaries
Set fruit_colors To {"apple": "red", "banana": "yellow"}
fruit_colors.CountOf() → 2
fruit_colors.CountOf("apple") → 1
fruit_colors.CountOf("grape") → 0
fruit_colors.CountOf(r/a/) → 2 // both contain "a"
```
"""
    def _re_count(x: str, p: Pattern) -> int: return len(re.findall(p, x))
    if x is None: return 0
    sub = str_arg(sub, 'Substr', False, True)
    if isinstance(x, dict): x = list(x.keys())
    if isinstance(x, list):
        if isinstance(sub, str) and len(sub) == 0: return len(x)
        cmp = poly_matches_all if isinstance(sub, Pattern) else poly_eq
        return sum(1 for x1 in x if cmp(x1, sub))
    x = _as_str(x)
    if len(x) == 0: return 0
    if isinstance(sub, Pattern):
        return _exec_x_y_op(x, sub, 'CountOf', poly_count, _re_count, _string_loc_ops)
    sub = '' if sub is None else sub
    return len(x) if len(sub) == 0 else _exec_x_y_op(x, sub, 'CountOf', poly_count, str.count, _string_loc_ops)

@builtin("IndexOf")
def poly_index_of(value: Any=None, sub: Any=None) -> Any:
    """
**Returns the *lowest* index of one item in another**

* IndexOf(*value*, *substr*)
* *value*.IndexOf(*substr*)

The returned index is zero based, with -1 returned if *substr* is not found.
When *value* is a string, the behavior is the same as with `FindStr()`.

```vgr
// General
None.IndexOf("a") → -1
123.IndexOf("2") → 1 // int converted to string

// With Strings
"aaaBc".IndexOf("") → -1
"aaaBc".IndexOf("z") → -1
"aaaBc".IndexOf("aB") → 2
"aaaBc".IndexOf(r/ab/i) → 2

// With Lists
Set fruits To ["apple", "banana", "apple", "orange", "apple"]
fruits.IndexOf("apple") → 0
fruits.IndexOf("grape") → -1
```

Also see `RIndexOf()` and `FindStr()`
"""
    if value is None: return _NOT_FOUND
    if isinstance(value, _SCALAR_TYPES):
        if sub is None: return _NOT_FOUND
        value = _as_str(value)
        if isinstance(sub, Pattern): return _re_find(value, sub)
        sub = _as_str(sub)
        if isinstance(sub, str): return _NOT_FOUND if len(sub) == 0 else value.find(sub)
        raise TypeError(f'Type {poly_type(sub)!r} cannot be used for Substr argument')
    if isinstance(value, list):
        if isinstance(sub, Pattern):
            # We skip None, list, and dict
            return next((i for i, v in enumerate(value)
                         if isinstance(v, _SCALAR_TYPES) and poly_matches(_as_str(v), sub)),
                        _NOT_FOUND)
        return next((i for i, v in enumerate(value)
                     if poly_eq(v, sub)),
                    _NOT_FOUND)
    raise TypeError(f'Type {poly_type(value)!r} cannot be used with IndexOf')

def _re_find(x: str, p: Pattern) -> int:
    return _NOT_FOUND if (m := re.search(p, x)) is None else m.start()

@builtin("RIndexOf")
def poly_rindex(x: Any=None, sub: Any=None) -> Any:
    """
**Returns the *highest* index of one item in another**

* RIndexOf(*value*, *substr*)
* *value*.RIndexOf(*substr*)

The returned index is zero based, with -1 returned if *substr* is not found.
When *value* is a string, the behavior is the same as with `RFindStr()`.

```vgr
// General
None.RIndexOf("a") → -1
1232.RIndexOf("2") → 3 // int converted to string

// With Strings
"aaaBc".RIndexOf("") → -1
"aaaBc".RIndexOf("z") → -1
"aaaBc".RIndexOf("aB") → 2

// With Lists
Set fruits To ["apple", "banana", "apple", "orange", "apple"]
fruits.RIndexOf("apple") → 4
fruits.RIndexOf("grape") → -1

// With Dictionaries
Set fruit_colors To {"apple": "red", "banana": "yellow"}
fruit_colors.RIndexOf("apple") → 0  // key present
fruit_colors.RIndexOf("grape") → -1 // key not present
```

Also see `IndexOf()` and `RFindStr()`
"""
    if x is None: return -1
    sub = str_arg(sub, 'str', False, True) or ''
    if isinstance(x, list):
        if isinstance(sub, str) and len(sub) == 0: return -1
        cmp = poly_matches_all if isinstance(sub, Pattern) else poly_eq
        return next((i for i in range(len(x) - 1, -1, -1) if cmp(x[i], sub)), -1)
    if isinstance(x, dict): return 0 if sub in x else -1
    if isinstance(x, (bool, int, float)): x = str(x)

    x = _as_str(x)
    if len(x) == 0: return -1
    if isinstance(sub, Pattern):
        return -1 if len(m := list(sub.finditer(x))) == 0 else m[-1].start()
    if sub is None or len(sub) == 0: return -1

    return _exec_x_y_op(x, sub, 'RIndexOf', poly_rindex, str.rfind, _string_loc_ops)

@builtin("FindStr")
def poly_findstr(value: Any=None, substr: Any=None) -> Any:
    """
**Returns the *lowest* index of one string in another**

* FindStr(*value*, *substr*)
* *value*.FindStr(*substr*)

The returned index is zero based.

If *substr* cannot be found, -1 is returned.

```vgr
None.FindStr("a") → None
"aaaBc".FindStr("") → -1
"aaaBc".FindStr("z") → -1
"aaaBc".FindStr("a") → 0
["A.b.c", "X.y.z"].FindStr(".") → [1, 1]
123.FindStr("1") → 0
```

Also see `RFindStr()` and `IndexOf()`
"""
    def _findstr(s: str, sub: Any) -> int:
        if isinstance(sub, Pattern):
            return _NOT_FOUND if (m := sub.search(s)) is None else m.start()
        return _NOT_FOUND if len(sub) == 0 else s.find(sub)
    value = _as_str(value)
    if substr is None: return _NOT_FOUND
    if isinstance(substr, Pattern):
        pass
    elif isinstance(substr, _SCALAR_TYPES):
        substr = _as_str(substr)
    else:
        raise TypeError(f'Type {poly_type(substr)!r} cannot be used for Substr argument')
    substr = substr if isinstance(substr, Pattern) else str_arg(substr, 'Substr', False)
    return _exec_x_y_op(value, substr, 'FindStr', poly_findstr, _findstr, _string_loc_ops)

@builtin("RFindStr")
def poly_rfindstr(x: Any=None, sub: Any=None) -> Any:
    """
**Returns the *highest* index of one string in another**

* RFindStr(*value*, *substr*)
* *value*.RFindStr(*substr*)

The returned index is zero based.

If *substr* cannot be found, -1 is returned.

When *substr* is a regular expression, the start position of the rightmost
non-overlapping match, as calculated from the start of the string, is returned.
For variable-length or complex patterns the semantics may conflict with
using a fixed string.

```vgr
None.RFindStr("a") → None
"aaaBc".RFindStr("") → 5
"aaaBc".RFindStr("z") → -1
"aaaBc".RFindStr("a") → 2
["A.b.c", "X.y.z"].RFindStr(".") → [3, 3]
123.RFindStr("1") → 0
```

Also see `FindStr()` and `RIndexOf()`
"""
    def _rfindstr(s: str, sub: Any) -> int:
        if isinstance(sub, Pattern):
            return -1 if len(m := list(sub.finditer(s))) == 0 else m[-1].start()
        return s.rfind(sub)
    x = _as_str(x)
    sub = sub if isinstance(sub, Pattern) else str_arg(sub, 'Substr', False) or ''
    return _exec_x_y_op(x, sub, 'RFindStr', poly_rfindstr, _rfindstr, _string_loc_ops)

#---------------------------------------------

def _layout_opt(x: Any, width: int, fillchar: str, op, str_op) -> Any:
    width = 0 if width is None else min(max(0, int_arg(width, "Width")), 256)
    fillchar = ' ' if fillchar is None else str_arg(fillchar, "Fillchar")[0]
    if x is None: return fillchar * width
    if isinstance(x, list): return list(op(x1, width, fillchar) for x1 in x)
    x = poly_str(x) if isinstance(x, dict) else _as_str(x)
    return str_op(x, width, fillchar)

@builtin("Center")
def poly_center(x: Any=None, width: int=0, fillchar: str=' ') -> Any:
    """
**Create a centered string of the given width**

* Center(*value*, *width*)
* Center(*value*, *width*, _pad_)
* *value*.Center(_width_)
* *value*.Center(_width_, _pad_)

If the *value* to be centered is `None`, it is treated as an empty string.
The *width* argument is interpreted as a numeric value. If `None`, zero is assumed.
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

@builtin("LeftJustify")
def poly_ljust(x: Any=None, width: int=0, fillchar: str=' ') -> Any:
    """
**Create a string of the given width with contents left aligned**

* LeftJustify(*value*, *width*)
* LeftJustify(*value*, *width*, _pad_)
* *value*.LeftJustify(_width_)
* *value*.LeftJustify(_width_, _pad_)

If the *value* to be centered is `None`, it is treated as an empty string.
The *width* argument is interpreted as a numeric value. If `None`, zero is assumed.
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

@builtin("RightJustify")
def poly_rjust(x: Any=None, width: int=0, fillchar: str=' ') -> Any:
    """
**Create a string of the given width with contents right aligned**

* RightJustify(*value*, *width*)
* RightJustify(*value*, *width*, _pad_)
* *value*.RightJustify(_width_)
* *value*.RightJustify(_width_, _pad_)

If the *value* to be centered is `None`, it is treated as an empty string.
The *width* argument is interpreted as a numeric value. If `None`, zero is assumed.
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

@builtin("ZeroFill")
def poly_zero_fill(x: Any=None, width: int=0) -> Any:
    """
**Create a string of the given width with contents right aligned, padded with zeroes**

* ZeroFill(*value*, *width*)
* *value*.ZeroFill(_width_)

If the *value* to be centered is `None`, it is treated as an empty string.
The *width* argument is interpreted as a numeric value. If `None`, zero is assumed.

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

@builtin("ShortenStr")
def poly_shorten(x: str=None, length: int=32, placeholder: str="\u2026") -> str:
    """
**Shorten a string's length, optionally adding a placeholder**

* ShortenStr(*value*, *length*)
* ShortenStr(*value*, *length*, *placeholder*)
* *value*.ShortenStr(*length*)
* *value*.ShortenStr(*length*, *placeholder*)

If the *value* is `None`, it is treated as an empty string.
The *length* argument is interpreted as a numeric value. If `None`, 32 is assumed.
The default *placeholder* is an ellipses, and is added when the string
is truncated. A value of `None` omits the placeholder.

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
    if isinstance(x, list): return list(poly_shorten(x1, length, placeholder) for x1 in x)
    x = str(x) if isinstance(x, dict) else _as_str(x)
    # No adjustment required
    if len(x) <= length: return x
    # No placeholder, so simple truncation
    if not placeholder:  return x[:length]
    pl_len = len(placeholder)
    # If the placeholder overflows the length
    if pl_len >= length: return placeholder[:length]
    # Truncate to length, adjusting for the addition of the placeholder
    return x[:length - pl_len] + placeholder

#---------------------------------------------

@builtin("AppendStr")
def poly_append(*args) -> Any:
    """
**Concatenate strings**

* AppendStr(*value*)
* AppendStr(*value*, *arg*&hellip;)
* *value*.AppendStr()
* *value*.AppendStr(*arg*&hellip;)

The argument values are concatenated to end of *value*.

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
    if not args: return None
    return reduce(_append, args[1:], args[0])

@builtin("PrependStr")
def poly_prepend(*args) -> Any:
    """
**Concatenate string placing values at the beginning of the string**

* PrependStr(*value*)
* PrependStr(*value*, *arg*&hellip;)
* *value*.PrependStr()
* *value*.PrependStr(*arg*&hellip;)

The argument values are concatenated to end of*value*.

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
    if not args: return None
    return reduce(_prepend, args[1:], args[0])

@builtin("ReplaceStr")
def poly_replace(*args) -> Any:
    """
**Replace or delete values in a string**

* ReplaceStr(*value*)
* ReplaceStr(*value*, *old*)
* ReplaceStr(*value*, *old*, *new*)
* ReplaceStr(*value*, *old*&hellip;, *new*)
* *value*.ReplaceStr()
* *value*.ReplaceStr(*old*)
* *value*.ReplaceStr(*old*, *new*)
* *value*.ReplaceStr(*old*&hellip;, *new*)

String conversion is performed on *value*, *old*, and *new* as
required. The value for *old* may be a compiled regular expression.

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
    if not args: return None
    x, *args = args
    if not args: return x
    if len(args) == 1: return _replace(x, args[0]) # old, default new
    if len(args) == 2: return _replace(x, args[0], args[1]) # old and new
    return _replace(x, args[:-1], args[-1]) # old is a list, single new

def _append(x: Any, y: Any) -> Any:
    if y is None: return x
    if isinstance(x, list): return list(_append(x1, y) for x1 in x)
    if isinstance(x, dict): return  {key: _append(value, y) for key, value in x.items()}
    if x is None: x = ''
    x = _as_str(x)
    if isinstance(x, str):
        if isinstance(y, list): return reduce(_append, y, x)
        if isinstance(y, (bool, int, float)): return x + str(y)
        if isinstance(y, str): return x + y
    raise TypeError(f'Concatenation between {poly_type(x)!r} and {poly_type(y)!r} not supported')

def _prepend(x: Any, y: Any) -> Any:
    if y is None: return x
    if isinstance(x, list): return list(_prepend(x1, y) for x1 in x)
    if isinstance(x, dict): return  {key: _prepend(value, y) for key, value in x.items()}
    if x is None: x = ''
    x = _as_str(x)
    if isinstance(x, str):
        if isinstance(y, list): return reduce(_prepend, y, x)
        if isinstance(y, (bool, int, float)): return str(y) + x
        if isinstance(y, str): return y + x
    raise TypeError(f'Concatenation between {poly_type(x)!r} and {poly_type(y)!r} not supported')

def _replace(x: Any, old: Any, new: Any=None) -> Any:
    if isinstance(old, Pattern): return poly_regex_replace(x, old, new)
    if old is None: return x
    if x is None: x = ''
    x = _as_str(x)
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
    if isinstance(old, list): return reduce(lambda x, old1: _replace(x, old1, new), old, x)
    old = str(old) if isinstance(old, (bool, int, float)) else str_arg(old, 'Old', False) or ''
    if isinstance(x, str): return x.replace(old, new)
    if isinstance(x, list): return list(_replace(x1, old, new) for x1 in x)
    if isinstance(x, dict): return {key: _replace(value, old, new) for key, value in x.items()}
    raise TypeError(f'Replacement of {poly_type(x)!r} not supported')

def _as_str(value: Any) -> Any:
    if isinstance(value, (bool, int, float)): value = str(value)
    if isinstance(value, Pattern): value = value.pattern
    return value
