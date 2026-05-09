"""
Polymorphic inequality operators
"""

from typing import Any, Callable, Iterable
import math

from .common import (
    str_to_bool,
    str_to_number,
    bound_ops,
)

@bound_ops("Is Equal To", "==", "⩵", "Equals", "Is")
def poly_eq(x: Any=None, y: Any=None) -> bool:
    """
**Equality comparison**

* *x* [Is] Equal To *y*
* *x* Equals *y*
* *x* Is *y*
* *x* == *y*
* *x* ⩵ *y*
* IsEqualTo(*x*, *y*)
* *x*.IsEqualTo(*y*)

Returns `True` if the *x* and *y* are considered equal.

| Type(x)    | Type(y)       | Operation           |
|------------|---------------|---------------------|
| None       | *any*         | y == None           |
| *any*      | None          | False               |
| integer    | integer/float | x == y              |
| integer    | string        | x == ToNumber(y)†   |
| integer    | list          | [x] == y‡           |
| float      | integer/float | x == y              |
| float      | string        | x == ToNumber(y)    |
| float      | list          | [x] == y            |
| string     | integer/float | ToNumber(x) == y    |
| string     | string        | x == y              |
| string     | list          | [x] == y            |
| list       | list          | x == y              |
| list       | *any*         | x == [y]            |
| dictionary | dictionary    | x == y by attribute |

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

Also see the `!=` and `===` operators

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
def poly_exact_eq(x: Any=None, y: Any=None) -> bool:
    """
**Exact equality comparison**

* *x* === *y*

While similar to a regular equals comparison, it requires that
types of the two values match. No conversions are performed.

```vgr
5 == "5" -> True
5 === "5" -> False
```

Also see the `==` and `!=` operators
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
def poly_ne(x: Any=None, y: Any=None) -> bool:
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

| Type(x)    | Type(y)       | Operation           |
|------------|---------------|---------------------|
| None       | *any*         | y != None           |
| *any*      | None          | True                |
| integer    | integer/float | x != y              |
| integer    | string        | x != ToNumber(y)†   |
| integer    | list          | [x] != y‡           |
| float      | integer/float | x != y              |
| float      | string        | x != ToNumber(y)    |
| float      | list          | [x] != y            |
| string     | integer/float | ToNumber(x) != y    |
| string     | string        | x != y              |
| string     | list          | [x] != y            |
| list       | list          | x != y              |
| list       | *any*         | x != [y]            |
| dictionary | dictionary    | x != y by attr      |

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

Also see the `==` and `===` operators
"""
    return not poly_eq(x, y)

@bound_ops("Is Less Than", "<", "＜")
def poly_lt(x: Any=None, y: Any=None) -> bool:
    """
**Less than comparison**

* *x* [Is] Less Than *y*
* *x* < *y*
* *x* ＜ *y*
* IsLessThan(*x*, *y*)
* *x*.IsLessThan(*y*)

| Type(x) | Type(y)       | Operation          |
|---------|---------------|--------------------|
| None    | *any*         | y != None          |
| *any*   | None          | False              |
| integer | integer/float | x < y              |
| integer | string        | x < ToNumber(y)†   |
| integer | list          | [x] < y‡           |
| float   | integer/float | x < y              |
| float   | string        | x < ToNumber(y)    |
| float   | list          | [x] < y            |
| string  | integer/float | ToNumber(x) < y    |
| string  | string        | x < y              |
| string  | list          | [x] < y            |
| list    | list          | x < y              |
| list    | *any*         | x < [y]            |

A type error is raised on all other combinations

† If the string value cannot be converted to a number
the corresponding non-string value is converted to
a string.

‡ After conversion to an array the comparison is
performed between corresponding elements.

```vgr
None < None → False
None < 5 → True
None < "5" → True
5 < " 5.0" → False
"5" < "5.0" → True
5 < [5] → False
[5, 7] < [5, "7"] → False
[5, 8] < [5, "7"] → False
```

