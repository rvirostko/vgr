"""
Polymorphic inequality operators
"""

from typing import Any, Callable, Iterable

from .common import str_to_number, bound_ops

@bound_ops("==", "⩵", "Equals", "Is", "Is Equal To")
def poly_eq(x: Any, y: Any) -> bool:
    """
**Equals comparison**

* _x_ == _y_
* _x_ ⩵ _y_
* _x_ Equals _y_
* _x_ Is _y_
* _x_ [Is] Equal To _y_
* _x_.IsEqualTo(_y_)

| x     | y          | operation           |
|-------|------------|---------------------|
| None  | _any_      | y == None           |
| _any_ | None       | False               |
| int   | int/float  | x == y              |
| int   | str        | x == ToNumber(y)†   |
| int   | list/tuple | [x] == y‡           |
| float | int/float  | x == y              |
| float | str        | x == ToNumber(y)    |
| float | list/tuple | [x] == y            |
| str   | int/float  | ToNumber(x) == y    |
| str   | str        | x == y              |
| str   | list/tuple | [x] == y            |
| list  | list/tuple | x == y              |
| list  | _any_      | x == [y]            |
| tuple | list/tuple | x == y              |
| tuple | _any_      | x == [y]            |
| dict  | dict       | x == y by attr      |
| dict  | _any_      | False               |

TypeError raised on all other combinations

† If the string value cannot be converted to a number
the corresponding non-string value is converted to
a string.

‡ After conversion to an array the comparison is
performed between corresponding elements.
"""
    # None is only equal to itself
    if x is None: return y is None
    if y is None: return False
    override = _overrides.get((type(x), type(y)))
    return override(poly_eq, x, y) if override else x == y

@bound_ops("===")
def poly_exact_eq(x: Any, y: Any) -> bool:
    """
**Exact Equals comparison**

* _x_ === _y_

While similar to a regular equals comparison, it requires that
types of the two values match. No conversion are performed.
"""
    # None is only equal to itself
    if x is None: return y is None
    if y is None: return False
    tx = type(x)
    ty = type(y)
    if tx != ty: return False
    override = _overrides.get((tx, ty))
    return override(poly_exact_eq, x, y) if override else x == y

@bound_ops("!=", "≠", "<>", "¬=", "Is Not", "Is Not Equal To")
def poly_ne(x: Any, y: Any) -> bool:
    """
**Not equals comparison**

* _x_ != _y_
* _x_ ≠ _y_
* _x_ <> _y_
* _x_ ¬= _y_
* _x_ Is Not _y_
* _x_ [Is] Not Equal To _y_
* _x_.NotEqualTo(_y_)

| x     | y          | operation           |
|-------|------------|---------------------|
| None  | _any_      | y != None           |
| _any_ | None       | True                |
| int   | int/float  | x != y              |
| int   | str        | x != ToNumber(y)†   |
| int   | list/tuple | [x] != y‡           |
| float | int/float  | x != y              |
| float | str        | x != ToNumber(y)    |
| float | list/tuple | [x] != y            |
| str   | int/float  | ToNumber(x) != y    |
| str   | str        | x != y              |
| str   | list/tuple | [x] != y            |
| list  | list/tuple | x != y              |
| list  | _any_      | x != [y]            |
| tuple | list/tuple | x != y              |
| tuple | _any_      | x != [y]            |
| dict  | dict       | x != y by attr      |
| dict  | _any_      | True                |

TypeError raised on all other combinations

† If the string value cannot be converted to a number
the corresponding non-string value is converted to
a string.

‡ After conversion to an array the comparison is
performed between corresponding elements.
"""
    return not poly_eq(x, y)

@bound_ops("<", "＜", "Is Less Than")
def poly_lt(x: Any, y: Any) -> bool:
    """
**Less than comparison**

* _x_ < _y_
* _x_ ＜ _y_
* _x_ [Is] Less Than _y_
* _x_.IsLessThan(_y_)

| x     | y          | operation          |
|-------|------------|--------------------|
| None  | _any_      | y != None          |
| _any_ | None       | False              |
| int   | int/float  | x < y              |
| int   | str        | x < ToNumber(y)†   |
| int   | list/tuple | [x] < y‡           |
| float | int/float  | x < y              |
| float | str        | x < ToNumber(y)    |
| float | list/tuple | [x] < y            |
| str   | int/float  | ToNumber(x) < y    |
| str   | str        | x < y              |
| str   | list/tuple | [x] < y            |
| list  | list/tuple | x < y              |
| list  | _any_      | x < [y]            |
| tuple | list/tuple | x < y              |
| tuple | _any_      | x < [y]            |
| dict  | dict       | x < y by attr      |

TypeError raised on all other combinations

† If the string value cannot be converted to a number
the corresponding non-string value is converted to
a string.

‡ After conversion to an array the comparison is
performed between corresponding elements.
"""
    # None is less than everything except itself
    if x is None: return y is not None
    if y is None: return False
    override = _overrides.get((type(x), type(y)))
    return override(poly_lt, x, y) if override else x < y

