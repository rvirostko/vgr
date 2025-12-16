"""
Functions to check or change types
"""

from typing import Any
import json
import math
import re

from .common import str_to_number, str_to_bool

def poly_bool(x: Any) -> Any:
    """
**Converts the value to a boolean**

* ToBool(_value_)
* _value_.ToBool()

If _value_ is _None_ then _False_ is returned.
Numbers that are zero return _False_ while all others return _True_.

When converting strings to booleans, comparisons are made
independent of case after leading and trailing
whitespace is removed.

* 'true', 't', 'yes', 'y', or 'on' return _True_
* 'false', 'f', 'no', 'n' or 'off' return _False_
* If none of the above, it is converted to a number, then a bool.

If it is a non-convertable type then _True_ is returned, as any
non-_None_ value is consider _True_.

Conversion is distributed over lists.

```vgr
**TODO**
```

"""
    if x is None: return False
    if poly_isbool(x): return x
    if poly_isnumber(x): return bool(x)
    if poly_isstr(x):
        try:
            return str_to_bool(x)
        except ValueError:
            # Not, null, and not empty, so Python truthy
            return True
    if isinstance(x, (list, tuple)):
        return list(poly_bool(x1) for x1 in x)
    return True

def poly_isbool(x: Any) -> bool:
    """
**Returns _True_ if the value is a boolean**

* IsBool(_value_)
* _value_.IsBool()

```vgr
**TODO**
```

Also see `Type()`, `IsInt()`, `IsFloat()`, `IsNumber()`, and `IsString()`
"""
    return isinstance(x, bool)

# Unique sentinel object
_SENTINEL = object()

def poly_float(x: Any, default: Any = _SENTINEL) -> Any:
    """
**Converts the value to a floating point number**

* ToFloat(_value_)
* ToFloat(_value_, _default_)
* _value_.ToFloat()
* _value_.ToFloat(_default_)

If _value_ is _None_ or is a non-convertable type then _None_ is returned.
Strings that cannot be converted may result in a value error.
The optional _default_ value is returned if the value cannot be converted
to a number. It can be any value, including _None_.

```vgr
**TODO**
```
"""
    if poly_isnumber(x): return float(x)
    if poly_isstr(x):
        try:
            return float(str_to_number(x))
        except ValueError as e:
            if default is _SENTINEL: raise e
            return default
    if isinstance(x, (list, tuple)): return list(poly_float(x1, default) for x1 in x)
    return None if default is _SENTINEL else default

def poly_isfloat(x: Any) -> bool:
    """
**Returns _True_ if the value is a floating point number**

* IsFloat(_value_)
* _value_.IsFloat()

```vgr
**TODO**
```

Also see `Type()`, `IsBool()`, `IsInt()`, `IsNumber()`, and `IsString()`
"""
    return isinstance(x, float)

def poly_int(x: Any, default: Any = _SENTINEL) -> Any:
    """
**Converts the value to an integer**

* ToInt(_value_)
* ToInt(_value_, _default_)
* _value_.ToInt()
* _value_.ToInt(_default_)

If _value_ is _None_ or is a non-convertable type then _None_ is returned.
Strings that cannot be converted may result in a value error.
The optional _default_ value is returned if the value cannot be converted
to a number. It can be any value, including _None_.

```vgr
**TODO**
```
"""
    if poly_isnumber(x): return int(x)
    if poly_isstr(x):
        try:
            return int(str_to_number(x))
        except ValueError as e:
            if default is _SENTINEL: raise e
            return default
    if isinstance(x, (list, tuple)): return list(poly_int(x1, default) for x1 in x)
    return None if default is _SENTINEL else default

def poly_isint(x: Any) -> bool:
    """
**Returns _True_ if the value is an integer**

* IsInt(_value_)
* _value_.IsInt()

```vgr
**TODO**
```

Also see `Type()`, `IsBool()`, `IsFloat()`, `IsNumber()`, and `IsString()`
"""
    return isinstance(x, int)

