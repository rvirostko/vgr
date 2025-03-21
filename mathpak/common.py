#! /usr/bin/env python3

"""
Routines and values that can be used by operator and function implementations.
"""

from typing import Any, Callable, Union

Number = Union[int, float]

# Operations table key for when the x value is None
X_None_Op = (type(None), type(Any))

# Operations table key for when the Y value is None
Y_None_Op = (type(Any), type(None))

# See matching_default()
_DEFAULTS_BY_TYPE = {
    dict : {},
    float : 0.0,
    int : 0,
    list : [],
    str : '',
    tuple : tuple(),
}

_TRUE_STRS = ('true', 't', 'yes', 'y', 'on')
_FALSE_STRS = ('false', 'f', 'no', 'n', 'off')

def str_to_number(s: str) -> Number:
    """
    Attempts to convert a string to a number value.
    Raises ValueError if it can't.
    """
    try:
        x: float = float(s.strip())
        return int(x) if x.is_integer() else x
    except ValueError as e:
        raise ValueError(f'Cannot convert {repr(s)} to a number') from e

def str_to_int(x: str) -> int:
    """See str_to_number - forces an int result"""
    return int(str_to_number(x))

def str_to_bool(x: str) -> bool:
    if x is None or x.isspace(): return False
    x = x.strip().lower()
    if x in _TRUE_STRS: return True
    if x in _FALSE_STRS: return False
    try:
        return bool(str_to_number(x))
    except ValueError:
        # we return True just because a non-None is "truthy"
        return True

def dist_x_list(op: Callable[[Any, Any], Any], x: list, y: Any) -> list:
    """
    Distribute op over the list: [op(<list>, y)]
    See dist_y_list()
    """
    return [op(x1, y) for x1 in x]

def dist_x_tuple(op: Callable[[Any, Any], Any], x: tuple, y: Any) -> tuple:
    """
    Distribute op over the tuple: (op(<list>, y))
    See dist_y_tuple()
    """
    return tuple(op(x1, y) for x1 in x)

def dist_y_list(op: Callable[[Any, Any], Any], x: Any, y: list) -> list:
    """
    Distribute op over the list: [op(x, <list>)]
    Used by commutative operations with a scalar x and list y
    See dist_x_list()
    """
    return [op(x, y1) for y1 in y]

def dist_y_tuple(op: Callable[[Any, Any], Any], x: tuple, y: Any) -> tuple:
    """
    Distribute op over the list: (op(x, <list>))
    Used by commutative operations with a scalar x and list y
    See dist_x_tuple()
    """
    return tuple(op(x, y1) for y1 in y)

def matching_default(x: Any) -> Any:
    """Given an object, return a _default_ value that matches its type"""
    xtype = type(x)
    default = _DEFAULTS_BY_TYPE.get(xtype)
    if default is not None: return default
    raise TypeError(f'No default value for {xtype.__name__}') # SNO

def op_key(x: Any, y: Any) -> tuple:
    """The key used to look up behavior by operand type"""
    if x is None: return X_None_Op
    if y is None: return Y_None_Op
    return (type(x), type(y))

def get_operation(x, y, *op_tables) -> Callable[[Any, Any], Any]:
    """Using the list of tables, find an applicable operation"""
    key = op_key(x, y)
    for op_table in op_tables:
        op = op_table.get(key)
        if op is not None: return op
    return None

# For non-commutative numeric operations that don't define behaviors for
# dictionaries and have "natural" operations on int/float
# Generally it attempts to cast strings to numbers and
# distributes operations over collections.
numeric_operations = {
    X_None_Op: lambda op, _, y: None if y is None else op(matching_default(y), y),
    Y_None_Op: lambda op, x, _: op(x, matching_default(x)),
    (int, str): lambda op, x, y: op(x, str_to_number(y)),
    (float, str): lambda op, x, y: op(x, str_to_number(y)),
    (str, int): lambda op, x, y: op(str_to_number(x), y),
    (str, float): lambda op, x, y: op(str_to_number(x), y),
    (str, str): lambda op, x, y: op(str_to_number(x), str_to_number(y)),
    (list, int): dist_x_list,
    (list, float): dist_x_list,
    (list, str): dist_x_list,
    (tuple, int): dist_x_tuple,
    (tuple, float): dist_x_tuple,
    (tuple, str): dist_x_tuple,
}
