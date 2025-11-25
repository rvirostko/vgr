from functools import reduce
from typing import Any, Callable

from .common import (
    bound_ops,
    dist_x,
    dist_y,
    get_operation,
    int_arg,
    str_to_number,
    X_None_Op,
    Y_None_Op,
)

from .types import poly_bool

_MAX_BITS = 256
_MAX_BIT_INDEX = _MAX_BITS - 1

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

def poly_set_bit(x: Any, index: int, do_set: bool=True) -> Any:
    """
**Set bit at an index to one**

* SetBit(_value_, _index_[, _set_])
* _value_.SetBit(_index_[, _set_])

The optional _set_ argument is interpreted as a boolean, indicating if the
bit at the given index should be set to one (_True_) or zero (_False_).
The default is _True_, setting the bit to one.

```vgr
None.SetBit(2).ToBinary() → None
1.SetBit(2).ToBinary() → 0b101
Ord("Hello").SetBit(5).Chr().Join() → "hello"
{"a": 5}.SetBit(7) → {"a": 5}
```

Also see `ClearBit()` and `ToggleBit()`
"""
    if x is None: return None
    index = _clamp_bit_param(int_arg(index, "Index"), _MAX_BIT_INDEX)
    if isinstance(x, list): return list(poly_set_bit(x1, index) for x1 in x)
    if isinstance(x, str): x = str_to_number(x)
    if isinstance(x, (int, float)):
        return int(x) | (1 << index) if poly_bool(do_set) else int(x) & ~(1 << index)
    return x

def poly_clear_bit(x: Any, index: int) -> Any:
    """
**Set bit at an index to zero**

* ClearBit(_value_, _index_)
* _value_.ClearBit(_index_)

```vgr
None.ClearBit(2).ToBinary() → None
5.ClearBit(2).ToBinary() → 0b1
Ord("Hello").ClearBit(5).Chr().Join() → "HELLO"
{"a": 5}.ClearBit(7) → {"a": 5}
```

Also see `SetBit()` and `ToggleBit()`
"""
    if x is None: return None
    index = _clamp_bit_param(int_arg(index, "Index"), _MAX_BIT_INDEX)
    if isinstance(x, list): return list(poly_clear_bit(x1, index) for x1 in x)
    if isinstance(x, str): x = str_to_number(x)
    if isinstance(x, (int, float)): return int(x) & ~(1 << index)
    return x

def poly_toggle_bit(x: Any, index: int) -> Any:
    """
** Reverse the setting of the bit at an index**

* ToggleBit(_value_, _index_)
* _value_.ToggleBit(_index_)

```vgr
None.ToggleBit(2).ToBinary() → None
1.ToggleBit(2).ToBinary() → 0b101
Ord("Hello").ToggleBit(5).Chr().Join() → "hELLO"
{"a": 5}.ToggleBit(7) → {"a": 5}
```

Also see `SetBit()` and `ClearBit()`
"""
    if x is None: return None
    index = _clamp_bit_param(int_arg(index, "Index"), _MAX_BIT_INDEX)
    if isinstance(x, list): return list(poly_toggle_bit(x1, index) for x1 in x)
    if isinstance(x, str): x = str_to_number(x)
    if isinstance(x, (int, float)): return int(x) ^ (1 << index)
    return x

def poly_test_bit(x: Any, index: int):
    """
**Return _True_ if the bit at index is one**

* IsBitSet(_value_, _index_)
* _value_.IsBitSet(_index_)

```vgr
None.IsBitSet(2) → False
5.IsBitSet(2) → True
Ord("Hello").IsBitSet(5) → [False, True, True, True, True]
{"a": 5}.IsBitSet(7) → {"a": 5}
```

Also see `SetBit()`, `ClearBit()`, and `ToggleBit()`
"""
    if x is None: return False
    index = _clamp_bit_param(int_arg(index, "Index"), _MAX_BIT_INDEX)
    if isinstance(x, list): return list(poly_test_bit(x1, index) for x1 in x)
    if isinstance(x, str): x = str_to_number(x)
    if isinstance(x, (int, float)): return ((int(x) >> index) & 1) == 1
    return x

def poly_count_ones(x: Any):
    """
**Return the number of one bits in a value**

* CountOneBits(_value_)
* _value.CountOneBits()

```vgr
None.CountOneBits() → 0
5.CountOneBits() → 2
Ord("Hello").CountOneBits() → [2, 4, 4, 4, 6]
{"a": 5}.CountOneBits() → {"a": 5}
```

Also see `CountZeroBits()`
"""
    if x is None: return 0
    if isinstance(x, list): return list(poly_count_ones(x1) for x1 in x)
    if isinstance(x, str): x = str_to_number(x)
    if isinstance(x, (int, float)): return _bit_count(int(x))
    return x

