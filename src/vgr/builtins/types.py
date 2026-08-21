"""
Functions to check or change types
"""

from typing import Any
import json
import math
import re

from ..vgr_callable import VgrCallable

from .common import (
    bound_ops,
    str_to_bool,
    str_to_number,
)
from .registry import builtin

@builtin("IsNone")
def poly_is_none(x: Any=None) -> Any:
    """
**Is a value equal to `None`**

* IsNone(*value*)
* *value*.IsNone()

```vgr
None.IsNone() → True
"anything".IsNone() → False
```
Also see `IsNotNone()`
"""
    return x is None

@builtin("IsNotNone")
def poly_not_none(x: Any=None) -> Any:
    """
**Is a value anything but `None`**

* IsNotNone(*value*)
* *value*.IsNotNone()

```vgr
None.IsNotNone() → False
"anything".IsNotNone() → True
```

Also see `IsNone()`
"""
    return x is not None

@builtin("ToBoolean")
def poly_to_boolean(x: Any=None) -> Any:
    """
**Converts the value to a boolean**

* ToBoolean(*value*)
* *value*.ToBoolean()

If *value* is `None` then `False` is returned.
Numbers that are zero return `False` while all others return `True`.

When converting strings to booleans, comparisons are made
independent of case after leading and trailing
whitespace is removed.

* 'true', 'yes', or 'on' return `True`
* 'false', 'no', or 'off' return `False`
* If none of the above, it is converted to a number, then a boolean.

If it is a non-convertable type then `True` is returned, as any
non-`None` value is consider `True`.

Conversion is distributed over lists.

```vgr
**TODO**
```

"""
    if x is None: return False
    if poly_is_boolean(x): return x
    if poly_is_number(x): return bool(x)
    if poly_is_string(x):
        try:
            return str_to_bool(x)
        except ValueError:
            # Not, null, and not empty, so Python truthy
            return True
    if isinstance(x, list):
        return list(poly_to_boolean(x1) for x1 in x)
    return True

@builtin("IsBoolean")
def poly_is_boolean(x: Any=None) -> bool:
    """
**Is the value value a boolean**

* IsBoolean(*value*)
* *value*.IsBoolean()

```vgr
None.IsBoolean() → False
Zero.IsBoolean() → False
True.IsBoolean() → True
```

Also see `Type()`, `IsInteger()`, `IsFloat()`, `IsNumber()`, and `IsString()`
"""
    return isinstance(x, bool)

# Unique sentinel object
_SENTINEL = object()

@builtin("ToFloat")
def poly_to_float(x: Any=None, default: Any=_SENTINEL) -> Any:
    """
**Converts the value to a floating point number**

* ToFloat(*value*)
* ToFloat(*value*, *default*)
* *value*.ToFloat()
* *value*.ToFloat(*default*)

If *value* is `None` or is a non-convertable type then `None` is returned.
Strings that cannot be converted may result in a value error.
The optional *default* value is returned if the value cannot be converted
to a number. It can be any value, including `None`.

```vgr
**TODO**
```
"""
    if isinstance(x, (bool, int, float)): return float(x)
    if poly_is_string(x):
        try:
            return float(str_to_number(x))
        except ValueError as e:
            if default is _SENTINEL: raise e
            return default
    if isinstance(x, list): return list(poly_to_float(x1, default) for x1 in x)
    return None if default is _SENTINEL else default

@builtin("IsFloat")
def poly_is_float(x: Any=None) -> bool:
    """
**Is a value a floating point number**

* IsFloat(*value*)
* *value*.IsFloat()

```vgr
None.IsFloat() → False
Zero.IsFloat() → False
1.0.IsFloat() → True
Inf.IsFloat() → True
```

Also see `Type()`, `IsBoolean()`, `IsInteger()`, `IsNumber()`, and `IsString()`
"""
    return isinstance(x, float)

@builtin("ToInteger")
def poly_to_integer(x: Any=None, default: Any = _SENTINEL) -> Any:
    """
**Converts the value to an integer**

* ToInteger(*value*)
* ToInteger(*value*, *default*)
* *value*.ToInteger()
* *value*.ToInteger(*default*)

If *value* is `None` or is a non-convertable type then `None` is returned.
Strings that cannot be converted may result in a value error.
The optional *default* value is returned if the value cannot be converted
to a number. It can be any value, including `None`.

```vgr
**TODO**
```
"""
    if isinstance(x, (bool, int, float)): return int(x)
    if poly_is_string(x):
        try:
            return int(str_to_number(x))
        except ValueError as e:
            if default is _SENTINEL: raise e
            return default
    if isinstance(x, list): return list(poly_to_integer(x1, default) for x1 in x)
    return None if default is _SENTINEL else default

