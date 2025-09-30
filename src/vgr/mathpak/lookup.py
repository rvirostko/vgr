from itertools import chain
from typing import Any

from .common import type_str
from .inequ import poly_eq

def poly_lookup(x: Any, attr: Any, *args) -> Any:
    """
**Find a matching entry in a list by value**

* _list_.Lookup(_attr_, _value_...)

The _attr_ argument can be an int or float but more typically is a string. Lists and dictionaries cannot be used.
The attributes named in the list must be an exact match.
For the value argument, it may be a single value or a list of values.

The result is always a list, which may be empty. A lookup performed on None or a non-list
always returns an empty list of results.

```vgr
**TODO**
```
"""
    if not isinstance(x, (list, tuple)): return []
    if not isinstance(attr, (str, int, float, tuple)):
        raise TypeError(f'Cannot use {type_str(attr)} for attribute in Lookup')
    # NB: Don't strip the attr! Crazy people put blanks in CSV column headers and you may have to deal with that
    if len(args) == 1:
        arg = args[0]
        return _multi_lookup(x, attr, arg) if isinstance(arg, (list, tuple)) else _lookup(x, attr, arg)
    return _multi_lookup(x, attr, args)

def _multi_lookup(x:Any, attr: Any, values: Any) -> list[Any]:
    # This chain takes all the results and handles as if it were a single iterator
    return list(chain.from_iterable(_lookup(x, attr, value) for value in values))

def _lookup(x: Any, attr: Any, value: Any) -> list[Any]:
    # NB: since poly_eq() uses the first param to drive conversions,
    #     we use the data we have in the records as the "right" type
    #     and let value be adjusted accordingly
    return [x1 for x1 in x
            if isinstance(x1, dict) and
                attr in x1 and
                poly_eq(x1.get(attr), value)]