def poly_count_zeros(x: Any, width: int):
    """
**Return the number of zero bits in a value, treating it as being _width_ bits long**

* CountZeroBits(_value_, _width_)
* _value.CountZeroBits(_width_)

```vgr
None.CountZeroBits(8) → 0
5.CountZeroBits(8) → 6
Ord("Hello").CountZeroBits(8) → [6, 4, 4, 4, 2]
{"a": 5}.CountZeroBits(8) → {"a": 5}
```

Also see `CountLeadingZeroBits()`, `CountTrailingZeroBits()`, and `CountOneBits()`
"""
    if x is None: return 0
    width: int = _clamp_bit_param(int_arg(width, "Width"), _MAX_BITS)
    if isinstance(x, list): return list(poly_count_zeros(x1, width) for x1 in x)
    if isinstance(x, str): x = str_to_number(x)
    if isinstance(x, (int, float)): return width - _bit_count((int(x) & ((1 << width) - 1)))
    return x

def poly_count_leading_zeros(x: Any, width: int):
    """
**Return the number of _leading_ zero bits in a value, treating it as being _width_ bits long**

* CountLeadingZeroBits(_value_, _width_)
* _value.CountLeadingZeroBits(_width_)

```vgr
None.CountLeadingZeroBits(8) → 0
5.CountLeadingZeroBits(8) → 5
Ord("Hello").CountLeadingZeroBits(8) → [1, 1, 1, 1, 1]
{"a": 5}.CountLeadingZeroBits(8) → {"a": 5}
```

Also see `CountZeroBits()`, `CountTrailingZeroBits()`, and `CountOneBits()`
"""
    if x is None: return 0
    width: int = _clamp_bit_param(int_arg(width, "Width"), _MAX_BITS)
    if isinstance(x, list): return list(poly_count_leading_zeros(x1, width) for x1 in x)
    if isinstance(x, str): x = str_to_number(x)
    if isinstance(x, (int, float)):
        masked = int(x) & ((1 << width) - 1)
        return width if masked == 0 else width - masked.bit_length()
    return x

def poly_count_trailing_zeros(x: Any):
    """
**Return the number of _trailing_ zero bits in a value**

* CountTrailingZeroBits(_value_)
* _value.CountTrailingZeroBits()

```vgr
None.CountTrailingZeroBits() → 0
5.CountTrailingZeroBits() → 0
Ord("Hello").CountTrailingZeroBits() → [3, 0, 2, 2, 0]
{"a": 5}.CountTrailingZeroBits() → {"a": 5}
```

Also see `CountZeroBits()`, `CountLeadingZeroBits()`, and `CountOneBits()`
"""
    if x is None: return 0
    if isinstance(x, list): return list(poly_count_trailing_zeros(x1) for x1 in x)
    if isinstance(x, str): x = str_to_number(x)
    if isinstance(x, (int, float)):
        x: int = int(x)
        return 0 if x == 0 else (x & -x).bit_length() - 1
    return x

def poly_highest_one_bit(x: Any):
    """
**Return a value with only its most significant one bit preserved**

* HighestOneBit(_value_)
* _value_.HighestOneBit()

```vgr
None.HighestOneBit() → None
5.HighestOneBit() → 4
Ord("Hello").HighestOneBit() → [64, 64, 64, 64, 64]
{"a": 5}.HighestOneBit() → {"a": 5}
```

Also see `LowestOneBit()`
"""
    if x is None: return None
    if isinstance(x, list): return list(poly_highest_one_bit(x1) for x1 in x)
    if isinstance(x, str): x = str_to_number(x)
    if isinstance(x, (int, float)):
        x: int = int(x)
        return 0 if x == 0 else 1 << (x.bit_length() - 1)
    return x

def poly_lowest_one_bit(x: Any):
    """
**Return a value with only its least significant one bit preserved**

* LowestOneBit(_value_)
* _value_.LowestOneBit()

```vgr
None.LowestOneBit() → None
5.LowestOneBit() → 1
Ord("Hello").LowestOneBit() → [8, 1, 4, 4, 1]
{"a": 5}.LowestOneBit() → {"a": 5}
```

Also see `HighestOneBit()`
"""
    if x is None: return None
    if isinstance(x, list): return list(poly_lowest_one_bit(x1) for x1 in x)
    if isinstance(x, str): x = str_to_number(x)
    if isinstance(x, (int, float)):
        x: int = int(x)
        return x & -x
    return x

