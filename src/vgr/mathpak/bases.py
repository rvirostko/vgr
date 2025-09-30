"""
Functions for converting numbers to non base10 representations and back again
"""

from typing import Any
import base64

from .common import type_str, NoneType
from .types import poly_int

def poly_bin(x: Any) -> Any:
    """
**Convert an integer number to a binary string prefixed with “0b”**

* _value_.ToBinary()

Distributed across all collections except dictionaries.

```vgr
None.ToBinary() → None
5.ToBinary() → "0b101"
5.1.ToBinary() → "0b101"
"5".ToBinary() → "0b101"
[5, 6.0, "7"].ToBinary() → ["0b101", "0b110", "0b111"]
[True, False].ToBinary() → ["0b1", "0b0"]
```

Also see `ToOctal()` and `ToHex()`
"""
    if x is None: return None
    if isinstance(x, (bool, int, float)): return bin(int(x))
    if isinstance(x, str): return bin(poly_int(x))
    if isinstance(x, (list, tuple)): return type(x)(poly_bin(x1) for x1 in x)
    raise TypeError(f'Binary format with {type_str(x)} not supported')

def poly_oct(x: Any) -> Any:
    """
**Convert an integer number to an octal string prefixed with “0o”**

* _value_.ToOctal()

Distributed across all collections except dictionaries.

```vgr
None.ToOctal() → None
5.ToOctal() → "0o5"
5.1.ToOctal() → "0o5"
"5".ToOctal() → "0o5"
[5, 6.0, "7"].ToOctal() → ["0o5", "0o6", "0o7"]
[True, False].ToOctal() → ["0o1", "0o0"]
```

Also see `ToBinary()` and `ToHex()`
"""
    if x is None: return None
    if isinstance(x, (bool, int, float)): return oct(int(x))
    if isinstance(x, str): return oct(poly_int(x))
    if isinstance(x, (list, tuple)): return type(x)(poly_oct(x1) for x1 in x)
    raise TypeError(f'Octal format with {type_str(x)} not supported')

def poly_hex(x: Any) -> Any:
    """
**Convert an integer number to a hexadecimal string prefixed with “0x”**

* _value_.ToHex()

Distributed across all collections except dictionaries.

```vgr
None.ToHex() → None
5.ToHex() → "0x5"
5.1.ToHex() → "0x5"
"5".ToHex() → "0x5"
[5, 6.0, "7"].ToHex() → ["0x5", "0x6", "0x7"]
[True, False].ToHex() → ["0x1", "0x0"]
```

Also see `ToBinary()` and `ToOctal()`
"""
    if x is None: return None
    if isinstance(x, (bool, int, float)): return hex(int(x))
    if isinstance(x, str): return hex(poly_int(x))
    if isinstance(x, (list, tuple)): return type(x)(poly_hex(x1) for x1 in x)
    raise TypeError(f'Hexadecimal format with {type_str(x)} not supported')

def poly_parse_int(x: Any, base: Any=10) -> Any:
    """
**Convert a non-numeric value into an integer**

* _value_.ParseInt()
* _value_.ParseInt(_base_)

The default base is decimal.

```vgr
None.ParseInt() → None
"".ParseInt() → None
" ".ParseInt() → None
"5".ParseInt() → 5
5.ParseInt() → 5
5.1.ParseInt() → 5
[5, 6.0, "7"].ParseInt() → [5, 6, 7]
[True, False].ParseInt() → [1, 0]
" -7 ".ParseInt() → -7
"111".ParseInt(2) → 7
"177".ParseInt(8) → 127
"C4".ParseInt(16) → 196
" 24 ".ParseInt(5) → 14
```

Also see `ParseBinary()`, `ParseOctal()`, `ParseHex()`
"""
    if x is None: return None
    if isinstance(x, (bool, int, float)): return int(x)
    if isinstance(x, str):
        try:
            return None if len(x) == 0 or x.isspace() else int(x.strip(), base)
        except ValueError as e:
            raise ValueError(f'Invalid value for use with base {base}: {x!r}') from e
    if isinstance(x, (list, tuple)): return type(x)(poly_parse_int(x1, base) for x1 in x)
    raise TypeError(f'Parsing from {type_str(x)} not supported')

def poly_parse_bin(x: Any) -> Any:
    """
**A specialized version of `ParseInt()` for base 2**

* _value_.ParseBinary()

```vgr
None.ParseBinary() → None
"".ParseBinary() → None
" ".ParseBinary() → None
5.ParseBinary() → 5
5.1.ParseBinary() → 5
[5, 6.0, "111"].ParseBinary() → [5, 6, 7]
[True, False].ParseBinary() → [1, 0]
" -111 ".ParseBinary() → -7
"111".ParseBinary() → 7
```

Also see `ParseInt()`
"""
    return poly_parse_int(x, 2)

def poly_parse_oct(x: Any) -> Any:
    """
**A specialized version of `ParseInt()` for base 8**

* _value_.ParseOctal()

```vgr
None.ParseOctal() → None
"".ParseOctal() → None
" ".ParseOctal() → None
"5".ParseOctal() → 5
5.ParseOctal() → 5
5.1.ParseOctal() → 5
[5, 6.0, "7"].ParseOctal() → [5, 6, 7]
[True, False].ParseOctal() → [1, 0]
" -177 ".ParseOctal() → -127
"177".ParseOctal() → 127
```

Also see `ParseInt()`
"""
    return poly_parse_int(x, 8)

