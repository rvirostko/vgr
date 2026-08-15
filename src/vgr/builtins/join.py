from typing import Any

from .as_str import as_str
from .common import str_arg
from .registry import builtin
from .type import poly_type

@builtin("Join")
def poly_join(x: Any=None, sep: str=None) -> Any:
    """
**Join together the elements of a list as strings**

* Join(*value*)
* Join(*value*, *sep*)
* *value*.Join()
* *value*.Join(*sep*)

The *sep* argument is the separator between the strings.
It defaults to an empty string, causing the values to be concatenated.

If *value* is a list, the items in it are converted to strings and concatenated
using *sep*. Items in the list that are `None` are ignored.

If *value* is an ordinal, it is converted to a string, and
*sep* is not used. With a *value* of `None` or for an empty list an
empty string is returned.

```vgr
None.Join() → ""
"a".Join() → "a"
[].Join() → ""
["a", "b"].Join(", ") → "a, b"
["a", ["b", "c"]].Join("-") → "a-b-c"
1234.Join(0) → "1234"
123.ToString().Ord().Chr().Join(0).ToInteger() → 10203
```

Also see `Split()` and `RSplit()`
"""
    if x is None: return ''
    x = as_str(x)
    if isinstance(x, str): return x
    sep = as_str(sep)
    sep = '' if sep is None else str_arg(sep, 'Sep', False)
    if isinstance(x, list): return sep.join([poly_join(x1, sep) for x1 in x if x1 is not None])
    raise TypeError(f'Join of {poly_type(x)!r} not supported')
