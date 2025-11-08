"""
Dictionary related functions
"""

from copy import copy, deepcopy
from itertools import chain
from typing import Any

from .common import type_str
from .inequ import poly_eq

def poly_dig(_data: Any, *_args) -> Any:
    """
**Obsolete: use GetValue()**
"""
    raise NotImplementedError("Dig() has been replaced by GetValue()")

def poly_isdict(x: Any) -> bool:
    """
**Returns _True_ if the value is a dictionary**

* IsDictionary(_value_)
* _value_.IsDictionary()

```vgr
None.IsDictionary() → False
"bob".IsDictionary() → False
{}.IsDictionary() → True
{"name": "bob"}.IsDictionary() → True
```

Also see `Type()`
"""
    return isinstance(x, dict)

def poly_getvalue(data: Any, path: Any, default_value: Any=None) -> Any:
    """
**Traverse a path in a dictionary and return its value**

* GetValue(_value_, _path_)
* GetValue(_value_, _path_, _default_value_)
* _value_.GetValue(_path_)
* _value_.GetValue(_path_, _default_value_)

The _value_ must either be a dictionary, a list, or _None_.

Path can be:
* A string, boolean, int, or float
* A list composed of path components

```vgr
Set point1 To {"x": 5, "y": 7, "meta": {"type": "2d", "name": "p1"}}
point1.GetValue(None) →
    {"x": 5, "y": 7, "meta": {"type": "2d", "name": "p1"}}
None.GetValue("x") → None
point1.GetValue("x") → 5
point1.GetValue(["x"]) → 5
point1.GetValue(["x", None]) → 5
point1.GetValue("z") → None
point1.GetValue("z", 0) → 0

Set point2 To {"x": 7, "y": 29, "meta": {"type": "2d", "name": "p2"}}
point2.GetValue(["meta", "name"]) → "p2"
[point1, point2].GetValue("y") → [7, 29]
```

Also see `SetValue()` and `Lookup()`
"""
    if isinstance(data, (list, tuple)): return list(poly_getvalue(d1, path, default_value) for d1 in data)
    if not isinstance(data, dict): return data
    path = _normalize_path(path)
    if path is None: return data
    if isinstance(path, (str, bool, int, float)):  return copy(data.get(path, default_value))
    return copy(_deref(data, path, default_value))

def poly_setvalue(data: Any, path: Any, value: Any=None) -> Any:
    """
**Traverse a path in a dictionary and set a value**

* SetValue(_value_, _path_)
* SetValue(_value_, _path_, _new_value_)
* _value_.SetValue(_path_)
* _value_.SetValue(_path_, _new_value_)

The _value_ must either be a dictionary, a list, or _None_.

Path can be:
* A string, boolean, int, or float
* A list composed of path components

```vgr
Set point1 To {"x": 5, "y": 7, "meta": {"type": "2d", "name": "p1"}}
None.SetValue("z", 0) → None
point1.SetValue(None)
    → {"x": 5, "y": 7, "meta": {"type": "2d", "name": "p1"}}
point1.SetValue("x")
    → {"x": None, "y": 7, "meta": {"type": "2d", "name": "p1"}}
point1.SetValue("z", 10)
    → {"x": 5, "y": 7, "meta": {"type": "2d", "name": "p1"}, "z": 10}
point1.SetValue(["meta", "name"], "alpha")
    → {"x": 5, "y": 7, "meta": {"type": "2d", "name": "alpha"}}
point1.SetValue([], "ignored")
    → {"x": 5, "y": 7, "meta": {"type": "2d", "name": "p1"}}

Set point2 To {"x": 7, "y": 29, "meta": {"type": "2d", "name": "p2"}}
point2.SetValue(["meta", "color"], "red")
    → {"x": 7, "y": 29, "meta": {"type": "2d", "name": "p2", "color": "red"}}
point2.SetValue(["meta", "extra", "layer"], 3)
    → {"x": 7, "y": 29, "meta": {"type": "2d", "name": "p2", "extra": {"layer": 3}}}
[point1, point2].SetValue("z", 0)
    → [{"x": 5, "y": 7, "meta": {"type": "2d", "name": "p1"}, "z": 0},
       {"x": 7, "y": 29, "meta": {"type": "2d", "name": "p2"}, "z": 0}]
[point1, point2].SetValue(["meta", "visible"], True)
    → [{"x": 5, "y": 7, "meta": {"type": "2d", "name": "p1", "visible": True}},
       {"x": 7, "y": 29, "meta": {"type": "2d", "name": "p2", "visible": True}}]
[point1, point2].SetValue(["meta", "name"], None)
    → [{"x": 5, "y": 7, "meta": {"type": "2d", "name": None}},
       {"x": 7, "y": 29, "meta": {"type": "2d", "name": None}}]
[None, point1].SetValue(["meta", "flag"], True)
    → [None, {"x": 5, "y": 7, "meta": {"type": "2d", "name": "p1", "flag": True}}]
```

Also see `GetValue()`
"""
    if isinstance(data, list): return list(poly_setvalue(d1, path, value) for d1 in data)
    if not isinstance(data, dict): return data
    path = _normalize_path(path)
    if path is None: return data
    if isinstance(path, (str, bool, int, float)):
        data = copy(data)
        data[path] = value
        return data
    path, key = path[:-1], path[-1]
    data = deepcopy(data)
    d = data
    for step in path:
        if step not in d or not isinstance(d[step], dict): d[step] = {}
        d = d[step]
    d[key] = value
    return data