def poly_parse_hex(x: Any) -> Any:
    """
**A specialized version of `ParseInt()` for base 16**

* _value_.ParseHex()

```vgr
None.ParseHex() → None
"".ParseHex() → None
" ".ParseHex() → None
"5".ParseHex() → 5
5.ParseHex() → 5
5.1.ParseHex() → 5
[8, 9.0, "A"].ParseHex() → [8, 9, 10]
[True, False].ParseHex() → [1, 0]
" -9F ".ParseHex() → -159
"9F".ParseHex() → 159
```

Also see `ParseInt()`
"""
    return poly_parse_int(x, 16)

def poly_base64_encode(x: Any, charset: str = "utf-8") -> Any:
    """
**Encode a string using base 64 encoding**

* _value_.Base64Encode()
* _value_.Base64Encode(_charset_)

The default _charset_ is UTF-8.

```vgr
None.Base64Encode() → None
"".Base64Encode() → ""
" ".Base64Encode() → "IA=="
"5".Base64Encode() → "NQ=="
5.Base64Encode() → "NQ=="
5.1.Base64Encode() → "NS4x"
[5, 6.0, "7"].Base64Encode() → ["NQ==", "Ni4w", "Nw=="]
[True, False].Base64Encode() → ["MQ==", "MA=="]
```

Also see `Base64Decode()`
"""
    if x is None: return None
    if isinstance(x, (list, tuple)): return type(x)(poly_base64_encode(x1, charset) for x1 in x)
    if isinstance(x, bool): x = str(int(x))
    if isinstance(x, (int, float)): x = str(x)
    if isinstance(x, str): return base64.b64encode(x.encode()).decode(_check_charset(charset))
    raise TypeError(f'Base64 encoding of {type_str(x)} not supported')

def poly_base64_decode(x: Any, charset: str = "utf-8") -> Any:
    """
**Decode a string using base 64 encoding**

* _value_.Base64Decode()
* _value_.Base64Decode(_charset_)

The default _charset_ is UTF-8.

```vgr
None.Base64Decode() → None
"".Base64Decode() → ""
" ".Base64Decode() → ""
5.Base64Decode() → 5
5.1.Base64Decode() → 5.1
"SGVsbG8=".Base64Decode() → "Hello"
"\\tSGVsbG8=\\n".Base64Decode() → "Hello"
["MQ==", "MA=="].Base64Decode().ToBool() → [True, False]
```

Also see `Base64Encode()`
"""
    if x is None: return None
    if isinstance(x, (bool, int, float)): return x
    if isinstance(x, (list, tuple)): return type(x)(poly_base64_decode(x1, charset) for x1 in x)
    if isinstance(x, str):
        x = x.strip()
        return '' if not x else base64.b64decode(x).decode(_check_charset(charset))
    raise TypeError(f'Base64 decoding of {type_str(x)} not supported')

def poly_hex_encode(x: Any, charset: str = "utf-8") -> str:
    """
**Encode a string as a series of hexidecimal characters**

* _value_.HexEncode()
* _value_.HexEncode(_charset_)

The default _charset_ is UTF-8.

```vgr
None.HexEncode() → None
"".HexEncode() → ""
" ".HexEncode() → "20"
5.HexEncode() → "35"
5.1.HexEncode() → "352e31"
"Hello".HexEncode() → "48656c6c6f"
[True, False].HexEncode() → ["31", "30"]
```

Also see `HexDecode()`
"""
    if x is None: return None
    if isinstance(x, (list, tuple)): return type(x)(poly_hex_encode(x1, charset) for x1 in x)
    if isinstance(x, bool): x = str(int(x))
    if isinstance(x, (int, float)): x = str(x)
    if isinstance(x, str): return x.encode(_check_charset(charset)).hex()
    raise TypeError(f'Hex encoding of {type_str(x)} not supported')

def poly_hex_decode(x: Any, charset: str = "utf-8") -> str:
    """
**Decode a string of hexidecimal characters into a string**

* _value_.HexDecode()
* _value_.HexDecode(_charset_)

The default _charset_ is UTF-8.

```vgr
None.HexDecode() → None
"".HexDecode() → ""
" ".HexDecode() → ""
5.HexDecode() → 5
5.1.HexDecode() → 5.1
"48656c6c6f".HexDecode() → "Hello"
"\\t48656c6c6f\\n".HexDecode() → "Hello"
["31", "30"].HexDecode().ToBool() → [True, False]
```

Also see `HexEncode()`
"""
    # Idempotentent for these types
    if isinstance(x, (NoneType, bool, int, float)): return x
    if isinstance(x, (list, tuple)): return type(x)(poly_hex_decode(x1, charset) for x1 in x)
    if isinstance(x, str):
        x = x.strip()
        return '' if not x else bytes.fromhex(x).decode(_check_charset(charset))
    raise TypeError(f'Hex decoding of {type_str(x)} not supported')

def _check_charset(charset: str) -> str:
    """Validate charset name, raising error if not known."""
    if not charset:
        charset = "utf-8"
    else:
        if not isinstance(charset, str):
            raise TypeError(f'Expected string for charset, found {type_str(charset)}')
        charset = charset.strip()
        if not charset: charset = "utf-8"
    try:
        # Just attempt a lookup — doesn't do conversion yet
        ''.encode(charset)
        return charset
    except LookupError as e:
        raise ValueError(f'Invalid charset {charset!r}') from e
