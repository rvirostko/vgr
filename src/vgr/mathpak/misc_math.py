"""Arithmetic functions"""

from typing import Any, Callable
import math

from .common import bound_ops, str_to_number, type_str, dist_x

def poly_abs(x: Any) -> Any:
    """
**Return the absolute value of a value**

* Abs(_value_)
* _value_.Abs()

Strings will be converted to numbers.
Distributed over lists.
Idempotent for None and dictionaries.

```vgr
None.Abs() → None
5.Abs() → 5
"-5".Abs() → 5
[7.0, -3, " -2.75 "].Abs() → [7.0, 3, 2.75]
{"a": 5}.Abs() → {"a": 5}
```
"""
    if x is None: return None
    if isinstance(x, str): return poly_abs(str_to_number(x))
    return abs(x) if hasattr(x, '__abs__') else _dist(poly_abs, x)

# First item is just for display purposes
@bound_ops("⌈...⌉")
def poly_ceil(x: Any) -> Any:
    """
**Returns the least integer greater than or equal to a value**

* Ceil(_value_)
* _value_.Ceil()
* ⌈ _value_ ⌉

Strings will be converted to numbers.
Distributed over lists.
Idempotent for None and dictionaries.

```vgr
None.Ceil() → None
5.1.Ceil() → 6
"-5.1".Ceil() → -5
[7.0, -3, " -2.75 "].Ceil() → [7, -3, -2]
{"a": 5}.Ceil() → {"a": 5}
```
Also see `Floor()` and `Trunc()`
"""
    if x is None: return None
    if isinstance(x, str): return poly_ceil(str_to_number(x))
    return math.ceil(x) if hasattr(x, '__ceil__') else _dist(poly_ceil, x)

def poly_trunc(x: Any) -> Any:
    """
**Truncates a value to the lowest integer towards zero**

* Trunc(_value_)
* _value_.Trunc()

```vgr
None.Trunc() → None
5.1.Trunc() → 5
"-5.1".Trunc() → -5
[7.0, -3, " -2.75 "].Trunc() → [7, -3, -2]
{"a": 5}.Trunc() → {"a": 5}
```

Also see `Ceil()` and `Floor()`
"""
    if x is None: return None
    if isinstance(x, str): return poly_trunc(str_to_number(x))
    return math.trunc(x) if hasattr(x, '__trunc__') else _dist(poly_trunc, x)

# First item is just for display purposes
@bound_ops("⌊...⌋")
def poly_floor(x: Any) -> Any:
    """
**Returns the least integer less than or equal to a value**

* Floor(_value_)
* _value_.Floor()
* ⌊ _value_ ⌋

Strings will be converted to numbers.
Distributed over lists.
Idempotent for None and dictionaries.

```vgr
None.Floor() → None
5.1.Floor() → 5
"-5.1".Floor() → -6
[7.0, -3, " -2.75 "].Floor() → [7, -3, -3]
{"a": 5}.Floor() → {"a": 5}
```

Also see `Ceil()` and `Trunc()`
"""

    if x is None: return None
    if isinstance(x, str): return poly_floor(str_to_number(x))
    return math.floor(x) if hasattr(x, '__floor__') else _dist(poly_floor, x)

def arithmetic_round(n: float, ndigits: int = 0) -> float:
    """Python's round() uses banker's rounding, so this can be used instead"""
    p = 10 ** ndigits
    return int(n * p + 0.5 if n >= 0 else n * p - 0.5) / p

