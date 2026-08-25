from typing import Any
from re import Pattern

from .registry import builtin

@builtin("Ord")
def poly_ord(*args) -> Any:
    """
**Convert a string to its ordinal values**

* Ord(*value*)
* *value*.Ord()

If *value* is a single character, the ordinal is returned; for an multi-character
string, an array of ordinals are returned.
The operation is distributed across lists and dictionaries.

```vgr
"5".Ord() → 53
5.Ord() → 5
"cat".Ord() → [99, 97, 116]
["cat", "dog"].Ord() → [[99, 97, 116], [100, 111, 103]]
```

Also see `Chr()`
"""
    x = None if len(args) == 0 else args[0] if len(args) == 1 else list(args)
    if x is None: return None
    if isinstance(x, (int, float)): return int(x) if 0 <= x <= 0x10FFFF else x
    if isinstance(x, str): return ord(x) if len(x) == 1 else [poly_ord(x1) for x1 in x]
    if isinstance(x, list): return list(poly_ord(el) for el in x)
    if isinstance(x, dict): return {k: poly_ord(v) for k, v in x.items()}
    return x