def poly_number(x: Any, default: Any = _SENTINEL) -> Any:
    """
**Converts the value to a number, which may be an integer or floating point number**

* ToNumber(_value_)
* ToNumber(_value_, _default_)
* _value_.ToNumber()
* _value_.ToNumber(_default_)

If _value_ is _None_ or is a non-convertable type then _None_ is returned.
Strings that cannot be converted may result in a value error.
The optional _default_ value is returned if the value cannot be converted
to a number. It can be any value, including _None_.

```vgr
**TODO**
```

Also see `ToInt()` and `ToFloat()`
"""
    if poly_isnumber(x): return x
    if poly_isstr(x):
        try:
            return str_to_number(x)
        except ValueError as e:
            if default is _SENTINEL: raise e
            return default
    if isinstance(x, (list, tuple)): return list(poly_number(x1, default) for x1 in x)
    return None if default is _SENTINEL else default

def poly_isnumber(x: Any) -> bool:
    """
**Returns _True_ if the value is a number**

* IsNumber(_value_)
* _value_.IsNumber()

Only _float_ and _int_ items are considered numbers.

```vgr
**TODO**
```

Also see `Type()`, `IsBool()`, `IsInt()`, `IsFloat()`, and `IsString()`
"""
    return isinstance(x, (int, float))

def poly_sign(x: Any) -> Any:
    """
**Return an integer value indicating the sign of a number**

* Sign(_value_)
* _value_.Sign()

If _value_ is greater than zero, _1_ is returned.
If less than zero, _-1_ is returned. Zero is returned for zero.
Distributed across lists, and strings are converted to numbers.
For all other types, _None_ is returned.

```vgr
**TODO**
```
"""
    if isinstance(x, (list, tuple)): return list(poly_sign(x1) for x1 in x)
    if isinstance(x, str): x = str_to_number(x)
    return (x > 0) - (x < 0) if isinstance(x, (int, float)) else None

def poly_isinf(x: Any) -> bool:
    """
**Returns _True_ if the value is infinity**

* IsInf(_value_)
* _value_.IsInf()

```vgr
**TODO**
```
"""
    return math.isinf(x) if isinstance(x, (int, float)) else False

def poly_isfinite(x: Any) -> bool:
    """
**Returns _True_ if the value is finite**

* IsFinite(_value_)
* _value_.IsFinite()

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

def poly_isnan(x: Any) -> bool:
    """
**Returns _True_ if the value is the special _not a number_ constant**

* IsNan(_value_)
* _value_.IsNan()

```vgr
None.IsNan() → False
Nan.IsNan() → True
" 0 ".IsNan() → False
0.IsNan() → False
True.IsNan() → False
```

"""
    return math.isnan(x) if isinstance(x, (int, float)) else False

def poly_iszero(x: Any) -> bool:
    """
**Returns _True_ if the value is zero**

* IsZero(_value_)
* _value_.IsZero()

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

def poly_str(x: Any) -> Any:
    """
**Converts the value to its string representation**

* ToString(_value_)
* _value_.ToString()

If _value_ is _None_ it is left as _None_, not converted to the string _"None"_.

```vgr
**TODO**
```
"""
    if x is None: return None
    if isinstance(x, bytes): return x.decode('utf-8')
    if isinstance(x, str): return x
    if isinstance(x, re.Pattern): return x.pattern
    if isinstance(x, (list, tuple)): return list(poly_str(x1) for x1 in x)
    if isinstance(x, dict): return json.dumps(x, default=str)
    return str(x)

def poly_isstr(x: Any) -> bool:
    """
**Returns _True_ if the value is a string**

* IsString(_value_)
* _value_.IsString()

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

def poly_isempty(x: Any) -> bool:
    """
**Test a value to see if it is _empty_**

* IsEmpty(_value_)
* _value_.IsEmpty()

A value is considered empty if:
* It is _None_
* It is a list that has no items
* It is a dictionary that has attributes
* It is a string that has zero length or
  consists of only space characters
* It is a number that is zero
* It is the boolean _False_

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
    if isinstance(x, (list, tuple, dict)): return len(x) == 0
    if isinstance(x, str): return len(x) == 0 or x.isspace()
    if isinstance(x, (int, float)): return x == 0
    return x is None

def poly_notempty(x: Any) -> bool:
    """
**Test a value to see if it is _not empty_**

* NotEmpty(_value_)
* _value_.NotEmpty()

A value is considered empty if:
* It is a list that has one or more items
* It is a dictionary that has one or more attributes
* It is a string that consists of more than just space characters
* It is a number that is not zero
* It is the boolean _True_

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
    if isinstance(x, (list, tuple, dict)): return len(x) > 0
    if isinstance(x, str): return len(x) > 0 and not x.isspace()
    if isinstance(x, (int, float)): return bool(x)
    return x is not None