@bound_ops(">", "＞", "Is Greater Than")
def poly_gt(x: Any, y: Any) -> Any:
    """
**Greater than comparison**

* _x_ > _y_
* _x_ ＞ _y_
* _x_ [Is] Greater Than _y_
* _x_.IsGreaterThan(_y_)

| x     | y          | operation          |
|-------|------------|--------------------|
| None  | _any_      | y != None          |
| _any_ | None       | True               |
| int   | int/float  | x > y              |
| int   | str        | x > ToNumber(y)†   |
| int   | list/tuple | [x] > y‡           |
| float | int/float  | x > y              |
| float | str        | x > ToNumber(y)    |
| float | list/tuple | [x] > y            |
| str   | int/float  | ToNumber(x) > y    |
| str   | str        | x > y              |
| str   | list/tuple | [x] > y            |
| list  | list/tuple | x > y              |
| list  | _any_      | x > [y]            |
| tuple | list/tuple | x > y              |
| tuple | _any_      | x > [y]            |
| dict  | dict       | x > y by attr      |

TypeError raised on all other combinations

† If the string value cannot be converted to a number
the corresponding non-string value is converted to
a string.

‡ After conversion to an array the comparison is
performed between corresponding elements.
"""
    # Everything is greater than None (except itself which is just equal)
    if x is None: return y is not None
    if y is None: return True
    override = _overrides.get((type(x), type(y)))
    return override(poly_gt, x, y) if override else x > y

@bound_ops("<=", "≤", "¬>", "!>", "Is Not Greater Than")
def poly_le(x: Any, y: Any) -> bool:
    """
**Less than or equal to comparison**

* _x_ <= _y_
* _x_ ≤ _y_
* _x_ ¬> _y_
* _x_ !> _y_
* _x_ [Is] Not Greater Than _y_
* _x_.NotGreaterThan(_y_)

| x     | y          | operation          |
|-------|------------|--------------------|
| None  | _any_      | True               |
| _any_ | None       | False              |
| int   | int/float  | x <= y             |
| int   | str        | x <= ToNumber(y)†  |
| int   | list/tuple | [x] <= y‡          |
| float | int/float  | x <= y             |
| float | str        | x <= ToNumber(y)   |
| float | list/tuple | [x] <= y           |
| str   | int/float  | ToNumber(x) <= y   |
| str   | str        | x <= y             |
| str   | list/tuple | [x] <= y           |
| list  | list/tuple | x <= y             |
| list  | _any_      | x <= [y]           |
| tuple | list/tuple | x <= y             |
| tuple | _any_      | x <= [y]           |
| dict  | dict       | x <= y by attr     |

TypeError raised on all other combinations

† If the string value cannot be converted to a number
the corresponding non-string value is converted to
a string.

‡ After conversion to an array the comparison is
performed between corresponding elements.
"""
    # None is less than everything or equal to itself
    if x is None: return True
    if y is None: return False
    override = _overrides.get((type(x), type(y)))
    return override(poly_le, x, y) if override else x <= y

@bound_ops(">=", "≥", "¬<", "!<", "Is Not Less Than")
def poly_ge(x: Any, y: Any) -> bool:
    """
**Greater than or equal to comparison**

* _x_ >= _y_
* _x_ ≥ _y_
* _x_ ¬< _y_
* _x_ !< _y_
* _x_ [Is] Not Less Than _y_
* _x_.NotLessThan(_y_)

| x     | y          | operation          |
|-------|------------|--------------------|
| None  | _any_      | y == None          |
| _any_ | None       | True               |
| int   | int/float  | x >= y             |
| int   | str        | x >= ToNumber(y)†  |
| int   | list/tuple | [x] >= y‡          |
| float | int/float  | x >= y             |
| float | str        | x >= ToNumber(y)   |
| float | list/tuple | [x] >= y           |
| str   | int/float  | ToNumber(x) >= y   |
| str   | str        | x >= y             |
| str   | list/tuple | [x] >= y           |
| list  | list/tuple | x >= y             |
| list  | _any_      | x >= [y]           |
| tuple | list/tuple | x >= y             |
| tuple | _any_      | x >= [y]           |
| dict  | dict       | x >= y by attr     |

TypeError raised on all other combinations

† If the string value cannot be converted to a number
the corresponding non-string value is converted to
a string.

‡ After conversion to an array the comparison is
performed between corresponding elements.
"""
    # Everything is greater than None and it is equal to itself
    if x is None: return y is None
    if y is None: return True
    override = _overrides.get((type(x), type(y)))
    return override(poly_ge, x, y) if override else x >= y

def poly_between(x: Any, y: Any, z: Any) -> bool:
    """
**Determine if a value is within an inclusive range**

* _value_.IsBetween(_low_, _high_)
* _value_.IsBetween(_high_, _low_)

When comparing mixed types, the type of the value,
not the constraints, determines conversions.
See _NotLessThan()_ and _NotGreaterThan()_ for
conversion details.
"""
    low, high = (y, z) if poly_lt(y, z) else (z, y)
    # We always want to use x as a base as it influences conversions
    return poly_ge(x, low) and poly_le(x, high)

def poly_clamp(x: Any, y: Any, z: Any) -> Any:
    """
**Constrain a value within a range**

* _value_.Clamp(_low_, _high_)
* _value_.Clamp(_high_, _low_)

When working with mixed types, the type of the value,
not the constraints, determines conversions.
See _LessThan()_ and _GreaterThan()_ for
conversion details.
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