def poly_round(x: Any, ndigits: int=0) -> Any:
    """
**Arithmetic rounding of a number to a given number of decimal places or power of ten**

* Round(_value_)
* Round(_value_, _ndigits_)

* Round(_value_)
* Round(_value_, _ndigits_)

If _ndigits_ is not provide _value_ is rounded to a whole number.
Positive values of _ndigits_ rounds to a number of decimal places.
Negative values round to a power of ten.

Strings will be converted to numbers.
Distributed over lists.
Idempotent for None and dictionaries.

```vgr
None.Round() → None
5.1.Round() → 5.0
"-5.1".Round() → -5.0
[7.0, -3, " -2.75 "].Round() → [7.0, -3.0, -3.0]
{"a": 5}.Round() → {"a": 5}
5.125.Round(2) → 5.13
94.5.Round(0) → 95.0
94.5.Round(1) → 94.5
94.5.Round(-1) → 90.0
94.5.Round(-2) → 100.0
```

Also see `RoundMultiple()`
"""
    if x is None: return None
    if isinstance(x, str): x = str_to_number(x)
    if isinstance(ndigits, (int, float)):
        ndigits = int(ndigits)
    else:
        if isinstance(ndigits, str): return poly_round(x, str_to_number(ndigits))
        raise TypeError(f'Unsupported type for NDigits: {type_str(ndigits)}')
    if isinstance(x, (int, float)): return arithmetic_round(x, ndigits)
    if hasattr(x, '__round__'): return round(x, ndigits)
    if isinstance(x, (list, tuple)): return dist_x(poly_round, x, ndigits)
    return x

def _get_multiple_arg(multiple: Any) -> Any:
    if not isinstance(multiple, (int, float)):
        if isinstance(multiple, str):
            multiple = str_to_number(multiple)
        else:
            raise TypeError(f'Unsupported type for multiple: {type_str(multiple)}')
    multiple = abs(multiple)
    return 1 if multiple == 0 else multiple

def poly_round_multiple(x: Any, multiple: Any=1) -> Any:
    """
**Arithmetic rounding of a number using a _multiple_ value to align the result**

* RoundMultiple(_value_)
* RoundMultiple(_value_, _multiple_)
* _value_.RoundMultiple()
* _value_.RoundMultiple(_multiple_)

Using _multiple_ like a modulus, an arithmetic rounding is
performed so that the result aligns with the multiple.
If not provided, _multiple_ default to 1, acting like `Round()`.

Strings will be converted to numbers.
Distributed over lists.
Idempotent for None and dictionaries.

```vgr
None.RoundMultiple() → None
5.1.RoundMultiple() → 5.0
"-5.1".RoundMultiple() → -5.0
[7.0, -3, " -2.75 "].RoundMultiple() → [7.0, -3.0, -3.0]
{"a": 5}.RoundMultiple() → {"a": 5}

5.125.RoundMultiple(0) → 5.0
5.125.RoundMultiple(1) → 5.0
5.125.RoundMultiple(2) → 6.0
5.125.RoundMultiple(4) → 4.0

// Sign of multiple ignored
94.5.RoundMultiple(-1) → 95.0
94.5.RoundMultiple(-2) → 94.0

5.125.RoundMultiple(1/2) → 5.0
5.125.RoundMultiple(1/4) → 5.25
5.125.RoundMultiple(1/8) → 5.125
```
Also see `Round()`
"""
    if x is None: return None
    multiple = _get_multiple_arg(multiple)
    if isinstance(x, str): x = str_to_number(x)
    if isinstance(x, (int, float)): return multiple * arithmetic_round(x / multiple)
    if isinstance(x, (list, tuple)): return dist_x(poly_round_multiple, x, multiple)
    return x

def poly_floor_multiple(x: Any, multiple: Any=1) -> Any:
    """
**Floor of a number using a _multiple_ value to align the result**

* FloorMultiple(_value_)
* FloorMultiple(_value_, _multiple_)
* _value_.FloorMultiple()
* _value_.FloorMultiple(_multiple_)

Using _multiple_ like a modulus, a floor operation is
performed so that the result aligns with the multiple.
If not provided, _multiple_ default to 1, acting like `Floor()`.

Strings will be converted to numbers.
Distributed over lists.
Idempotent for None and dictionaries.

```vgr
None.FloorMultiple() → None
5.1.FloorMultiple() → 5
"-5.1".FloorMultiple() → -6
[7.0, -3, " -2.75 "].FloorMultiple() → [7, -3, -3]

{"a": 5}.FloorMultiple() → {"a": 5}
5.125.FloorMultiple(0) → 5
5.125.FloorMultiple(1) → 5
5.125.FloorMultiple(2) → 4
5.125.FloorMultiple(4) → 4

// Sign of multiple ignored
94.5.FloorMultiple(-1) → 94
94.5.FloorMultiple(-2) → 94

5.125.FloorMultiple(1/2) → 5.0
5.125.FloorMultiple(1/4) → 5.0
5.125.FloorMultiple(1/8) → 5.125
```
Also see `Floor()` and `CeilMultiple()`
"""
    if x is None: return None
    multiple = _get_multiple_arg(multiple)
    if isinstance(x, str): x = str_to_number(x)
    if isinstance(x, (int, float)): return multiple * math.floor(x / multiple)
    if isinstance(x, (list, tuple)): return dist_x(poly_floor_multiple, x, multiple)
    return x

