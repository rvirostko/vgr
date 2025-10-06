"""
Functions for working with attrs and dictionaries
"""

from typing import Any

from .common import type_str

def poly_dig(data: Any, *args) -> Any:
    """
**Traverse a path in a dictionary object**

* Dig(_value_)
* Dig(_value_, _path_...)
* _value_.Dig()
* _value_.Dig(_path_...)

The _value_ must either be a dictionary, a list, or _None_.

Path parts can be:
* A _None_, string, boolean, int, or float
* A list composed of path components

```vgr
None.Dig() → None

Set point1 To {"x": 5, "y": 7, "meta": {"type": "2d", "name": "p1"}}
point1.Dig(None) → None
point1.Dig("x") → 5
point1.Dig("z") → None
point1.Dig("meta", "type") → "2d"

Set point2 To {"x": 7, "y": 29, "meta": {"type": "2d", "name": "p2"}}
point2.Dig(["meta", "name"]) → "p2"

[point1, point2].Dig("y") → [7, 29]
```

Also see `Lookup()`
"""
    if data is None: return data
    if isinstance(data, (list, tuple)):
        return list(poly_dig(d1, *args) for d1 in data)
    if not isinstance(data, dict):
        raise TypeError(f'Digging into {type_str(data)} not supported')
    # Always go through the path parts just to validate their types
    for arg in args: data = _dig(data, arg)
    return data

def _dig(data: dict, path: Any) -> Any:
    if path is not None:
        if isinstance(path, (str, bool, int, float)):
            # NB: don't str() as dictionaries can have non-string keys
            path = [path]
        elif not isinstance(path, (list, tuple)):
            raise TypeError(f'Digging with a {type_str(path)} not supported')
        if data is not None:
            for key in path:
                if not isinstance(data, dict) or key not in data: return None
                data = data[key]
    return data
