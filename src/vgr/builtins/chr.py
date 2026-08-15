from typing import Any

from .registry import builtin

@builtin("Chr")
def poly_chr(x: Any=None) -> Any:
    """
**Convert a number to a single character string**

* Chr(*value*)
* *value*.Chr()

If *value* is a value for a Unicode character a single character string
is returned.
The operation is distributed across lists and dictionaries.

```vgr
99.Chr() → "c"
print [99, 97, 116].Chr() → ["c", "a", "t"]
```

Also see `Ord()`
"""
    if x is None: return None
    if isinstance(x, (int, float)): return chr(int(x)) if 0 <= x <= 0x10FFFF else x
    if isinstance(x, (bytes, bytearray)): return ''.join(chr(b) for b in x)
    if isinstance(x, list): return list(poly_chr(x1) for x1 in x)
    if isinstance(x, dict): return {k: poly_chr(v) for k, v in x.items()}
    return x
