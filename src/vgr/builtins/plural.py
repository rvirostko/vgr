from typing import Any

from .registry import builtin

@builtin("Plural")
def poly_plural(x: Any=None, plural: Any='s', singular: Any='') -> Any:
    """
**Return a suffix for pluralization**

* *value*.Plural()
* *value*.Plural(*plural*)
* *value*.Plural(*plural*, *singular*)

If *value* is a number is not equal to one, or a value that
has a length that is not one, then the *plural* value is returned.
Otherwise, the *singular* value is returned.
The defaults arguments are *s* and an empty string respectively.
The values for *plural* and *singular* can be any any values.

```vgr
"value" + None.Plural() → "values"
"value" + 1.Plural() → "value"
"character" + "1".Plural() → "character"
"character" + "2".Plural() → "character"
"character" + "two".Plural() → "characters"
"item" + [].Plural() → "items"
"item" + ["one", "two"].Plural() → "items"
"Zero" + 2.Plural("es") → "Zeroes"
1.Plural("mice", "mouse") → "mouse"
```
"""
    if isinstance(x, (int, float)):
        is_one = x == 1
    else:
        is_one = hasattr(x, "__len__") and len(x) == 1
    return singular if is_one else plural