Also see the `>` and `<=` operators
"""
    # None is less than everything except itself
    if x is None: return y is not None
    if y is None: return False
    override = _overrides.get((type(x), type(y)))
    return override(poly_lt, x, y) if override else x < y

@bound_ops("Is Greater Than", ">", "＞")
def poly_gt(x: Any=None, y: Any=None) -> Any:
    """
**Greater than comparison**

* *x* [Is] Greater Than *y*
* *x* > *y*
* *x* ＞ *y*
* IsGreaterThan(*x*, *y*)
* *x*.IsGreaterThan(*y*)

| Type(x) | Type(y)       | Operation          |
|---------|---------------|--------------------|
| None    | *any*         | y != None          |
| *any*   | None          | True               |
| integer | integer/float | x > y              |
| integer | string        | x > ToNumber(y)†   |
| integer | list          | [x] > y‡           |
| float   | integer/float | x > y              |
| float   | string        | x > ToNumber(y)    |
| float   | list          | [x] > y            |
| string  | integer/float | ToNumber(x) > y    |
| string  | string        | x > y              |
| string  | list          | [x] > y            |
| list    | list          | x > y              |
| list    | *any*         | x > [y]            |

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

Also see the `<` and `>=` operators
"""
    # Everything is greater than None (except itself which is just equal)
    if x is None: return y is not None
    if y is None: return True
    override = _overrides.get((type(x), type(y)))
    return override(poly_gt, x, y) if override else x > y

@bound_ops("<=", "Is Not Greater Than", "≤", "¬>", "!>")
def poly_le(x: Any=None, y: Any=None) -> bool:
    """
**Less than or equal to comparison**

* *x* [Is] Not Greater Than *y*
* *x* <= *y*
* *x* ≤ *y*
* *x* ¬> *y*
* *x* !> *y*
* NotGreaterThan(*x*, *y*)
* *x*.NotGreaterThan(*y*)

| Type(x) | Type(y)       | Operation          |
|---------|---------------|--------------------|
| None    | *any*         | True               |
| *any*   | None          | False              |
| integer | integer/float | x <= y             |
| integer | string        | x <= ToNumber(y)†  |
| integer | list          | [x] <= y‡          |
| float   | integer/float | x <= y             |
| float   | string        | x <= ToNumber(y)   |
| float   | list          | [x] <= y           |
| string  | integer/float | ToNumber(x) <= y   |
| string  | string        | x <= y             |
| string  | list          | [x] <= y           |
| list    | list          | x <= y             |
| list    | *any*         | x <= [y]           |

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

Also see the `<` and `>=` operators
"""
    # None is less than everything or equal to itself
    if x is None: return True
    if y is None: return False
    override = _overrides.get((type(x), type(y)))
    return override(poly_le, x, y) if override else x <= y

@bound_ops(">=", "Is Not Less Than", "≥", "¬<", "!<")
def poly_ge(x: Any=None, y: Any=None) -> bool:
    """
**Greater than or equal to comparison**

* *x* [Is] Not Less Than *y*
* *x* >= *y*
* *x* ≥ *y*
* *x* ¬< *y*
* *x* !< *y*
* NotLessThan(*x*, *y*)
* *x*.NotLessThan(*y*)

| Type(x) | Type(y)       | Operation          |
|---------|---------------|--------------------|
| None    | *any*         | y == None          |
| *any*   | None          | True               |
| integer | integer/float | x >= y             |
| integer | string        | x >= ToNumber(y)†  |
| integer | list          | [x] >= y‡          |
| float   | integer/float | x >= y             |
| float   | string        | x >= ToNumber(y)   |
| float   | list          | [x] >= y           |
| string  | integer/float | ToNumber(x) >= y   |
| string  | string        | x >= y             |
| string  | list          | [x] >= y           |
| list    | list          | x >= y             |
| list    | *any*         | x >= [y]           |

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

