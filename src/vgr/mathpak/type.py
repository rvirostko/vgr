
from typing import Any
import re

from ..vgr_callable import VgrCallable

def poly_type(x: Any) -> str:
    """
**Return the internal data type of an item**

* Type(_value_)
* _value_.Type()

For _None_ the value _none_ is returned.

```vgr
None.Type() → "none"
"five".Type() → "string"
True.Type() → "boolean"
5.Type() → "integer"
5.0.Type() → "float"
CompilePattern("[abc]").Type() → "pattern"
["five", 5, 5.0].Type() → "list"
{"One": 1, "Two": 2}.Type() → "dictionary"

Set f(x) -> x+2
f.Type() -> "function"
```
"""
    if x is None: return 'none'
    if isinstance(x, bool): return 'boolean'
    if isinstance(x, dict): return 'dictionary'
    if isinstance(x, int): return 'integer'
    if isinstance(x, re.Pattern): return 'pattern'
    if isinstance(x, str): return 'string'
    if isinstance(x, VgrCallable): return 'function'
    return (x if isinstance(x, type) else type(x)).__name__
