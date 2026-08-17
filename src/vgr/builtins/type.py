
from typing import Any
import re

from .registry import builtin

from ..vgr_callable import VgrCallable

@builtin("Type")
def poly_type(x: Any=None) -> str:
    """
**Return the internal data type of an item**

* Type(*value*)
* *value*.Type()

For `None` the value *none* is returned.

```vgr
None.Type() → "none"
"five".Type() → "string"
True.Type() → "boolean"
5.Type() → "integer"
5.0.Type() → "float"
CompilePattern("[abc]").Type() → "pattern"
["five", 5, 5.0].Type() → "list"
{"One": 1, "Two": 2}.Type() → "dictionary"

Function f(x) -> x+2
f.Type() -> "function"
```

Also see `IsNone()`, `IsBoolean()`, `IsDictionary()`, `IsInteger()`,
`IsFloat()`, `IsNumber()`, `IsPattern()`,
`IsString()`, and `IsFunction()`.
"""
    if x is None: return 'none'
    if isinstance(x, bool): return 'boolean'
    if isinstance(x, dict): return 'dictionary'
    if isinstance(x, int): return 'integer'
    if isinstance(x, re.Pattern): return 'pattern'
    if isinstance(x, str): return 'string'
    if isinstance(x, VgrCallable): return 'function'
    if callable(x) and not isinstance(x, type): return poly_type(x())
    return (x if isinstance(x, type) else type(x)).__name__
