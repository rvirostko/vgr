
from typing import Any

from collections.abc import Sequence, Iterable

from .common import int_arg
from .registry import builtin

@builtin("Slice")
def poly_slice(x: Any=None, start: Any=None, stop: Any=None, step: Any=None) -> Any:
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
of the slice, and the modulus of elements to be included.

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
    start = _int_arg(start, "Start")
    stop = _int_arg(stop, "Stop")
    step = _int_arg(step, "Step")
    if x is None: return None
    # Treat bytes and bytearray like strings (return same type)
    if isinstance(x, (str, bytes, bytearray)): return x[start:stop:step]
    # Accept any object that supports slicing via __getitem__
    if isinstance(x, Sequence): return list(x[start:stop:step])
    # Convert iterable to list then slice
    if isinstance(x, Iterable): return list(list(x)[start:stop:step])
    # likely a bool, int, float, Pattern
    return x

@builtin("Head")
def poly_head(x: Any=None, count: Any=None, *args) -> Any:
    """
**Return a subset of a collection starting from the first item**

* Head(*value*, *count*)
* *value*.Head(*count*)

If *count* is omitted, the value is returned unchanged.
If *count* is negative, it is interpreted as an offset from the end
of the collection.

```vgr
Constant data Is [1, 2, 3]

None.Head() → None
5.Head() → [5]
data.Head() → [1, 2, 3]
data.Head(0) → []
data.Head(1) → [1]
data.Head(2) → [1, 2]
data.Head(-1) → [1, 2]
```

Also see `Tail()` and `Slice()`
"""
    if x is None: return None
    if not isinstance(x, list): x = [x]
    # No need to mess with count: poly_slice will do that
    return poly_slice(x, 0, count)

@builtin("Tail")
def poly_tail(x: Any=None, count: Any=None, *args) -> Any:
    """
**Return a subset of a collection starting from the last item**

```vgr
Constant data Is [1, 2, 3]

None.Tail() → None
5.Tail() → [5]
data.Tail() → [1, 2, 3]
data.Tail(0) → []
data.Tail(1) → [3]
data.Tail(2) → [2, 3]
data.Tail(-1) → [2, 3]
```

Also see `Head()` and `Slice()`
"""
    if x is None: return None
    if not isinstance(x, list): x = [x]
    count = _int_arg(count, "Count")
    if count is None: return x
    # zero: no items
    # negative: all but the first N
    # positive: start N back from the end
    return [] if count == 0 else poly_slice(x, -count)

# effectively this is just an "allow None" version of int_arg()
def _int_arg(arg, name): return None if arg is None else int_arg(arg, name)