def poly_ceil_multiple(x: Any, multiple: Any=1) -> Any:
    """
**Ceil of a number using a _multiple_ value to align the result**

* CeilMultiple(_value_)
* CeilMultiple(_value_, _multiple_)
* _value_.CeilMultiple()
* _value_.CeilMultiple(_multiple_)

Using _multiple_ like a modulus, a ceil operation is
performed so that the result aligns with the multiple.
If not provided, _multiple_ default to 1, acting like `Ceil()`.

Strings will be converted to numbers.
Distributed over lists.
Idempotent for None and dictionaries.

```vgr
None.CeilMultiple() → None
5.1.CeilMultiple() → 6
"-5.1".CeilMultiple() → -5
[7.0, -3, " -2.75 "].CeilMultiple() → [7, -3, -2]
{"a": 5}.CeilMultiple() → {"a": 5}
5.125.CeilMultiple(0) → 6
5.125.CeilMultiple(1) → 6
5.125.CeilMultiple(2) → 6
5.125.CeilMultiple(4) → 8
94.5.CeilMultiple(-1) → 95
94.5.CeilMultiple(-2) → 96
5.125.CeilMultiple(1/2) → 5.5
5.125.CeilMultiple(1/4) → 5.25
5.125.CeilMultiple(1/8) → 5.125
```

Also see `Ceil()` and `FloorMultiple()`
"""
    if x is None: return None
    multiple = _get_multiple_arg(multiple)
    if isinstance(x, str): x = str_to_number(x)
    if isinstance(x, (int, float)): return multiple * math.ceil(x / multiple)
    if isinstance(x, (list, tuple)): return dist_x(poly_ceil_multiple, x, multiple)
    return x

def _dist(op: Callable[[Any], Any], x: Any) -> Any:
    if x is None: return None
    # Distribute the operation over the collection
    return type(x)(op(x1) for x1 in x) if isinstance(x, (list, tuple)) else x

def poly_pred(x: Any) -> Any:
    """
**Return the arithmetic predecessor of a value**

* Pred(_value_)
* _value_.Pred()

```vgr
None.Pred() → None
5.Pred() → 4
5.1.Pred() → 5.099999999999999
"-5.1".Pred() → -5.1000000000000005
[7.0, -3, " -2.75 "].Pred() → [6.999999999999999, -4, -2.7500000000000004]
[True, False].Pred() → [False, False]
{"a": 5}.Pred() → {"a": 5}
"IBM".Ord().Pred().Chr().Join('') → "HAL"
```

Also see `Succ()`
"""
    if x is None: return None
    if isinstance(x, str): x = str_to_number(x)
    if isinstance(x, bool): return False
    if isinstance(x, int): return x - 1
    if isinstance(x, float): return math.nextafter(x, -math.inf)
    if isinstance(x, (list, tuple)): return type(x)(poly_pred(x1) for x1 in x)
    return x

def poly_succ(x: Any) -> Any:
    """
**Return the arithmetic successor of a value**

* Succ(_value_)
* _value_.Succ()

```vgr
None.Succ() → None
5.Succ() → 6
5.1.Succ() → 5.1000000000000005
"-5.1".Succ() → -5.099999999999999
[7.0, -3, " -2.75 "].Succ() → [7.000000000000001, -2, -2.7499999999999996]
[True, False].Succ() → [True, True]
{"a": 5}.Succ() → {"a": 5}
"ohms".Ord().Succ().Chr().Join('') → "pint"
```

Also see `Pred()`
"""
    if x is None: return None
    if isinstance(x, str): x = str_to_number(x)
    if isinstance(x, bool): return True
    if isinstance(x, int): return x + 1
    if isinstance(x, float): return math.nextafter(x, math.inf)
    if isinstance(x, (list, tuple)): return type(x)(poly_succ(x1) for x1 in x)
    return x