def poly_rotate_left(x: Any, count: int, width: int):
    """
**Rotate right by _count_ bits within a unsigned space of _width_ bits**

* RotateLeft(_value_, _count_, _width_)
* _value_.RotateLeft(_count_, _width_)

```vgr
None.RotateLeft(2, 8) → None
5.RotateLeft(2, 8).ToBinary() → 0b10100
Ord("Hello").RotateLeft(2, 8) → [33, 149, 177, 177, 189]
{"a": 5}.RotateLeft(2, 8) → {"a": 5}
```

Also see `RotateLeft()` and `LeftShift()`
    """
    if x is None: return None
    count: int = int_arg(count, "Count")
    width: int = _clamp_bit_param(int_arg(width, "Width"), _MAX_BITS)
    if isinstance(x, list): return list(poly_rotate_left(x1, count, width) for x1 in x)
    if isinstance(x, str): x = str_to_number(x)
    if isinstance(x, (int, float)):
        mask = (1 << width) - 1
        d = count % width
        x: int = int(x)
        return ((x << d) | (x >> (width - d))) & mask
    return x

def poly_rotate_right(x: Any, count: int, width: int):
    """
**Rotate right by _count_ bits within a unsigned space of _width_ bits**

* RotateRight(_value_, _count_, _width_)
* _value_.RotateRight(_count_, _width_)

```vgr
None.RotateRight(2, 8) → None
5.RotateRight(2, 8).ToBinary() → 0b1000001
Ord("Hello").RotateRight(2, 8) → [18, 89, 27, 27, 219]
{"a": 5}.RotateRight(2, 8) → {"a": 5}
```

Also see `RotateLeft()` and `RightShift()`
"""
    if x is None: return None
    count: int = int_arg(count, "Count")
    width: int = _clamp_bit_param(int_arg(width, "Width"), _MAX_BITS)
    if isinstance(x, list): return list(poly_rotate_right(x1, count, width) for x1 in x)
    if isinstance(x, str): x = str_to_number(x)
    if isinstance(x, (int, float)):
        mask = (1 << width) - 1
        d = count % width
        x: int = int(x)
        return ((x >> d) | (x << (width - d))) & mask
    return x

def poly_reverse_bits(x: Any, width: int):
    """
**Reverse the order of bits within an unsigned space of _width_ bits**

* ReverseBits(_value_, _width_)
* _value_.ReverseBits(_width_)

```vgr
None.ReverseBits(8) → None
5.ReverseBits(8).ToBinary() → 0b10100000
Ord("ABC").ReverseBits(4).ToBinary() → ["0b1000", "0b100", "0b1100"]
{"a": 5}.ReverseBits(8) → {"a": 5}
```

Also see `ReverseBytes()`
"""
    if x is None: return None
    width: int = _clamp_bit_param(int_arg(width, "Width"), _MAX_BITS)
    if isinstance(x, list): return list(poly_reverse_bits(x1, width) for x1 in x)
    if isinstance(x, str): x = str_to_number(x)
    if isinstance(x, (int, float)):
        x: int = int(x)
        r = 0
        for i in range(width):
            r = (r << 1) | ((x >> i) & 1)
        return r
    return x

def poly_reverse_bytes(x: Any, width: int):
    """
**Swaps byte order for correct interpretation
when moving between big-endian and little-endian architectures, protocols, or file formats**

* ReverseBytes(_value_, _width_)
* _value_.ReverseBytes(_width_)

_width_ must be a multiple of eight

```vgr
None.ReverseBytes(32) → None
0x01020304.ReverseBytes(32).ToHex() → 0x4030201
{"a": 5}.ReverseBytes(32) → {"a": 5}
```

Also see `ReverseBits()`
"""
    if x is None: return None
    width = _clamp_bit_param(int_arg(width, "Width"), _MAX_BITS)
    if isinstance(x, list): return list(poly_reverse_bytes(x1, width) for x1 in x)
    if isinstance(x, str): x = str_to_number(x)
    if isinstance(x, (int, float)):
        byte_count = width // 8
        v = int(x) & (1 << width) - 1
        result = 0
        for i in range(byte_count):
            result = (result << 8) | ((v >> (8 * i)) & 0xFF)
        return result
    return x

