import random
from typing import Any

from .common import int_arg
from .inequ import poly_lt, poly_clamp
from .list import poly_to_list
from .misc_math import poly_ceil
from .registry import builtin
from .type import poly_type
from .types import poly_to_number

@builtin("Random")
def poly_random(*args) -> Any:
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

Also see `RandomChoice()` and `RandomSample()`
"""
    # Unpack the args: If more than two, the first n-1 become a list of start values
    n = args[0:-1] if len(args) > 2 else args[0] if 1 <= len(args) <= 2 else None
    m = args[-1] if len(args) >= 2 else None
    if n is None and m is None: return random.random()
    if isinstance(n, (list, tuple)): return list(poly_random(n1, m) for n1 in n)
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
RandomChoice() → None
RandomChoice(None) → None
RandomChoice(1) → 1
RandomChoice(1, 2) → 1 or 2
RandomChoice([1, 2]) → 1 or 2
RandomChoice({}) → None
RandomChoice({"a": 1, "b": 2}) → ['a': 1] or ['b', 2]
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

@builtin("RandomSample")
def poly_random_choice(*args: Any) -> Any:
    """
**Return a random sample from a collection**

* RandomSample()
* RandomSample(*collection*[, *size*])
* *collection*.RandomSample([*size*])

The *size* is a number representing the desired sample size. Values between 0 and 1 (exclusive)
represent a fraction of the lists size. Values greater than zero represent
the count of items from the original list.

When *size* is omitted, approximately half the contents of the list will be returned.

If *collection* is a dictionary, it is converted to a list as with `ToList()` and the
sample is taken from list of keys and values.

```vgr
RandomSample() → None
None.RandomSample() → None
[].RandomSample() → []
[1, 2, 3].RandomSample()        # ex: [2, 3] or [3, 1]
[1, 2, 3, 4].RandomSample(.25)  # ex: [3]
[1, 2, 3, 4].RandomSample(.1)   # ex: [2]
[1, 2, 3, 4].RandomSample(3)    # ex: [3, 4, 1]

{}.RandomSample() → []
{"a": 1, "b": 2}.RandomSample() # ex: [['a': 1]] or [['b', 2]]
```

Also see `RandomChoice()`
"""
    # Unpack the args: If more than two, the first n-1 become a list of start values
    population = args[0:-1] if len(args) > 2 else args[0] if 1 <= len(args) <= 2 else None
    k = args[-1] if len(args) >= 2 else None
    if isinstance(population, dict): population = poly_to_list(population)
    if isinstance(population, (list, tuple)):
        plen = len(population)
        if k == None:
            k = .5 if plen > 2 else 1 # 50% but at least one
        elif isinstance(k, str):
            k = poly_to_number(k) # we don't pass a default, so it might throw a ValueError
        if isinstance(k, float):
            k = int(poly_ceil(plen * k) if 0.0 <= k < 1.0 else k)
        elif not isinstance(k, int):
            raise TypeError(f'SampleSize must be a number, found {poly_type(k)!r}')
        k = poly_clamp(k, 0, plen)
        return [] if k == 0 else random.sample(population, k) if plen > 0 else None
    return population