Also see the `>` and `<=` operators
"""
    # Everything is greater than None and it is equal to itself
    if x is None: return y is None
    if y is None: return True
    override = _overrides.get((type(x), type(y)))
    return override(poly_ge, x, y) if override else x >= y

def poly_is_between(x: Any=None, y: Any=None, z: Any=None) -> bool:
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

Also see `Succ()` and `Pred()`, as well as `IsLessThan()` and `IsGreaterThan()` for conversion details
"""
    low, high = (y, z) if poly_lt(y, z) else (z, y)
    # We always want to use x as a base as it influences conversions
    return poly_ge(x, low) and poly_le(x, high)

def poly_clamp(x: Any=None, y: Any=None, z: Any=None) -> Any:
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

Also see `Succ()` and `Pred()` as well as `IsLessThan()` and `IsGreaterThan()` for conversion details
"""
    low, high = (y, z) if poly_lt(y, z) else (z, y)
    # We always want to use x as a base as it influences conversions
    return low if poly_lt(x, low) else high if poly_gt(x, high) else x

@bound_ops('Is Negative', 'Is Not Positive')
def poly_is_negative(x: Any=None) -> Any:
    """
**Is the value less than zero**

* *value* Is Negative
* *value* Is Not Positive
* IsNegative(*value*)
* *value*.IsNegative()

Strings will be converted to numbers.
Note that zero is neither positive nor negative.

```vgr
For Each v In [ None, List(), Dictionary(), -1, Zero, 1 ]
  Choose Using v:
    When Is Negative: Print v.Repr(), "is negative"
    When Is Positive: Print v.Repr(), "is positive"
    Otherwise: Print v.Repr(), "is neither negative nor positive"
  End-Choose
End-For

None is neither negative nor positive
[] is neither negative nor positive
{} is neither negative nor positive
-1 is negative
0 is neither negative nor positive
1 is positive
```

Also see `Is Negative` and `Sign()`
"""
    return isinstance(x, (str, int, float)) and poly_lt(x, 0)

@bound_ops('Is Positive', 'Is Not Negative')
def poly_is_positive(x: Any=None) -> Any:
    """
**Is the value greater than zero**

* *value* Is Positive
* *value* Is Not Negative
* IsPositive(*value*)
* *value*.IsPositive()

Strings will be converted to numbers.
Note that zero is neither positive nor negative.

```vgr
For Each v In [ None, List(), Dictionary(), -1, Zero, 1 ]
  Choose Using v:
    When Is Negative: Print v.Repr(), "is negative"
    When Is Positive: Print v.Repr(), "is positive"
    Otherwise: Print v.Repr(), "is neither negative nor positive"
  End-Choose
End-For

None is neither negative nor positive
[] is neither negative nor positive
{} is neither negative nor positive
-1 is negative
0 is neither negative nor positive
1 is positive
```

Also see `Is Positive` and `Sign()`
"""
    return isinstance(x, (str, int, float)) and poly_gt(x, 0)

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

def _str_bool_op(op: Callable[[Any, Any], Any], x: str, y: bool) -> Any:
    try:
        # "1" == True
        return op(str_to_number(x), y)
    except ValueError:
        try:
            # "False" == False
            return op(str_to_bool(x), y)
        except ValueError:
            return op(x, str(y))

def _bool_str_op(op: Callable[[Any, Any], Any], x: bool, y: str) -> Any:
    try:
        # False == "0"
        return op(x, str_to_number(y))
    except ValueError:
        try:
            # False == "False"
            return op(x, str_to_bool(y))
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
    (bool, str): _bool_str_op,
    (int, str): _num_str_op,
    (int, list): lambda op, x, y: _lex_comp(op, [x], y),
    (float, str): _num_str_op,
    (float, list): lambda op, x, y: _lex_comp(op, [x], y),
    (str, bool): _str_bool_op,
    (str, int): _str_num_op,
    (str, float): _str_num_op,
    (str, list): lambda op, x, y: _lex_comp(op, [x], y),
    (list, int): lambda op, x, y: _lex_comp(op, x, [y]),
    (list, float): lambda op, x, y: _lex_comp(op, x, [y]),
    (list, str): lambda op, x, y: _lex_comp(op, x, [y]),
    (list, list): _lex_comp,
}
