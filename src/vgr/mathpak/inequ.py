"""
Polymorphic inequality operators
"""

from typing import Any, Callable, Iterable
import math

from .common import str_to_number, bound_ops

@bound_ops("Is Equal To", "==", "⩵", "Equals", "Is")
def poly_eq(x: Any, y: Any) -> bool:
    """
**Equality comparison**

* *x* [Is] Equal To *y*
* *x* Equals *y*
* *x* Is *y*
* *x* == *y*
* *x* ⩵ *y*
* IsEqualTo(*x*, *y*)
* *x*.IsEqualTo(*y*)

| x     | y          | operation           |
|-------|------------|---------------------|
| None  | *any*      | y == None           |
| *any* | None       | False               |
| int   | int/float  | x == y              |
| int   | str        | x == ToNumber(y)†   |
| int   | list       | [x] == y‡           |
| float | int/float  | x == y              |
| float | str        | x == ToNumber(y)    |
| float | list       | [x] == y            |
| str   | int/float  | ToNumber(x) == y    |
| str   | str        | x == y              |
| str   | list       | [x] == y            |
| list  | list       | x == y              |
| list  | *any*      | x == [y]            |
| dict  | dict       | x == y by attr      |

A type error is raised on all other combinations

Dictionary comparisons do not perform any type
conversions.

† If the string value cannot be converted to a number
the corresponding non-string value is converted to
a string.

‡ After conversion to an array the comparison is
performed between corresponding elements.

```vgr
None == None → True
None == 5 → False
None == "5" → False
5 == " 5.0" → True
"5" == "5.0" → False
5 == [5] → True
[5, 7] == [5, "7"] → True
{"a": 5, "b": 7} == {"b": 7, "a": 5} → True
{"a": 5, "b": 7, "c": 11} == {"c": 13, "b": 7, "a": 5} → False
```
"""
    # None is only equal to itself
    if x is None: return y is None
    if y is None: return False
    tx = type(x)
    ty = type(y)
    # Nan is only equal to itself
    if tx == float and math.isnan(x): return ty == float and math.isnan(y)
    if ty == float and math.isnan(y): return False
    override = _overrides.get((tx, ty))
    return override(poly_eq, x, y) if override else x == y

@bound_ops("===")
def poly_exact_eq(x: Any, y: Any) -> bool:
    """
**Exact equality comparison**

* *x* === *y*

While similar to a regular equals comparison, it requires that
types of the two values match. No conversions are performed.

```vgr
5 == "5" -> True
5 === "5" -> False
```

Also see `==`
"""
    # None is only equal to itself
    if x is None: return y is None
    if y is None: return False
    tx = type(x)
    ty = type(y)
    if tx != ty: return False
    # Nan is only equal to itself, so reuse equals logic
    if tx == float and math.isnan(x): return poly_eq(x, y)
    override = _overrides.get((tx, ty))
    return override(poly_exact_eq, x, y) if override else x == y

@bound_ops("Is Not Equal To", "!=", "≠", "<>", "¬=")
def poly_ne(x: Any, y: Any) -> bool:
    """
**Not equals comparison**

* *x* Is Not *y*
* *x* [Is] Not Equal To *y*
* *x* != *y*
* *x* ≠ *y*
* *x* <> *y*
* *x* ¬= *y*
* NotEqualTo(*x*, *y*)
* *x*.NotEqualTo(*y*)

| x     | y          | operation           |
|-------|------------|---------------------|
| None  | *any*      | y != None           |
| *any* | None       | True                |
| int   | int/float  | x != y              |
| int   | str        | x != ToNumber(y)†   |
| int   | list       | [x] != y‡           |
| float | int/float  | x != y              |
| float | str        | x != ToNumber(y)    |
| float | list       | [x] != y            |
| str   | int/float  | ToNumber(x) != y    |
| str   | str        | x != y              |
| str   | list       | [x] != y            |
| list  | list       | x != y              |
| list  | *any*      | x != [y]            |
| dict  | dict       | x != y by attr      |

A type error is raised on all other combinations

Dictionary comparisons do not perform any type
conversions.

† If the string value cannot be converted to a number
the corresponding non-string value is converted to
a string.

‡ After conversion to an array the comparison is
performed between corresponding elements.

```vgr
None != None → False
None != 5 → True
None != "5" → True
5 != " 5.0" → False
"5" != "5.0" → True
5 != [5] → False
[5, 7] != [5, "7"] → False
{"a": 5, "b": 7} != {"b": 7, "a": 5} → False
{"a": 5, "b": 7, "c": 11} != {"c": 13, "b": 7, "a": 5} → True
```
"""
    return not poly_eq(x, y)