def poly_set_bits(x: Any, bits: int, start: int, width: int) -> Any:
    """
**Sets one or more bits at a specific location in a value**

* SetBits(_value_, _bits_, _start_, _width_)
* _value.SetBits(_bits_, _start_, _width_)

_bits_ is the new value which will be set in the _value_.
_start_ is the starting bit in value with zero being the least significant bit.
Values up to 256 bits long are supported.

If a single bit is being changed, it is better to use `SetBit()` or `ClearBit()`.

```vgr
None.SetBits(1, 0, 1) → None
0xEE55.SetBits(0, 15, 8).ToHex() → 0x55
0xEE55.SetBits(255, 7, 8).ToHex() → 0xeeff
Ord("ABC").SetBits(3, 6, 2).Chr() → ["a", "b", "c"]
{"a": 5}.SetBits(31, 5, 4) → {"a": 5}
```

Also see `SetBit()`, `ClearBit()`, and `ExtractBits()`
"""
    if x is None: return None
    bits = int_arg(bits, "Bits")
    start = _clamp_bit_param(int_arg(start, "Start"), _MAX_BIT_INDEX)
    width = min(_clamp_bit_param(int_arg(width, "Width"), _MAX_BITS), start + 1)
    if width == 0: return 0
    if isinstance(x, list): return list(poly_set_bits(x1, bits, start, width) for x1 in x)
    if isinstance(x, str): x = str_to_number(x)
    if isinstance(x, (int, float)):
        # Mask for the number of bits being manipulated
        mask = (1 << width) - 1
        shift_count = (start + 1) - width
        # Clear target bits in original value
        x = int(x) & ~(mask << shift_count)
        if bits != 0:
            # Adjust replacement to the correct length and location and combine
            x = x | ((bits & mask) << shift_count)
        return x
    return x

def poly_extract_bits(x: Any, start: int, width: int) -> Any:
    """
**Extracts one or more bits at a specific location in a value**

* ExtractBits(_value_, _start_, _width_)
* _value.ExtractBits(_start_, _width_)

_start_ is the starting bit in value with zero being the least significant bit.
Values up to 256 bits long are supported.

If a single bit is being extracted, it is better to use `TestBit()`.

```vgr
None.ExtractBits(0, 1) → None
0xEE55.ExtractBits(15, 8).ToHex() → 0xee
0xEE55.ExtractBits(7, 8).ToHex() → 0x55
Ord("123").ExtractBits(3, 4).ToInt() → [1, 2, 3]
{"a": 5}.ExtractBits(3, 4) → {"a": 5}
```

Also see `SetBits()` and `TestBit()`
"""
    if x is None: return None
    start = _clamp_bit_param(int_arg(start, "Start"), _MAX_BIT_INDEX)
    width = min(_clamp_bit_param(int_arg(width, "Width"), _MAX_BITS), start + 1)
    if width == 0: return 0
    if isinstance(x, list): return list(poly_extract_bits(x1, start, width) for x1 in x)
    if isinstance(x, str): x = str_to_number(x)
    if isinstance(x, (int, float)):
        x = int(x)
        if x == 0: return 0
        mask = (1 << width) - 1
        shift_count = (start + 1) - width
        # shift value down and mask off desired bits
        return (x >> shift_count) & mask
    return x

def _clamp_bit_param(value: int, max_value: int) -> int:
    """Clamp bit index or bit length into the inclusive range [0, 256]."""
    return 0 if value < 0 else max_value if value > max_value else value

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
    See if the value is a string that can be made into
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

def _bit_count(x: int) -> int:
    if hasattr(int, 'bit_count'):
        # bit_count() returns number of ones in absolute value for negative ints;
        # but when masked (unsigned semantics) value is non-negative.
        return x.bit_count()
    # fallback: convert to binary string and count '1'
    return bin(abs(x)).count('1')

# pylint: disable=arguments-out-of-order
_bit_operations = {
    X_None_Op: lambda op, _, y: None if y is None else op(0, y),
    Y_None_Op: lambda op, x, _: op(x, 0),
    (int, float): lambda op, x, y: op(x, int(y)),
    (int, str): lambda op, x, y: _str_num_op(op, y, x),
    (int, list): dist_y,
    (float, int): lambda op, x, y: op(int(x), y),
    (float, float): lambda op, x, y: op(int(x), int(y)),
    (float, str): lambda op, x, y: _str_num_op(op, y, x),
    (float, list): lambda op, x, y: op(int(x), y),
    (str, int): _str_num_op,
    (str, float): _str_num_op,
    (str, str): _str_str_op,
    (str, list): dist_y,
    (list, int): dist_x,
    (list, float): dist_x,
    (list, str): dist_x,
}
# pylint: enable=arguments-out-of-order

# Collection-to-collection "or" combines contents
_bit_or_operations = {
    (list, list): lambda _, x, y: x + y,
    (dict, dict): lambda _, x, y: {**x, **y},
}
