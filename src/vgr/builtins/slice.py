
from typing import Any

from collections.abc import Sequence, Iterable

from .common import int_arg
from .registry import builtin

@builtin("Slice")
def poly_slice(x: Any=None, start: int=None, stop: int=None, step: int=None) -> Any:
    """
**Extract a portion of a list, string, or dictionary**

* *value*.Slice()
* *value*.Slice(*start*)
* *value*.Slice(*start*, *stop*)
* *value*.Slice(*start*, *stop*, *step*)

`Slice()` works with strings, lists, and dictionaries. For other types,
*value* is returned unchanged.

The *start* value is a zero-based start index for the slice.
If omitted, the slice starts at the first element.

The *stop* value is a zero-based, exclusive index for the slice.
If omitted, the slice includes *all* elements.

The *step* value is a non-zero value that indicates both the direction
of the slice, and what elements will be included, defaulting to 1.

Negative values for *start* and *stop* reference the end rather than
the start. Negative *step* values are used to move right-to-left
withing *value*.

```vgr
None.Slice() → None
True.Slice(2) → True
5.Slice(2) → 5
5.1.Slice(2) → 5.1

"".Slice() → ""
"cake".Slice() → "cake"
"cake".Slice(2) → "ke"
"cake".Slice(1, 3) → "ak"
"cake".Slice(1, 4, 2) → "ae"

[].Slice(2) → []
[1, 2, 3, 4, 5].Slice(2) → [3, 4, 5]
[1, 2, 3, 4, 5].Slice(1, 4) → [2, 3, 4]
[1, 2, 3, 4, 5].Slice(0, 5, 2) → [1, 3, 5]
[10, 20, 30, 40].Slice(-2) → [30, 40]
[10, 20, 30, 40].Slice(-3, -1) → [20, 30]
[10, 20, 30, 40].Slice(-1, -5, -1) → [40, 30, 20, 10]

// Slicing a dictionary works on its keys
{}.Slice(2) → []
{"a": 1, "b": 2, "c": 3}.Slice() → ["a", "b", "c"]
{"a": 1, "b": 2, "c": 3}.Slice(1) → ["b", "c"]
{"a": 1, "b": 2, "c": 3}.Slice(0, 2) → ["a", "b"]
{"a": 1, "b": 2, "c": 3}.Slice(0, 3, 2) → ["a", "c"]
```
"""
    start = int_arg(start, "Start") if start is not None else None
    stop = int_arg(stop, "Stop") if stop is not None else None
    step = int_arg(step, "Step") if step is not None else None
    if x is None: return None
    # Treat bytes and bytearray like strings (return same type)
    if isinstance(x, (str, bytes, bytearray)): return x[start:stop:step]
    # Accept any object that supports slicing via __getitem__
    if isinstance(x, Sequence): return list(x[start:stop:step])
    # Convert iterable to list then slice
    if isinstance(x, Iterable): return list(list(x)[start:stop:step])
    # likely a bool, int, float, Pattern
    return x
