from typing import Any

from .as_str import as_str
from .common import bool_arg
from .registry import builtin
from .type import poly_type

@builtin("SplitLines")
def poly_split_lines(x: Any=None, keepends: bool=False) -> Any:
    """
**Split a string into multiple lines**

* SplitLines(*value*)
* SplitLines(*value*, *keepends*)
* *value*.SplitLines()
* *value*.SplitLines(*keepends*)

```vgr
None.SplitLines() → None
"".SplitLines() → []
"One\\nTwo".SplitLines() → ["One", "Two"]
"One\\nTwo".SplitLines(True) → ["One\\n", "Two"]
```
"""
    if x is None: return None
    keepends = bool_arg(keepends, "KeepEnds")
    x = as_str(x)
    if isinstance(x, str): return x.splitlines(keepends)
    if isinstance(x, list): return list(poly_split_lines(x1, keepends) for x1 in x)
    raise TypeError(f'Splitlines with {poly_type(x)!r} not supported')
