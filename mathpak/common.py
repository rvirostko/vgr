#! /usr/bin/env python3

"""
Routines and values that can be used by operator and function implementations.
"""

from typing import Any, Callable, Union

Number = Union[int, float]

NoneType = type(None)

# See matching_default()
_DEFAULTS_BY_TYPE = {
    dict : {},
    float : 0.0,
    int : 0,
    list : [],
    str : '',
    tuple : tuple(),
}

def str_to_number(s: str) -> Number:
    """Attempts to convert a string to a number value. Raises TypeError if it can't."""
    try:
        x: float = float(s.strip())
        return int(x) if x.is_integer() else x
    except ValueError as e:
        raise TypeError(f'Cannot convert "{s}" to a number') from e

def dist_list(op: Callable[[Any, Any], Any], x: list, y: Any) -> list:
    """Distribute op over the list: [op(<list>, y)]"""
    return [op(x1, y) for x1 in x]

def dist_tuple(op: Callable[[Any, Any], Any], x: tuple, y: Any) -> tuple:
    """Distribute op over the tuple: (op(<list>, y))"""
    return tuple(op(x1, y) for x1 in x)

def matching_default(x: Any) -> Any:
    """Given an object, return a _default_ value that matches its type"""
    xtype = type(x)
    default = _DEFAULTS_BY_TYPE.get(xtype)
    if default is not None: return default
    raise TypeError(f'No default value for {xtype.__name__}')

def op_key(x: Any, y: Any) -> tuple:
    """The key used to look up behavior by operand type"""
    # TODO none type handling here in the future
    return (type(x), type(y))

# For non-commutative mathematical operations that don't define behaviors for
# dictionaries and have "natural" operations on int/float
# Generally it attempts to cast strings to numbers and
# distributes operations over collections.
math_overrides = {
    (int, str): lambda op, x, y: op(x, str_to_number(y)),
    (float, str): lambda op, x, y: op(x, str_to_number(y)),
    (str, int): lambda op, x, y: op(str_to_number(x), y),
    (str, float): lambda op, x, y: op(str_to_number(x), y),
    (str, str): lambda op, x, y: op(str_to_number(x), str_to_number(y)),
    (list, int): dist_list,
    (list, float): dist_list,
    (list, str): dist_list,
    (tuple, int): dist_tuple,
    (tuple, float): dist_tuple,
    (tuple, str): dist_tuple,
}
