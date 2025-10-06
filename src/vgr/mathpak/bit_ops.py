from functools import reduce
from typing import Any, Callable

from .common import bound_ops, dist_x, dist_y, str_to_number, X_None_Op, Y_None_Op, get_operation

@bound_ops("&")
def poly_bit_and(x: Any, *args) -> Any:
    """
**Bitwise And operation**

* _x_ & _y_
* BitAnd(_x_, _y_...)
* _x_.BitAnd(_y_...)

| x     | y     | returns   | operation             |
|-------|-------|-----------|-----------------------|
| int   | int   | int       | x & y                 |
| int   | float | int       | x & y                 |
| int   | str   | int       | _See below_           |
| _any_ | list  | list      | distributive          |
| float | int   | int       | ToInt(x) & y          |
| float | float | int       | ToInt(x) & ToInt(y)   |
| float | str   | int       | _See below_           |
| str   | int   | str       | _See below_           |
| str   | float | str       | _See below_           |
| str   | str   | str       | _See below_           |
| list  | _any_ | list      | distributive          |

TypeError raised on all other combinations

*String operations*

```vgr
"frog" & 3 → "\\x02\\x02\\x03\\x03"
"frog" & 3.14 → "\\x02\\x02\\x03\\x03"
"frog" & "1" → "\\x00\\x00\\x01\\x01"
"frog" & "1".Ord() → " 0!!"
"frog" & "o" → "fbog"
"frog" & "AB" → "@BAB"
["frog", "bog"].BitAnd("AB") → ["@BAB", "@BA"]
```

Also see `BitOr()` and `BitXor()`
"""
    return reduce(_bit_and, args, x)

@bound_ops("|")
def poly_bit_or(x: Any, *args) -> Any:
    """
**Bitwise Or operation**

* _x_ | _y_
* BitOr(_x_, _y_...)
* _x_.BitOr(_y_...)

| x     | y     | returns   | operation             |
|-------|-------|-----------|-----------------------|
| int   | int   | int       | x | y                 |
| int   | float | int       | x | y                 |
| int   | str   | int       | _See below_           |
| _any_ | list  | list      | distributive          |
| float | int   | int       | ToInt(x) | y          |
| float | float | int       | ToInt(x) | ToInt(y)   |
| float | str   | int       | _See below_           |
| str   | int   | str       | _See below_           |
| str   | float | str       | _See below_           |
| str   | str   | str       | _See below_           |
| list  | _any_ | list      | distributive          |

TypeError raised on all other combinations

*String operations*

```vgr
"frog" | 3 → "gsog"
"frog" | 3.14 → "gsog"
"frog" | "1" → "gsog"
"frog" | "1".Ord() → "ws\\x7fw"
"frog" | "o" → "o\\x7foo"
"frog" | "AB" → "grog"
["frog", "bog"].BitOr("AB") → ["grog", "cog"]
```

Also see `BitAnd()` and `BitXor()`
"""
    return reduce(_bit_or, args, x)

@bound_ops("^")
def poly_bit_xor(x: Any, *args) -> Any:
    """
**Bitwise exclusive Or (Xor) operation**

* _x_ ^ _y_
* BitXor(_x_, _y_...)
* _x_.BitXor(_y_...)

| x     | y     | returns   | operation             |
|-------|-------|-----------|-----------------------|
| int   | int   | int       | x ^ y                 |
| int   | float | int       | x ^ y                 |
| int   | str   | int       | _See below_           |
| _any_ | list  | list      | distributive          |
| float | int   | int       | ToInt(x) ^ y          |
| float | float | int       | ToInt(x) ^ ToInt(y)   |
| float | str   | int       | _See below_           |
| str   | int   | str       | _See below_           |
| str   | float | str       | _See below_           |
| str   | str   | str       | _See below_           |
| list  | _any_ | list      | distributive          |

TypeError raised on all other combinations

*String operations*

```vgr
"frog" ^ 3 → "eqld"
"frog" ^ 3.14 → "eqld"
"frog" ^ "1" → "gsnf"
"frog" ^ "1".Ord() → "WC^V"
"frog" ^ "o" → "\\t\\x1d\\x00\\x08"
"frog" ^ "_" → "9-08"
["frog", "BOG"].BitXor(" ") → ["FROG", "bog"]
```

Also see `BitAnd()` and `BitOr()`
"""
    return reduce(_bit_xor, args, x)

def poly_bit_not(x: Any) -> Any:
    """
**Bitwise invert (negation) operation**

* BitNot(_value_)
* _value_.BitNot()

Returns the shortest length bitwise negation, in multiples of eight bits,
for a numeric value.

```vgr
None.BitNot() → None
5.BitNot().ToBinary() → "0b11111010"
511.BitNot().ToBinary() → "0b1111111000000000"
"5".BitNot().ToBinary() → "0b11111010"
"5".Ord().BitNot().ToBinary() → "0b11001010"
[1, 2].Ord().BitNot().ToBinary() → ["0b11111110", "0b11111101"]
```

Also see `BitXor()`
"""
    if x is None: return None
    operation = _bit_operations.get((type(x), int))
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

def _str_num_op(op: Callable[[Any, Any], Any], x: str, y: Any) -> Any:
    # TODO see if this is still useful...
    """See if the string can be converted to a number before applying the operation"""
    y_int = int(y)
    try:
        return op(int(str_to_number(x)), y_int)
    except ValueError:
        return _int_str_op(op, y_int, x)

def _int_str_op(op: Callable[[Any, Any], Any], x: int, y: str) -> str:
    """The operation is distributed over the characters in the string"""
    return ''.join(chr(op(ord(c), x)) for c in y)

def _coerce_str_to_int(x: Any) -> Any:
    """
    See if the value is a string tha can be made into
    a number. If it can't, we'll use the string value.
    """
    if isinstance(x, str):
        try:
            n = str_to_number(x)
            if n is not None: return int(n)
        except ValueError:
            pass
    return x

def _str_str_op(op: Callable[[Any, Any], Any], x: str, y: str) -> str:
    y_bytes = y.encode()
    y_len = len(y_bytes)
    return ''.join(chr(op(ord(c), y_bytes[i % y_len])) for i, c in enumerate(x))

def _bit_and(x: Any, y: Any) -> Any:
    x = _coerce_str_to_int(x)
    y = _coerce_str_to_int(y)
    operation = get_operation(x, y, _bit_operations)
    return operation(_bit_and, x, y) if operation else x & y

def _bit_or(x: Any, y: Any) -> Any:
    x = _coerce_str_to_int(x)
    y = _coerce_str_to_int(y)
    operation = get_operation(x, y, _bit_or_operations, _bit_operations)
    return operation(_bit_or, x, y) if operation else x | y

def _bit_xor(x: Any, y: Any) -> Any:
    x = _coerce_str_to_int(x)
    y = _coerce_str_to_int(y)
    operation = get_operation(x, y, _bit_operations)
    return operation(_bit_xor, x, y) if operation else x ^ y

# pylint: disable=arguments-out-of-order
_bit_operations = {
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
_bit_or_operations = {
    (list, list): lambda _, x, y: x + y,
    (list, tuple): lambda _, x, y: x + list(y),
    (tuple, list): lambda _, x, y: x + tuple(y),
    (tuple, tuple): lambda _, x, y: x + y,
    (dict, dict): lambda _, x, y: {**x, **y},
}
