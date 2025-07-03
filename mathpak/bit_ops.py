from functools import reduce
from typing import Any, Callable

from .common import dist_x, dist_y, str_to_number, X_None_Op, Y_None_Op, get_operation

def _str_num_op(op: Callable[[Any, Any], Any], x: str, y: Any) -> Any:
    """See if the string can be converted to a number before applying the operation"""
    y_int = int(y)
    try:
        return op(int(str_to_number(x)), y_int)
    except ValueError:
        return _int_str_op(op, y_int, x)

def _int_str_op(op: Callable[[Any, Any], Any], x: int, y: str) -> str:
    """The operation is distributed over the characters in the string"""
    return ''.join(chr(op(ord(c), x)) for c in y)

def _str_str_op(op: Callable[[Any, Any], Any], x: str, y: str) -> str:
    """
    See if either or both values can be converted to a number.
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
        except ValueError:
            # y is not a number, so distribute x1 over y
            return _int_str_op(op, x1, y)
    except ValueError:
        try:
            # see if we can be an int/str operation with y
            return _int_str_op(op, int(str_to_number(y)), x)
        except ValueError:
            pass
    # neither x nor y were numbers
    # perform the operation between the two strings
    y_bytes = y.encode()
    y_len = len(y_bytes)
    return ''.join(chr(op(ord(c), y_bytes[i % y_len])) for i, c in enumerate(x))

def poly_bit_and(x: Any, *args) -> Any:
    """Polymorphic bitwise and function.

# TODO

TypeError raised on all other combinations
"""
    return _bit_and(x, reduce(poly_bit_or, args, 0))

def _bit_and(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, bit_operations)
    return operation(_bit_and, x, y) if operation else x & y

def poly_bit_or(x: Any, *args) -> Any:
    """Polymorphic bitwise or function.

# TODO

TypeError raised on all other combinations
"""
    return reduce(_bit_or, args, x)

def _bit_or(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, bit_or_operations, bit_operations)
    return operation(_bit_or, x, y) if operation else x | y

def poly_bit_xor(x: Any, *args) -> Any:
    """Polymorphic bitwise xor function.

# TODO

TypeError raised on all other combinations
"""
    return _bit_xor(x, poly_bit_or(0, args))

def _bit_xor(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, bit_operations)
    return operation(_bit_xor, x, y) if operation else x ^ y

def poly_bit_not(x: Any) -> Any:
    """Polymorphic bitwise invert (negation) function.

# TODO

TypeError raised on all other combinations
"""
    if x is None: return None
    operation = bit_operations.get((type(x), int))
    if operation: return operation(lambda x, _: poly_bit_not(x), x, 0)
    mask = 0xFF # Default to at least 8 bits
    if x != 0:
        # Find the position of the highest set bit (0-based index)
        highest_bit = x.bit_length()  # bit_length() gives the index of the highest bit + 1
        # Round up to the nearest multiple of 8 - Equivalent to ceil(highest_bit / 8) * 8
        rounded_bits = (highest_bit + 7) & ~7
        # Create a bitmask with all bits set up to rounded_bits
        mask = (1 << rounded_bits) - 1
    return x ^ mask

# pylint: disable=arguments-out-of-order
bit_operations = {
    X_None_Op: lambda op, _, y: None if y is None else op(0, y),
    Y_None_Op: lambda op, x, _: op(x, 0),
    (int, float): lambda op, x, y: op(x, int(y)),
    (int, str): lambda op, x, y: _str_num_op(op, y, x),
    (int, list): dist_y,
    (int, tuple): dist_y,
    (float, int): lambda op, x, y: op(int(x), y),
    (float, float): lambda op, x, y: op(int(x), int(y)),
    (float, str): lambda op, x, y: _str_num_op(op, y, x),
    (float, list): lambda op, x, y: op(int(x), y),
    (float, tuple): lambda op, x, y: op(int(x), y),
    (str, int): _str_num_op,
    (str, float): _str_num_op,
    (str, str): _str_str_op,
    (str, list): dist_y,
    (str, tuple): dist_y,
    (list, int): dist_x,
    (list, float): dist_x,
    (list, str): dist_x,
    (tuple, int): dist_x,
    (tuple, float): dist_x,
    (tuple, str): dist_x,
}
# pylint: enable=arguments-out-of-order

# Collection-to-collection "or" combines contents
bit_or_operations = {
    (list, list): lambda _, x, y: x + y,
    (list, tuple): lambda _, x, y: x + list(y),
    (tuple, list): lambda _, x, y: x + tuple(y),
    (tuple, tuple): lambda _, x, y: x + y,
    (dict, dict): lambda _, x, y: {**x, **y},
}
