import random
from typing import Any

from .common import (
    int_arg,
)
from .inequ import poly_lt
from .registry import builtin

@builtin("Random")
def poly_random(n: Any=None, m: Any=None) -> Any:
    """
**Generate a random number within limits

* Random()
* Random(*limit*)
* *limit*.Random()
* Random(*start*, *end*)
* *start*.Random(*end*)

Without arguments, a floating point value from 0 to 1.0 is returned.
For other limits, the result is an integer.

```vgr
Random() → 0.0405106169393431
Random(1) → 0 or 1
Random(1, 3) → 1, 2, or 3
```

Also see `RandomChoice()`
"""
    if isinstance(n, list): return list(poly_random(n1, m) for n1 in n)
    # No arguments: return float [0.0, 1.0)
    if n is None and m is None: return random.random()
    if m is None:
        low = 0
        high = int_arg(n, "Limit")
    else:
        low = int_arg(n, "Start")
        high = int_arg(m, "End")
    low, high = (low, high) if poly_lt(low, high) else (high, low)
    return random.randint(low, high)

@builtin("RandomChoice")
def poly_random_choice(*args: Any) -> Any:
    """
**Return a random item from a collection**

* RandomChoice()
* RandomChoice(*collection*)
* *collection*.RandomChoice()

Returns a random item from a list, or if dictionary is provided, a
random key/value pair is returned. For all other types, the item itself
is returned. If given multiple arguments, the arguments themselves constitute
the collection.

```vgr
RandomChoice(1) → 1
RandomChoice(1, 2) → 2
RandomChoice([1, 2]) → 2
RandomChoice({}) → None
RandomChoice({"a": 1, "b": 2}) → ['b', 2]
```

Also see `Random()`
"""
    if len(args) == 0: return None
    if len(args) > 1: return random.choice(args)
    obj = args[0]
    if isinstance(obj, list): return random.choice(obj) if obj else None
    if isinstance(obj, dict):
        if not obj: return None
        key, value = random.choice(list(obj.items()))
        return [key, value]
    return obj
