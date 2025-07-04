"""
Polymorphic inequality operators
"""

from typing import Any, Callable, Iterable

from .common import str_to_number

def poly_eq(x: Any, y: Any) -> bool:
    """
**Polymorphic equals comparison**

* _value_.IsEqualTo(_value_)
* _value_ == _value_
* _value_ Equals _value_
* _value_ Is _value_
* _value_ [Is] Equal To _value_

"""
    # None is only equal to itself
    if x is None: return y is None
    if y is None: return False
    override = _overrides.get((type(x), type(y)))
    return override(poly_eq, x, y) if override else x == y

def poly_ne(x: Any, y: Any) -> bool:
    """Polymorphic not equals comparison.
# TODO

TypeError raised on all other combinations
"""
    return not poly_eq(x, y)

def poly_lt(x: Any, y: Any) -> bool:
    """Polymorphic less than comparison.
# TODO

TypeError raised on all other combinations
"""
    # None is less than everything except itself
    if x is None: return y is not None
    if y is None: return False
    override = _overrides.get((type(x), type(y)))
    return override(poly_lt, x, y) if override else x < y

def poly_gt(x: Any, y: Any) -> Any:
    """Polymorphic greater than comparison.
# TODO

TypeError raised on all other combinations
"""
    # Everything is greater than None (except itself which is just equal)
    if x is None: return False
    if y is None: return True
    override = _overrides.get((type(x), type(y)))
    return override(poly_gt, x, y) if override else x > y

def poly_le(x: Any, y: Any) -> bool:
    """Polymorphic less than or equal to comparison.
# TODO

TypeError raised on all other combinations
"""
    # None is less than everything or equal to itself
    if x is None: return True
    if y is None: return False
    override = _overrides.get((type(x), type(y)))
    return override(poly_le, x, y) if override else x <= y

def poly_ge(x: Any, y: Any) -> bool:
    """Polymorphic greater than or equal to comparison.
# TODO

TypeError raised on all other combinations
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

# Most items do a "natural" compare, except numeric/string
# and all collections
# NB: str/str doe NOT attempt math conversions (it probably should)
#     and should both be non-numeric, there is an infinite loop problem.
#     str/str like that would need to be handled outside this table.
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