@builtin("IsInteger")
def poly_is_integer(x: Any=None) -> bool:
    """
**Is a value an integer**

* IsInteger(*value*)
* *value*.IsInteger()

```vgr
None.IsInteger() → False
Zero.IsInteger() → True
1.0.IsInteger() → False
Inf.IsInteger() → False
```

Also see `Type()`, `IsBoolean()`, `IsFloat()`, `IsNumber()`, and `IsString()`
"""
    return isinstance(x, int)

@builtin("ToNumber")
def poly_to_number(x: Any=None, default: Any = _SENTINEL) -> Any:
    """
**Converts the value to a number, which may be an integer or floating point number**

* ToNumber(*value*)
* ToNumber(*value*, *default*)
* *value*.ToNumber()
* *value*.ToNumber(*default*)

If *value* is `None` or is a non-convertable type then `None` is returned.
Strings that cannot be converted may result in a value error.
The optional *default* value is returned if the value cannot be converted
to a number. It can be any value, including `None`.

```vgr
**TODO**
```

Also see `ToInteger()` and `ToFloat()`
"""
    if isinstance(x, bool): return int(x)
    if isinstance(x, (int, float)): return x
    if poly_is_string(x):
        try:
            return str_to_number(x)
        except ValueError as e:
            if default is _SENTINEL: raise e
            return default
    if isinstance(x, list): return list(poly_to_number(x1, default) for x1 in x)
    return None if default is _SENTINEL else default

@builtin("IsNumber")
def poly_is_number(x: Any=None) -> bool:
    """
**Is a value a number**

* IsNumber(*value*)
* *value*.IsNumber()

Only _float_ and _int_ items are considered numbers, although booleans
can be converted to numbers.

```vgr
None.IsNumber() → False
Zero.IsNumber() → True
1.0.IsNumber() → True
"1.0".IsNumber() → False
Inf.IsNumber() → True
```

Also see `Type()`, `IsBoolean()`, `IsInteger()`, `IsFloat()`, and `IsString()`
"""
    return not isinstance(x, bool) and isinstance(x, (int, float))

@builtin("Sign")
def poly_sign(x: Any=None) -> Any:
    """
**Return an integer value indicating the sign of a number**

* Sign(*value*)
* *value*.Sign()

If *value* is greater than zero, _1_ is returned.
If less than zero, _-1_ is returned. Zero is returned for zero.
Distributed across lists, and strings are converted to numbers.
For all other types, `None` is returned.

```vgr
**TODO**
```
"""
    if isinstance(x, list): return list(poly_sign(x1) for x1 in x)
    if isinstance(x, str): x = str_to_number(x)
    return (x > 0) - (x < 0) if isinstance(x, (int, float)) else None

@builtin("IsInf")
def poly_is_inf(x: Any=None) -> bool:
    """
**Is a value equal to infinity**

* IsInf(*value*)
* *value*.IsInf()

```vgr
None.IsInf() → False
Zero.IsInf() → False
Inf.IsInf() → True
math.neg_inf.IsInf() → True
```
"""
    return math.isinf(x) if isinstance(x, (int, float)) else False

@builtin("IsFinite")
def poly_is_finite(x: Any=None) -> bool:
    """
**Is the value a number that is not infinite**

* IsFinite(*value*)
* *value*.IsFinite()

```vgr
None.IsFinite() → False
Inf.IsFinite() → False
" 0 ".IsFinite() → False
0.IsFinite() → True
1.0.IsFinite() → True
True.IsFinite() → True
False.IsFinite() → True
```
"""
    return math.isfinite(x) if isinstance(x, (int, float)) else False

@builtin("IsNan")
def poly_is_nan(x: Any=None) -> bool:
    """
**Is a value the special _not a number_ constant**

* IsNan(*value*)
* *value*.IsNan()

```vgr
None.IsNan() → False
Nan.IsNan() → True
" 0 ".IsNan() → False
0.IsNan() → False
True.IsNan() → False
```

"""
    return math.isnan(x) if isinstance(x, float) else False

@builtin("IsZero")
def poly_is_zero(x: Any=None) -> bool:
    """
**Is the value equal to zero**

* IsZero(*value*)
* *value*.IsZero()

```vgr
None.IsZero() → False
"".IsZero() → False
Space.IsZero() → False
" 0 ".IsZero() → True
0.IsZero() → True
0.0.IsZero() → True
Zero.IsZero() → True
True.IsZero() → False
False.IsZero() → True
```
"""
    if isinstance(x, str):
        try:
            x = str_to_number(x)
        except ValueError:
            return False
    return x == 0 if isinstance(x, (int, float)) else False