@bound_ops("Is Less Than", "<", "＜")
def poly_lt(x: Any, y: Any) -> bool:
    """
**Less than comparison**

* *x* [Is] Less Than *y*
* *x* < *y*
* *x* ＜ *y*
* IsLessThan(*x*, *y*)
* *x*.IsLessThan(*y*)

| x     | y          | operation          |
|-------|------------|--------------------|
| None  | *any*      | y != None          |
| *any* | None       | False              |
| int   | int/float  | x < y              |
| int   | str        | x < ToNumber(y)†   |
| int   | list       | [x] < y‡           |
| float | int/float  | x < y              |
| float | str        | x < ToNumber(y)    |
| float | list       | [x] < y            |
| str   | int/float  | ToNumber(x) < y    |
| str   | str        | x < y              |
| str   | list       | [x] < y            |
| list  | list       | x < y              |
| list  | *any*      | x < [y]            |

A type error is raised on all other combinations

† If the string value cannot be converted to a number
the corresponding non-string value is converted to
a string.

‡ After conversion to an array the comparison is
performed between corresponding elements.

```vgr
**TODO**
```

"""
    # None is less than everything except itself
    if x is None: return y is not None
    if y is None: return False
    override = _overrides.get((type(x), type(y)))
    return override(poly_lt, x, y) if override else x < y

@bound_ops("Is Greater Than", ">", "＞")
def poly_gt(x: Any, y: Any) -> Any:
    """
**Greater than comparison**

* *x* [Is] Greater Than *y*
* *x* > *y*
* *x* ＞ *y*
* IsGreaterThan(*x*, *y*)
* *x*.IsGreaterThan(*y*)

| x     | y          | operation          |
|-------|------------|--------------------|
| None  | *any*      | y != None          |
| *any* | None       | True               |
| int   | int/float  | x > y              |
| int   | str        | x > ToNumber(y)†   |
| int   | list       | [x] > y‡           |
| float | int/float  | x > y              |
| float | str        | x > ToNumber(y)    |
| float | list       | [x] > y            |
| str   | int/float  | ToNumber(x) > y    |
| str   | str        | x > y              |
| str   | list       | [x] > y            |
| list  | list       | x > y              |
| list  | *any*      | x > [y]            |

A type error is raised on all other combinations

† If the string value cannot be converted to a number
the corresponding non-string value is converted to
a string.

‡ After conversion to an array the comparison is
performed between corresponding elements.

```vgr
None > None → False
None > 5 → True
None > "5" → True
5 > " 5.0" → False
"5" > "5.0" → False
5 > [5] → False
[5, 7] > [5, "7"] → False
[5, 8] > [5, "7"] → True
```
"""
    # Everything is greater than None (except itself which is just equal)
    if x is None: return y is not None
    if y is None: return True
    override = _overrides.get((type(x), type(y)))
    return override(poly_gt, x, y) if override else x > y

