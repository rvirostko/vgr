#! /usr/bin/env python3

from functools import reduce
from typing import Any, Callable

from .common import dist_list, dist_tuple, str_to_number

def _str_num_op(op: Callable[[Any, Any], Any], x: str, y: Any) -> Any:
    """See if the string can be converted to a number before applying the operation"""
    y = int(y)
    try:
        return op(int(str_to_number(x)), y)
    except TypeError:
        return _int_str_op(op, y, x) # TODO reversed? Explain?

def _int_str_op(op: Callable[[Any, Any], Any], x: int, y: str) -> str:
    """The operation is distributed over the characters in the string"""
    return ''.join(chr(op(ord(c), x)) for c in y)

def _str_str_op(op: Callable[[Any, Any], Any], x: str, y: str) -> str:
    """See if either or both values can be converted to a number.
    If both are numbers, the operation is an int/int.
    If one can be converted, the operation is distriubted over the other
    If neither, the operation is applied between characters.
    """
    x1 = None
    try:
        x1 = int(str_to_number(x))
        try:
            # see if it can be an int/int operation
            return op(x1, int(str_to_number(y)))
        except TypeError:
            # y is not a number, so distribute x1 over y
            return _int_str_op(op, x1, y)
    except TypeError:
        try:
            # see if we can be an int/str operation with y
            return _int_str_op(op, int(str_to_number(y)), x)
        except TypeError:
            pass
    # neither x nor y were numbers
    # perform the operation between the two strings
    y_bytes = y.encode()
    y_len = len(y_bytes)
    return ''.join(chr(op(ord(c), y_bytes[i % y_len])) for i, c in enumerate(x))

_overrides = {
    (int, float): lambda op, x, y: op(x, int(y)),
    (int, str): lambda op, x, y: _str_num_op(op, y, x),
    (int, list): lambda op, x, y: dist_list(op, y, x),
    (int, tuple): lambda op, x, y: dist_tuple(op, y, x),
    (float, int): lambda op, x, y: op(int(x), y),
    (float, float): lambda op, x, y: op(int(x), int(y)),
    (float, str): lambda op, x, y: _str_num_op(op, y, x),
    (float, list): lambda op, x, y: dist_list(op, y, int(x)),
    (float, tuple): lambda op, x, y: dist_tuple(op, y, int(x)),
    (str, int): _str_num_op,
    (str, float): _str_num_op,
    (str, str): _str_str_op,
    (str, list): lambda op, x, y: dist_list(op, y, x),
    (str, tuple): lambda op, x, y: dist_tuple(op, y, x),
    (list, int): dist_list,
    (list, float): dist_list,
    (list, str): dist_list,
    (tuple, int): dist_tuple,
    (tuple, float): dist_tuple,
    (tuple, str): dist_tuple,
}

def poly_vbit_and(x: Any, *args) -> Any:
    """Varargs version of poly_bit_and"""
    return poly_bit_and(x, poly_vbit_or(0, args))

def poly_bit_and(x: Any, y: Any) -> Any:
    """Polymorphic bitwise and function.

# TODO

TypeError raised on all other combinations
"""
    if x is None: return None if y is None else poly_bit_and(0, y)
    if y is None: return poly_bit_and(x, 0)
    override = _overrides.get((type(x), type(y)))
    return override(poly_bit_and, x, y) if override else x & y

def poly_vbit_or(x: Any, *args) -> Any: return reduce(poly_bit_or, args, x)
def poly_bit_or(x: Any, y: Any) -> Any:
    """Polymorphic bitwise or function.

# TODO

TypeError raised on all other combinations
"""
    if x is None: return None if y is None else poly_bit_or(0, y)
    if y is None: return poly_bit_or(x, 0)
    override = _or_overrides.get((type(x), type(y)))
    if not override: override = _overrides.get((type(x), type(y)))
    return override(poly_bit_or, x, y) if override else x | y

_or_overrides = {
    (list, list): lambda _, x, y: x + y,
    (list, tuple): lambda _, x, y: x + list(y),
    (tuple, list): lambda _, x, y: x + tuple(y),
    (tuple, tuple): lambda _, x, y: x + y,
    (dict, dict): lambda _, x, y: {**x, **y},
}

def poly_vbit_xor(x: Any, *args) -> Any:
    """Varags version of poly_bit_xor"""
    return poly_bit_xor(x, poly_vbit_or(0, args))

def poly_bit_xor(x: Any, y: Any) -> Any:
    """Polymorphic bitwise xor function.

# TODO

TypeError raised on all other combinations
"""
    if x is None: return None if y is None else poly_bit_xor(0, y)
    if y is None: return poly_bit_xor(x, 0)
    override = _overrides.get((type(x), type(y)))
    return override(poly_bit_xor, x, y) if override else x ^ y

def poly_bit_not(x: Any) -> Any:
    """Polymorphic bitwise invert (negation) function.

# TODO

TypeError raised on all other combinations
"""
    if x is None: return None
    override = _overrides.get((type(x), int))
    if override: override(lambda x, _: poly_bit_not(x), x, 0)
    mask = 0xFF # Default to at least 8 bits
    if x != 0:
        # Find the position of the highest set bit (0-based index)
        highest_bit = x.bit_length()  # bit_length() gives the index of the highest bit + 1
        # Round up to the nearest multiple of 8 - Equivalent to ceil(highest_bit / 8) * 8
        rounded_bits = (highest_bit + 7) & ~7
        # Create a bitmask with all bits set up to rounded_bits
        mask = (1 << rounded_bits) - 1
    return x ^ mask
