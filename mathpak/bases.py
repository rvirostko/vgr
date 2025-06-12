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

Distributed across all collections except dictionaries.
"""
    if x is None: return None
    if isinstance(x, (bool, int, float)): return bin(int(x))
    if isinstance(x, str): return bin(poly_int(x))
    if isinstance(x, (list, tuple)): return type(x)(poly_bin(x1) for x1 in x)
    raise TypeError(f'Binary format with {type_str(x)} not supported')

def poly_oct(x: Any) -> Any:
    """
**Convert an integer number to an octal string prefixed with “0o”**

Distributed across all collections except dictionaries.
"""
    if x is None: return None
    if isinstance(x, (bool, int, float)): return oct(int(x))
    if isinstance(x, str): return oct(poly_int(x))
    if isinstance(x, (list, tuple)): return type(x)(poly_oct(x1) for x1 in x)
    raise TypeError(f'Octal format with {type_str(x)} not supported')

def poly_hex(x: Any) -> Any:
    """
**Convert an integer number to a hexadecimal string prefixed with “0x”**

Distributed across all collections except dictionaries.
"""
    if x is None: return None
    if isinstance(x, (bool, int, float)): return hex(int(x))
    if isinstance(x, str): return hex(poly_int(x))
    if isinstance(x, (list, tuple)): return type(x)(poly_hex(x1) for x1 in x)
    raise TypeError(f'Hexadecimal format with {type_str(x)} not supported')

def poly_parse_int(x: Any, base: Any=10) -> Any:
    if x is None: return None
    if isinstance(x, (bool, int, float)): return int(x)
    if isinstance(x, str):
        try:
            return None if len(x) == 0 or x.isspace() else int(x.strip(), base)
        except ValueError as e:
            raise ValueError(f'Invalid value for use with base {base}: {repr(x)}') from e
    if isinstance(x, (list, tuple)): return type(x)(poly_parse_int(x1, base) for x1 in x)
    raise TypeError(f'Parsing from {type_str(x)} not supported')

def poly_parse_bin(x: Any) -> Any:
    return poly_parse_int(x, 2)

def poly_parse_oct(x: Any) -> Any:
    return poly_parse_int(x, 8)

def poly_parse_hex(x: Any) -> Any:
    return poly_parse_int(x, 16)

def poly_base64_encode(x: Any) -> Any:
    # Idempotentent for these types
    if isinstance(x, (NoneType, bool, int, float)): return x
    if isinstance(x, str): return base64.b64encode(x.encode()).decode('ascii')
    if isinstance(x, (list, tuple)): return type(x)(poly_base64_encode(x1) for x1 in x)
    raise TypeError(f'Base64 encoding of {type_str(x)} not supported')

def poly_base64_decode(x: Any) -> Any:
    # Idempotentent for these types
    if isinstance(x, (NoneType, bool, int, float)): return x
    if isinstance(x, str): return base64.b64decode(x)
    if isinstance(x, (list, tuple)): return type(x)(poly_base64_decode(x1) for x1 in x)
    raise TypeError(f'Base64 decoding of {type_str(x)} not supported')