@bound_ops("<=", "Is Not Greater Than", "≤", "¬>", "!>")
def poly_le(x: Any, y: Any) -> bool:
    """
**Less than or equal to comparison**

* *x* [Is] Not Greater Than *y*
* *x* <= *y*
* *x* ≤ *y*
* *x* ¬> *y*
* *x* !> *y*
* NotGreaterThan(*x*, *y*)
* *x*.NotGreaterThan(*y*)

| x     | y          | operation          |
|-------|------------|--------------------|
| None  | *any*      | True               |
| *any* | None       | False              |
| int   | int/float  | x <= y             |
| int   | str        | x <= ToNumber(y)†  |
| int   | list       | [x] <= y‡          |
| float | int/float  | x <= y             |
| float | str        | x <= ToNumber(y)   |
| float | list       | [x] <= y           |
| str   | int/float  | ToNumber(x) <= y   |
| str   | str        | x <= y             |
| str   | list       | [x] <= y           |
| list  | list       | x <= y             |
| list  | *any*      | x <= [y]           |

A type error is raised on all other combinations

† If the string value cannot be converted to a number
the corresponding non-string value is converted to
a string.

‡ After conversion to an array the comparison is
performed between corresponding elements.

```vgr
None <= None → True
None <= 5 → True
None <= "5" → True
5 <= " 5.0" → True
"5" <= "5.0" → True
5 <= [5] → True
[5, 7] <= [5, "7"] → True
[5, 8] <= [5, "7"] → False
```
"""
    # None is less than everything or equal to itself
    if x is None: return True
    if y is None: return False
    override = _overrides.get((type(x), type(y)))
    return override(poly_le, x, y) if override else x <= y

@bound_ops(">=", "Is Not Less Than", "≥", "¬<", "!<")
def poly_ge(x: Any, y: Any) -> bool:
    """
**Greater than or equal to comparison**

* *x* [Is] Not Less Than *y*
* *x* >= *y*
* *x* ≥ *y*
* *x* ¬< *y*
* *x* !< *y*
* NotLessThan(*x*, *y*)
* *x*.NotLessThan(*y*)

| x     | y          | operation          |
|-------|------------|--------------------|
| None  | *any*      | y == None          |
| *any* | None       | True               |
| int   | int/float  | x >= y             |
| int   | str        | x >= ToNumber(y)†  |
| int   | list       | [x] >= y‡          |
| float | int/float  | x >= y             |
| float | str        | x >= ToNumber(y)   |
| float | list       | [x] >= y           |
| str   | int/float  | ToNumber(x) >= y   |
| str   | str        | x >= y             |
| str   | list       | [x] >= y           |
| list  | list       | x >= y             |
| list  | *any*      | x >= [y]           |

A type error is raised on all other combinations

† If the string value cannot be converted to a number
the corresponding non-string value is converted to
a string.

‡ After conversion to an array the comparison is
performed between corresponding elements.

```vgr
None >= None → True
None >= 5 → False
None >= "5" → False
5 >= " 5.0" → True
"5" >= "5.0" → False
5 >= [5] → True
[5, 7] >= [5, "7"] → True
[5, 7] >= [5, "8"] → False
```
"""
    # Everything is greater than None and it is equal to itself
    if x is None: return y is None
    if y is None: return True
    override = _overrides.get((type(x), type(y)))
    return override(poly_ge, x, y) if override else x >= y

def poly_between(x: Any, y: Any=None, z: Any=None) -> bool:
    """
**Determine if a value is within an inclusive range**

* IsBetween(*value*, *low*, *high*)
* IsBetween(*value*, *high*, *low*)
* *value*.IsBetween(*low*, *high*)
* *value*.IsBetween(*high*, *low*)

If *low* and/or *high* are omitted, `None` is assumed.

When comparing mixed types, the type of the value,
not the constraints, determines conversions.

```vgr
None.IsBetween() → True
5.IsBetween(10) → True
5.IsBetween(4) → False
5.IsBetween(4, 10) → True
"dog".IsBetween("cat", "fish") → True
5.IsBetween(" 7", 3.2) → True

// An exclusive numeric range
4.IsBetween(4.0.Succ(), 5.0.Pred()) → False
```

Also see `Succ()` and `Pred()`, as well as `LessThan()` and `GreaterThan()` for conversion details
"""
    low, high = (y, z) if poly_lt(y, z) else (z, y)
    # We always want to use x as a base as it influences conversions
    return poly_ge(x, low) and poly_le(x, high)

