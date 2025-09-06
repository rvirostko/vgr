"""
Functions to check or change types
"""

from typing import Any
import json
import math

from .common import str_to_number, str_to_bool, str_to_int

def poly_bool(x: Any) -> Any:
    """
**Converts the value to a boolean**

* _value_.ToBool()
* _value_.Bool()

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
    if isinstance(x, (list, tuple)): return type(x)(poly_bool(x1) for x1 in x)
    return True

def poly_isbool(x: Any) -> bool:
    """
**Returns _True_ if the value is a boolean**

* _value_.IsBool()

"""
    return isinstance(x, bool)

def poly_float(x: Any) -> Any:
    """
**Converts the value to a floating point number**

* _value_.ToFloat()
* _value_.Float()

Strings that cannot be converted to an floating point number result in a value error.
If _value_ is _None_ or is a non-convertable type then _None_ is returned.
"""
    if poly_isnumber(x): return float(x)
    if poly_isstr(x): return str_to_number(x)
    if isinstance(x, (list, tuple)): return type(x)(poly_float(x1) for x1 in x)
    return None

def poly_isfloat(x: Any) -> bool:
    """
**Returns _True_ if the value is a floating point number**

* _value_.IsFloat()
"""
    return isinstance(x, float)

def poly_int(x: Any) -> Any:
    """
**Converts the value to an integer**

* _value_.ToInt()
* _value_.Int()

Strings that cannot be converted to an integer result in a value error.
If _value_ is _None_ or is a non-convertable type then _None_ is returned.
"""
    if poly_isnumber(x): return int(x)
    if poly_isstr(x): return str_to_int(x)
    if isinstance(x, (list, tuple)): return type(x)(poly_int(x1) for x1 in x)
    return None

def poly_isint(x: Any) -> bool:
    """
**Returns _True_ if the value is an integer**

* _value_.IsInt()
"""
    return isinstance(x, int)

def poly_number(x: Any) -> Any:
    """
**Converts the value to a number, which may be an integer or floating point number**

* _value_.ToNumber()
* _value_.Number()

Strings that cannot be converted to numbers result in a value error.
If _value_ is _None_ or is a non-convertable type then _None_ is returned.
"""
    if poly_isnumber(x): return x
    if poly_isstr(x): return str_to_number(x)
    if isinstance(x, (list, tuple)): return type(x)(poly_number(x1) for x1 in x)
    return None

def poly_isnumber(x: Any) -> bool:
    """
**Returns _True_ if the value is a number**

* _value_.IsNumber()

Only _float_ and _int_ items are considered numbers.
"""
    return isinstance(x, (int, float))

def poly_sign(x: Any) -> Any:
    """
**Return an integer value indicating the sign of a number**

* _value_.Sign()

If _value_ is greater than zero, _1_ is returned.
If less than zero, _-1_ is returned. Zero is returned for zero.
Distributed across lists, and strings are converted to numbers.
For all other types, _None_ is returned.
"""
    if isinstance(x, (list, tuple)): return type(x)(poly_sign(x1) for x1 in x)
    if isinstance(x, str): x = str_to_number(x)
    return (x > 0) - (x < 0) if isinstance(x, (int, float)) else None

def poly_isinf(x: Any) -> bool:
    """
**Returns _True_ if the value is infinity**

* _value_.IsInf()

"""
    return math.isinf(x) if isinstance(x, (int, float)) else False

def poly_isfinite(x: Any) -> bool:
    """
**Returns _True_ if the value is finite**

* _value_.IsFinite()

"""
    return math.isfinite(x) if isinstance(x, (int, float)) else False

def poly_isnan(x: Any) -> bool:
    """
**Returns _True_ if the value is the special _not a number_ constant**

* _value_.IsNan()

"""
    return math.isnan(x) if isinstance(x, (int, float)) else False

def poly_iszero(x: Any) -> bool:
    """
**Returns _True_ if the value is zero**

* _value_.IsZero()

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

* _value_.ToStr()
* _value_.Str()

If _value_ is _None_ it is left as _None_, not converted to the string _"None"_.
"""
    if x is None: return None
    if isinstance(x, bytes): return x.decode('utf-8')
    if isinstance(x, str): return x
    if isinstance(x, (list, tuple)): return type(x)(poly_str(x1) for x1 in x)
    if isinstance(x, dict): return json.dumps(x)
    return str(x)

def poly_isstr(x: Any) -> bool:
    """
**Returns _True_ if the value is a string**

* _value_.IsStr()

"""
    return isinstance(x, str)

def poly_islist(x: Any) -> bool:
    """
**Returns _True_ if the value is a list**

* _value_.IsList()

The Python _tuple_ and _list_ types are both considered lists.
"""
    return isinstance(x, (list, tuple))

def poly_list(x: Any) -> Any:
    """
**Converts a value to a list**

* _x_.ToList()
* _x_.List()

Dictionaries are converted to a list of key/value pairs.
If _value_ is _None_ an empty list is returned.
"""
    if x is None: return []
    if isinstance(x, (list, tuple)): return x
    if isinstance(x, dict): return [(key, x[key]) for key in sorted(x)]
    return [x]