@builtin("ToString")
def poly_to_string(x: Any=None) -> Any:
    """
**Converts the value to its string representation**

* ToString(*value*)
* *value*.ToString()

If *value* is `None` it is left as `None`.

```vgr
**TODO**
```

> **Note**\\
> With a list, `ToString()` works distributively, applying the
> operation to each item in the list in turn. To turn the
> list into a single string, consider using `FormatJSON()`.

"""
    if x is None: return None
    if isinstance(x, bytes): return x.decode('utf-8')
    if isinstance(x, str): return x
    if isinstance(x, re.Pattern): return x.pattern
    if isinstance(x, list): return list(poly_to_string(x1) for x1 in x)
    if isinstance(x, dict): return json.dumps(x, allow_nan=True, default=str)
    return str(x)

@builtin("IsString")
def poly_is_string(x: Any=None) -> bool:
    """
**Is the value a string**

* IsString(*value*)
* *value*.IsString()

```vgr
None.IsString() → False
"".IsString() → True
Space.IsString() → True
"frog".IsString() → True
0.IsString() → False
True.IsString() → False
```

Also see `Type()` and `IsNumber()`
"""
    return isinstance(x, str)

@bound_ops("Is Empty")
@builtin("IsEmpty")
def poly_is_empty(x: Any=None) -> bool:
    """
**Test a value to see if it is empty**

* *value* Is Empty
* IsEmpty(*value*)
* *value*.IsEmpty()

A value is considered empty if:

* It is `None`
* It is a list that has no items
* It is a dictionary that has no attributes
* It is a string that has zero length or
  consists of only space characters
* It is a number that is zero
* It is the boolean `False`

```vgr
None.IsEmpty() → True
[].IsEmpty() → True
[""].IsEmpty() → False
{}.IsEmpty() → True
{"a": 1}.IsEmpty() → False
"".IsEmpty() → True
Space.IsEmpty() → True
"frog".IsEmpty() → False
0.IsEmpty() → True
1.IsEmpty() → False
True.IsEmpty() → False
False.IsEmpty() → True
```

Also see `IsNotEmpty()`
"""
    if isinstance(x, (list, dict)): return len(x) == 0
    if isinstance(x, str): return len(x) == 0 or x.isspace()
    if isinstance(x, (int, float)): return x == 0
    return x is None

@bound_ops("Is Not Empty")
@builtin("IsNotEmpty")
def poly_not_empty(x: Any=None) -> bool:
    """
**Test a value to see if it is *not* empty**

* *value* Is Not Empty
* IsNotEmpty(*value*)
* *value*.IsNotEmpty()

A value is considered empty if:

* It is a list that has one or more items
* It is a dictionary that has one or more attributes
* It is a string that consists of more than just space characters
* It is a number that is not zero
* It is the boolean `True`

```vgr
None.IsNotEmpty() → False
[].IsNotEmpty() → False
[""].IsNotEmpty() → True
{}.IsNotEmpty() → False
{"a": 1}.IsNotEmpty() → True
"".IsNotEmpty() → False
Space.IsNotEmpty() → False
"frog".IsNotEmpty() → True
0.IsNotEmpty() → False
1.IsNotEmpty() → True
True.IsNotEmpty() → True
False.IsNotEmpty() → False
```

Also see `IsEmpty()`
"""
    if isinstance(x, (list, dict)): return len(x) > 0
    if isinstance(x, str): return len(x) > 0 and not x.isspace()
    if isinstance(x, (int, float)): return bool(x)
    return x is not None

@builtin("DefaultTo")
def default_to(value: Any=None, *args) -> Any:
    """
**Returns the default if a value is `None`**

* DefaultTo(*value*, *default*&hellip;)
* *value*.DefaultTo(*default**&hellip;)

When *value* is `None` a value is choosen from those provided.
If multiple default values are provided, the first non-`None` one
is returned. If all default values are `None` then `None` is returned.

```vgr
DefaultTo() → None
None.DefaultTo() → None
None.DefaultTo(None) → None
5.DefaultTo(6) → 5
None.DefaultTo(6) → 6
```

```vgr
Constant phone = {
    "home": None,
    "work": None,
    "cell": "909-867-5309"
}

phone.home.DefaultTo(phone.work, phone.cell) → "909-867-5309"
```
"""
    if value is None:
        for arg in args:
            if arg is not None: return arg
    return value

@builtin("IsFunction")
def poly_is_function(obj: Any=None) -> Any:
    """
**Is a value a function**

* IsFunction(*value*)
* *value*.IsFunction()

```vgr
None.IsFunction() → False
Function f(x) -> x+1
f.IsFunction() → True
```
"""
    return isinstance(obj, VgrCallable)