def poly_clamp(x: Any, y: Any=None, z: Any=None) -> Any:
    """
**Constrain a value within an inclusive range**

* Clamp(*value*, *low*, *high*)
* Clamp(*value*, *high*, *low*)
* *value*.Clamp(*low*, *high*)
* *value*.Clamp(*high*, *low*)

If *low* and/or *high* are omitted, `None` is assumed.

When working with mixed types, the type of the value,
not the constraints, determines conversions.

```vgr
None.Clamp() → None
11.Clamp() → None
11.Clamp(5) → 5
11.Clamp(19) → 11
2.Clamp(5, 11) → 5
"dog".Clamp("cat", "fish") → "dog"
"horse".Clamp("cat", "fish") → "fish"
5.Clamp(" 7", 3.2) → 5

// An exclusive numeric range
4.Clamp(4.0.Succ(), 5.0.Pred()) → 4.000000000000001
```

Also see `Succ()` and `Pred()` as well as `LessThan()` and `GreaterThan()` for conversion details
"""
    low, high = (y, z) if poly_lt(y, z) else (z, y)
    # We always want to use x as a base as it influences conversions
    return low if poly_lt(x, low) else high if poly_gt(x, high) else x

def _str_num_op(op: Callable[[Any, Any], Any], x: str, y: Any) -> Any:
    """See if the string can be converted to a number before applying the operation"""
    try:
        return op(str_to_number(x), y)
    except ValueError:
        return op(x, str(y))

def _num_str_op(op: Callable[[Any, Any], Any], x: Any, y: str) -> Any:
    """See if the string can be converted to a number before applying the operation"""
    try:
        return op(x, str_to_number(y))
    except ValueError:
        return op(str(x), y)

def _lex_comp(cmp: Callable[[Any, Any], bool], x: Iterable, y: Iterable) -> bool:
    """Performs lexicographic comparison on non-scalar iterables using cmp for element-wise comparison."""
    for xi, yi in zip(x, y):
        # Once the equality fails, we apply the given comparison to the failing pair
        if not poly_eq(xi, yi): return cmp(xi, yi)
    # At this point, one is a prefix (or exact match) of
    # the other, so we apply the comparison to the length
    # which determines the desired order
    return cmp(len(x), len(y))

# Most items do a "natural" compare, except numeric/string and all collections
_overrides = {
    (int, str): _num_str_op,
    (int, list): lambda op, x, y: _lex_comp(op, [x], y),
    (int, tuple): lambda op, x, y: _lex_comp(op, (x,), y),
    (float, str): _num_str_op,
    (float, list): lambda op, x, y: _lex_comp(op, [x], y),
    (float, tuple): lambda op, x, y: _lex_comp(op, (x,), y),
    (str, int): _str_num_op,
    (str, float): _str_num_op,
    (str, list): lambda op, x, y: _lex_comp(op, [x], y),
    (str, tuple): lambda op, x, y: _lex_comp(op, [x], y),
    (list, int): lambda op, x, y: _lex_comp(op, x, [y]),
    (list, float): lambda op, x, y: _lex_comp(op, x, [y]),
    (list, str): lambda op, x, y: _lex_comp(op, x, [y]),
    (list, list): _lex_comp,
    (list, tuple): _lex_comp,
    (tuple, int): lambda op, x, y: _lex_comp(op, x, [y]),
    (tuple, float): lambda op, x, y: _lex_comp(op, x, [y]),
    (tuple, str): lambda op, x, y: _lex_comp(op, x, [y]),
    (tuple, list): _lex_comp,
    (tuple, tuple): _lex_comp,
}
