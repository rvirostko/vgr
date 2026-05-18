"""
Modulo operation.
"""

from functools import reduce
from math import nan
from re import Pattern
from typing import Any

from .common import (
    bound_ops,
    empty_is_zero,
    get_operation,
    numeric_operations,
    str_to_number,
)
from .type import poly_type

@bound_ops("%")
def poly_mod(*args):
    """
**Modulo operation**

* *x* % *y*
* Mod(*x*, *y*&hellip;)
* *x*.Mod(*y*&hellip;)

| Type(x) | Type(y) | Returns | Operation               |
|---------|---------|---------|-------------------------|
| integer | integer | float   | x % y                   |
| integer | float   | float   | x % y                   |
| integer | string  | float   | x % ToFloat(y)          |
| float   | integer | float   | x % y                   |
| float   | float   | float   | x % y                   |
| float   | string  | float   | x % ToFloat(y)          |
| string  | integer | float   | ToFloat(x) % y          |
| string  | float   | float   | ToFloat(x) % y          |
| string  | string  | float   | ToFloat(x) % ToFloat(y) |
| list    | integer | list    | Distributed             |
| list    | float   | list    | Distributed             |
| list    | string  | list    | Distributed             |

A type error is raised on all other combinations

```vgr
None % None → None
None % 5 → 0
None % "5" → 0
5 % 2 → 1
5 % "2" → 1
"5" % 2 → 1
[5, 7] % 3 → [2, 1]
```
"""
    return reduce(_mod, args[1:], args[0]) if args else None

def _mod(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, _mod_operations, numeric_operations)
    try:
        return operation(_mod, x, y) if operation else x % y
    except TypeError as e:
        raise TypeError(f"Cannot perform modulo on type {poly_type(x)!r} with {poly_type(y)!r}") from e
    except ZeroDivisionError:
        return nan

_mod_operations = {
    (str, str): lambda op, x, y: op(empty_is_zero(x), empty_is_zero(y)),
}

@bound_ops('Is Even', 'Is Not Odd')
def poly_is_even(x: Any) -> bool:
    """
**Is the value an even integral value**

* *value* Is Even
* *value* Is Not Odd
* IsEven(*value*)
* *value*.IsEven()

Strings are converted to numbers.
Only integral values can be even numbers.

```vgr
For-Each v In [ None, List(), Dictionary(), -1, Zero, 1.5, 2 ]
    Choose Using v
        When Is Even  Print v.Repr(), "is even"
        When Is Odd   Print v.Repr(), "is odd"
        Otherwise     Print v.Repr(), "is neither odd nor even"
    End-Choose
End-For

None is neither odd nor even
[] is neither odd nor even
{} is neither odd nor even
-1 is odd
0 is even
1.5 is neither odd nor even
2 is even
```

Also see `Is Odd` and `Mod()`
"""
    return _check_remainder(x, 0)

@bound_ops('Is Odd', 'Is Not Even')
def poly_is_odd(x: Any) -> bool:
    """
**Is the value an odd integral value**

* *value* Is Odd
* *value* Is Not Even
* IsOdd(*value*)
* *value*.IsOdd()

Strings are converted to numbers.
Only integral values can be odd numbers.

```vgr
For-Each v In [ None, List(), Dictionary(), -1, Zero, 1.5, 2 ]
    Choose Using v
        When Is Even  Print v.Repr(), "is even"
        When Is Odd   Print v.Repr(), "is odd"
        Otherwise     Print v.Repr(), "is neither odd nor even"
    End-Choose
End-For

None is neither odd nor even
[] is neither odd nor even
{} is neither odd nor even
-1 is odd
0 is even
1.5 is neither odd nor even
2 is even
```

Also see `Is Even` and `Mod()`
"""
    return _check_remainder(x, 1)

_NUMERIC_TYPES = (bool, int, float, str)
def _check_remainder(x: Any, remainder: int) -> bool:
    if not isinstance(x, _NUMERIC_TYPES): return False
    if isinstance(x, Pattern): x = x.pattern
    if isinstance(x, str):
        try:
            x = str_to_number(x)
        except ValueError:
            return False
    return x % 2 == remainder if isinstance(x, int) or (isinstance(x, float) and x.is_integer()) else False