def poly_getkeys(data: Any) -> list:
    """
**Retrieve the keys used in a dictionary**

* GetKeys(_value_)
* _value_.GetKeys()

The _value_ must either be a dictionary or a list.
For non-dictionaries, an empty list is returned.

```vgr
Set point1 To {"x": 5, "y": 7}
None.GetKeys() → []
"bob".GetKeys() → []
point1.GetKeys() → ["x", "y"]

Set point2 To {"x": 7, "z": 29}
point2.GetKeys() → ["x", "z"]
[point1, point2].GetKeys() → ["y", "x", "z"]
```
"""
    if isinstance(data, dict): return list(data.keys())
    if isinstance(data, list):
        keys = set()
        for item in data: keys.update(poly_getkeys(item))
        return list(keys)
    return []

def poly_removekey(data: Any, path: Any) -> Any:
    """
**Remove a key from a dictionary**

* RemoveKey(_value_, _path_)
* _value_.RemoveKey(_path_)

The _value_ must either be a dictionary, a list, or _None_.

Path can be:
* A string, boolean, int, or float
* A list composed of path components

```vgr
Set point1 To {"x": 5, "y": 7, "meta": {"type": "2d", "name": "p1"}}
None.RemoveKey("z") → None
point1.RemoveKey(None) → {"x": 5, "y": 7, "meta": {"type": "2d", "name": "p1"}}
point1.RemoveKey("x") → {"y": 7, "meta": {"type": "2d", "name": "p1"}}
point1.RemoveKey(["meta", "name"]) → {"x": 5, "y": 7, "meta": {"type": "2d"}}

Set point2 To {"x": 7, "y": 29, "meta": {"type": "2d", "name": "p2"}}
[point1, point2].RemoveKey("y")
    → [{"x": 5, "meta": {"type": "2d", "name": "p1"}},
       {"x": 7, "meta": {"type": "2d", "name": "p2"}}]
[point1, point2].RemoveKey(["meta", "type"])
    → [{"x": 5, "y": 7, "meta": {"name": "p1"}},
       {"x": 7, "y": 29, "meta": {"name": "p2"}}]
```

Also see `SetValue()`
"""
    if isinstance(data, list): return list(poly_removekey(d1, path) for d1 in data)
    if not isinstance(data, dict): return data
    path = _normalize_path(path)
    if path is None: return data
    # A simple removal request
    if isinstance(path, (str, bool, int, float)):
        if path in data:
            data = copy(data)
            data.pop(path)
    else:
        # A multi step path removal, last part is the final key
        path, key = path[:-1], path[-1]
        target = _deref(data, path)
        if isinstance(target, dict) and key in target:
            # Multiple layers down so make a deep copy
            # Then, because it is a deep copy, we need to
            # relocate "target" before removing the key
            data = deepcopy(data)
            _deref(data, path).pop(key)
    return data

# TODO "attr" needs to become "path"
def poly_lookup(x: Any, attr: Any, *args) -> Any:
    """
**Find a matching entry in a list by value**

* Lookup(_list_, _attr_, _value_...)
* _list_.Lookup(_attr_, _value_...)

The _attr_ argument can be an int or float but more typically is a string. Lists and dictionaries cannot be used.
The attributes named in the list must be an exact match.
For _value_ argument, it may be a single value or a list of values.

The result is always a list, which may be empty. A Lookup() performed on _None_ or a non-list
always returns an empty list of results.

```vgr
Set point1 To {"x": 5, "y": 7, "space": 2, "name": "p1"}
Set point2 To {"x": 7, "y":29, "space": 2, "name": "p2"}
Set point3 To {"x": 9, "y":31, "z": -7, "space": 3, "name": "p3"}
Set point4 To {"x":11, "y":37, "z": None, "space": 3, "name": "p4"}
Set points To [point1, point2, point3, point4]
points.Lookup("x", 5) → [{"x": 5, "y": 7, "space": 2, "name": "p1"}]
points.Lookup("z", None).GetValue("name") → ["p4"]
points.Lookup("space", 1).GetValue("name") → []
points.Lookup("space", 1, 2).GetValue("name") → ["p1", "p2"]
points.Lookup("space", 3).Lookup("z", None).GetValue("name") → ["p4"]
```

Also see `GetValue()`
"""
    if not isinstance(x, list): return []
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

def _deref(data: Any, path: list, default_value: Any=None) -> Any:
    for step in path:
        if not isinstance(data, dict) or step not in data:
            data = default_value
            break
        data = data[step]
    return data

def _normalize_path(path: Any) -> Any:
    def _validate_step(step: Any) -> Any:
        if isinstance(step, (str, bool, int, float)): return step
        raise TypeError(f'Dereferencing with a {type_str(step)} not supported')
    if path is None: return None
    # Single step; path is just a key
    if not isinstance(path, list): return _validate_step(path)
    # Strip out Nones and validate each step's type
    path[:] = [_validate_step(step) for step in path if step is not None]
    # Just skip empty requests
    if len(path) == 0: return None
    # Unwrap arrays of one
    if len(path) == 1: return path[0]
    return path
