#! /usr/bin/python3

from typing import Any, Callable, Iterable

from .common import str_to_number, time_test

def poly_eq(x: Any, y: Any) -> bool:
    """Polymorphic equals comparison.
# TODO

TypeError raised on all other combinations
"""
    # None is only equal to itself
    if x == None: return y == None
    if y == None: return False
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
    if x == None: return y != None
    if y == None: return False
    override = _overrides.get((type(x), type(y)))
    return override(poly_lt, x, y) if override else x < y

def poly_gt(x: Any, y: Any) -> Any:
    """Polymorphic greater than comparison.
# TODO

TypeError raised on all other combinations
"""
    # Everything is greater than None (except itself which is just equal)
    if x == None: return False
    if y == None: return True
    override = _overrides.get((type(x), type(y)))
    return override(poly_gt, x, y) if override else x > y

def poly_le(x: Any, y: Any) -> bool:
    """Polymorphic less than or equal to comparison.
# TODO

TypeError raised on all other combinations
"""
    # None is less than everything or equal to itself
    if x == None: return True
    if y == None: return False
    override = _overrides.get((type(x), type(y)))
    return override(poly_le, x, y) if override else x <= y

def poly_ge(x: Any, y: Any) -> bool:
    """Polymorphic greater than or equal to comparison.
# TODO

TypeError raised on all other combinations
"""
    # Everything is greater than None and it is equal to itself
    if x == None: return y == None
    if y == None: return True
    override = _overrides.get((type(x), type(y)))
    return override(poly_ge, x, y) if override else x >= y

def _str_num_op(op: Callable[[Any, Any], Any], x: str, y: Any) -> Any:
    """See if the string can be converted to a number before applying the operation"""
    try:
        return op(str_to_number(x), y)
    except TypeError:
        return op(x, str(y))

def _num_str_op(op: Callable[[Any, Any], Any], x: Any, y: str) -> Any:
    """See if the string can be converted to a number before applying the operation"""
    try:
        return op(x, str_to_number(y))
    except TypeError:
        return op(str(x), y)

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
    (list, list): lambda op, x, y: _lex_comp(op, x, y),
    (list, tuple): lambda op, x, y: _lex_comp(op, x, y),
    (tuple, int): lambda op, x, y: _lex_comp(op, x, [y]),
    (tuple, float): lambda op, x, y: _lex_comp(op, x, [y]),
    (tuple, str): lambda op, x, y: _lex_comp(op, x, [y]),
    (tuple, list): lambda op, x, y: _lex_comp(op, x, y),
    (tuple, tuple): lambda op, x, y: _lex_comp(op, x, y),
}

def _lex_comp(cmp: Callable[[Any, Any], bool], x: Iterable, y: Iterable) -> bool:
    """Performs lexicographic comparison on non-scalar iterables using cmp for element-wise comparison."""
    for xi, yi in zip(x, y):
        # Once the equality fails, we apply the given comparison to the failing pair
        if not poly_eq(xi, yi): return cmp(xi, yi)
    # At this point, one is a prefix (or exact match) of
    # the other, so we apply the comparison to the length
    # which determines the desired order
    return cmp(len(x), len(y))

def inequ_test():
    cases = [
        (True, 3),
        (False, 3),
        (2, True),
        (2, False),
        (True, True),
        (False, False),
        (True, 1),
        (False, 0),
        ("a", "b"),
        ("a", 1),
        ("a", 1.0),
        (1, "2"),
        (1.0, "+2"),
        (2, 3),
        (2, 3.5),
        (2, "3"),
        (2.5, 3),
        (2.5, 3.5),
        (2.5, "3"),
        (2.5, "frog"),
        ("2", 3),
        ("2", 3.5),
        ("2", "3"),
        ([2, 3, 4], 2),
        ([2.5, 3.5], 2.0),
        ([2, 3, 4], "2"),
        ("-2.0", [2, 3, 4]),
        ((2, 3, 4), 2),
        ((2.5, 3.5), 2.0),
        (2.0, (2.5, 3.5)),
        ((2, 3, 4), "2"),
        ((2, 3, 4), ["2", 3, 4.0]),
        (None, 3),
        (2, None),
        (None, None),
    ]
    #time_test(poly_eq, cases, 1)
    #time_test(poly_neq, cases, 1)
    #time_test(poly_lt, cases, 1)
    #time_test(poly_gt, cases, 1)
    #time_test(poly_le, cases, 1)
    time_test(poly_ge, cases, 1)

if __name__ == "__main__": inequ_test()
