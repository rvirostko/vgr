"""
Dictionary related functions
"""

from copy import copy, deepcopy
from re import Pattern
from typing import Any

from ..vgr_callable import VgrCallable

from .common import (
    bound_ops,
    int_arg,
    requires_exec_context,
)
from .inequ import poly_eq
from .match import poly_matches
from .type import poly_type
from .types import poly_bool

@bound_ops("{...}", "dictionary", "dict")
def build_dict(*values: Any) -> dict:
    """
**Create a dictionary from the collected key/value pairs**

* **{** **}** _an_ _empty_ _dictionary_
* **{** _key_ **:** _value_ [, _key_ **:** _value_]... **}** _an_ _initialized_ _dictionary_

Keys can be any ordinal type: int, float, string. _None_ cannot be a key.

Values can be any type including _None_, other lists, and dictionaries.

```vgr
Set data To {}
Set person To {
    "name": "Alice",
    "age":  30,
    "city": "Paris"
}
Set employee To {
    "id": "E123",
    "info": {
        "name":       "Bob",
        "department": "Sales",
        "active":     True
    }
}
Set inventory To {
    "fruits": ["apple", "banana", "orange"],
    "counts": [10, 25, 7]
}
Set users To {
    "alice": {"email": "alice@example.com", "active": True},
    "bob":   {"email": "bob@example.com",   "active": False}
}
Set mixed To {
    "number": 42,
    "text":   "hello",
    "flag":   False,
    "none":   None,
    "list":   [1, 2, 3],
    "dict":   {"nested": "value"}
}
```
Also see `Dict()`, `GetKeyValue()`, and `LookupItem()`
"""
    # Values is alternating pairs of key/values
    # so we use a "stride" of two to form two groups
    # and recombine into pairs using zip()
    return None if values is None else dict(zip(values[::2], values[1::2]))

def poly_dict_create(*args: Any) -> dict:
    """
**Compose a dictionary from hetrogenous data**

* Dict()
* Dict(_expression_ [, _expression_...])

Creates a dictionary and optionally initializes it.
Sources for initialization can be ordinals used as keys or composite keys,
lists of initializations, and other dictionaries.

When dictionaries are added, a deep merge is performed, unlike
the shallow merge performed by `Add()`.

```vgr
Dict(None) → {}
Dict([]) → {}
Dict("a") → {"a": None}
Dict(["a"]) → {"a": None}
Dict(["a", 1]) → {"a": 1}
Dict(["a", 1, 2]) → {"a": [1, 2]}
Dict(["f.a", 1], ["f.b", 2]) → {"f": {"a": 1, "b": 2}}
Dict([["f.a", 1], ["f.b", 2]]) → {"f": {"a": 1, "b": 2}}
Dict({"f":{"a": 1}}, ["f.b", 2]) → {"f": {"a": 1, "b": 2}}

Set lines = ["a | b | c", "1 | 2 | 3", "one | two | three"]
Set records To List()
ForEach line in lines:
    Set elems To line.Split("|").Strip()
    If $loop.first:
        Set headers To elems.Upper()
    Else:
        Append Dict(CombineLists(headers, elems)) To records
    End
End
Print records.FormatJson()
[
  {
    "A": "1",
    "B": "2",
    "C": "3"
  },
  {
    "A": "one",
    "B": "two",
    "C": "three"
  }
]
```

Also see `CombineLists()`
"""
    def _set_key(data: dict, key: Any, value: Any) -> dict:
        # Only scalar keys can be used; other ignored
        if isinstance(key, (int, float)): return poly_setkeyvalue(data, key, value)
        # String can be paths; simple split with no other cleanup
        if isinstance(key, str): return poly_setkeyvalue(data, key.split('.'), value)
        # Other types are ignored
        return data
    def _normalize_args(*args):
        for item in args:
            if isinstance(item, list):
                # Is this is a list of lists/dicts?
                inner_all_complex = True
                for sub in item:
                    if sub is not None and not isinstance(sub, (list, dict)):
                        inner_all_complex = False
                        break
                if inner_all_complex:
                    yield from item
                else:
                    yield item
            else:
                yield item
    data = {}
    for arg in _normalize_args(*args):
        if arg is not None:
            if isinstance(arg, dict):
                data = _merge_dict(data, arg)
            elif isinstance(arg, list):
                if len(arg) > 0:
                    # Lists should be [key, value(s)]
                    key = arg[0]
                    if key is not None:
                        l = len(arg)
                        data = _set_key(data, key, None if l == 1 else arg[1] if l == 2 else arg[1:])
            else:
                data = _set_key(data, arg, None)
    return data

def _merge_dict(a: dict, b: dict) -> dict:
    """
    Recursively merge dict b into dict a.
    Values in b override unless both sides are dicts.
    Operates in-place on a and also returns it.
    """
    if len(a) == 0:
        a = b
    elif len(b) != 0:
        for key, b_val in b.items():
            if key in a and isinstance(a[key], dict) and isinstance(b_val, dict):
                _merge_dict(a[key], b_val)
            else:
                a[key] = b_val
    return a


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

def poly_getkeyvalue(data: Any, path: Any, default_value: Any=None) -> Any:
    """
**Traverse a path in a dictionary and return its value**

* GetKeyValue(_value_, _path_)
* GetKeyValue(_value_, _path_, _default_value_)
* _value_.GetKeyValue(_path_)
* _value_.GetKeyValue(_path_, _default_value_)

The _value_ must either be a dictionary, a list, or _None_.

The _path_ can be:

* A string, boolean, int, or float
* A list composed of path components

```vgr
Set point1 To {"x": 5, "y": 7, "meta": {"type": "2d", "name": "p1"}}
point1.GetKeyValue(None) →
    {"x": 5, "y": 7, "meta": {"type": "2d", "name": "p1"}}
None.GetKeyValue("x") → None
point1.GetKeyValue("x") → 5
point1.GetKeyValue(["x"]) → 5
point1.GetKeyValue(["x", None]) → 5
point1.GetKeyValue("z") → None
point1.GetKeyValue("z", 0) → 0

Set point2 To {"x": 7, "y": 29, "meta": {"type": "2d", "name": "p2"}}
point2.GetKeyValue(["meta", "name"]) → "p2"
[point1, point2].GetKeyValue("y") → [7, 29]
```

Also see `SetKeyValue()` and `LookupItem()`
"""
    if isinstance(data, (list, tuple)): return list(poly_getkeyvalue(d1, path, default_value) for d1 in data)
    if not isinstance(data, dict): return data
    path = _normalize_path(path)
    if path is None: return data
    if isinstance(path, (str, bool, int, float)):  return copy(data.get(path, default_value))
    found, rc = _deref(data, path)
    return copy(rc if found else default_value)

def poly_setkeyvalue(data: Any, path: Any, value: Any=None) -> Any:
    """
**Traverse a path in a dictionary and set a value**

* SetKeyValue(_value_, _path_)
* SetKeyValue(_value_, _path_, _new_value_)
* _value_.SetKeyValue(_path_)
* _value_.SetKeyValue(_path_, _new_value_)

The _value_ must either be a dictionary, a list, or _None_.

The _path_ can be:

* A string, boolean, int, or float
* A list composed of path components

```vgr
Set point1 To {"x": 5, "y": 7, "meta": {"type": "2d", "name": "p1"}}
None.SetKeyValue("z", 0) → None
point1.SetKeyValue(None)
    → {"x": 5, "y": 7, "meta": {"type": "2d", "name": "p1"}}
point1.SetKeyValue("x")
    → {"x": None, "y": 7, "meta": {"type": "2d", "name": "p1"}}
point1.SetKeyValue("z", 10)
    → {"x": 5, "y": 7, "meta": {"type": "2d", "name": "p1"}, "z": 10}
point1.SetKeyValue(["meta", "name"], "alpha")
    → {"x": 5, "y": 7, "meta": {"type": "2d", "name": "alpha"}}
point1.SetKeyValue([], "ignored")
    → {"x": 5, "y": 7, "meta": {"type": "2d", "name": "p1"}}

Set point2 To {"x": 7, "y": 29, "meta": {"type": "2d", "name": "p2"}}
point2.SetKeyValue(["meta", "color"], "red")
    → {"x": 7, "y": 29, "meta": {"type": "2d", "name": "p2", "color": "red"}}
point2.SetKeyValue(["meta", "extra", "layer"], 3)
    → {"x": 7, "y": 29, "meta": {"type": "2d", "name": "p2", "extra": {"layer": 3}}}
[point1, point2].SetKeyValue("z", 0)
    → [{"x": 5, "y": 7, "meta": {"type": "2d", "name": "p1"}, "z": 0},
       {"x": 7, "y": 29, "meta": {"type": "2d", "name": "p2"}, "z": 0}]
[point1, point2].SetKeyValue(["meta", "visible"], True)
    → [{"x": 5, "y": 7, "meta": {"type": "2d", "name": "p1", "visible": True}},
       {"x": 7, "y": 29, "meta": {"type": "2d", "name": "p2", "visible": True}}]
[point1, point2].SetKeyValue(["meta", "name"], None)
    → [{"x": 5, "y": 7, "meta": {"type": "2d", "name": None}},
       {"x": 7, "y": 29, "meta": {"type": "2d", "name": None}}]
[None, point1].SetKeyValue(["meta", "flag"], True)
    → [None, {"x": 5, "y": 7, "meta": {"type": "2d", "name": "p1", "flag": True}}]
```

Also see `GetKeyValue()`
"""
    if isinstance(data, list): return list(poly_setkeyvalue(d1, path, value) for d1 in data)
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

Also see `GetValues()`
"""
    if isinstance(data, dict): return list(data.keys())
    if isinstance(data, list):
        keys = set()
        for item in data: keys.update(poly_getkeys(item))
        return list(keys)
    return []

def poly_getvalues(data: Any) -> list:
    """
**Return a list of all the values in a dictionary**

* GetValues(_value_)
* _value_.GetValues()

The _value_ must either be a dictionary or a list.
For non-dictionaries, an empty list is returned.

```vgr
Set point1 To {"x": 5, "y": 7, "space": 2, "name": "p1"}
Set point2 To {"x": 7, "y":29, "space": 2, "name": "p2"}
Set points To [point1, point2]

None.GetValues() → []
5.GetValues() → []
point1.GetValues() → [5, 7, 2, "p1"]
points.GetValues() → [[5, 7, 2, "p1"], [7, 29, 2, "p2"]]
```

Also see `GetKeys()`
"""
    if isinstance(data, dict): return list(data.values())
    if isinstance(data, list):
        values = []
        for item in data: values.append(poly_getvalues(item))
        return values
    return []

def poly_removekey(data: Any, path: Any) -> Any:
    """
**Remove a key from a dictionary**

* RemoveKey(_value_, _path_)
* _value_.RemoveKey(_path_)

The _value_ must either be a dictionary, a list, or _None_.

The _path_ can be:

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

Also see `SetKeyValue()`
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
        found, target = _deref(data, path)
        if found and isinstance(target, dict) and key in target:
            # Multiple layers down so make a deep copy
            # Then, because it is a deep copy, we need to
            # relocate "target" before removing the key
            data = deepcopy(data)
            _, target = _deref(data, path)
            target.pop(key)
    return data

@requires_exec_context
def poly_lookupitem(x: Any, path: Any, values: Any=None, limit: Any=None, *, ctx=None) -> Any:
    """
**Find a matching entries in a list by value**

* LookupItem(_list_, _path_, _value_ [, limit])
* _list_.LookupItem(_path_, _value_ [, limit])

The _path_ can be:

* A string, boolean, int, or float
* A list composed of path components

For _value_ argument, may be a single value, a list of values.
Regular expressions can also be used for comparisons: see `CompilePattern()`.
If a _value_ is a function the dereferenced key value is passed as the argument to
the function for testing. The function should return a boolean value.

The returned result is always a list, which may be empty.
When performed on _None_ or a non-dictionary it returns an empty list.

```vgr
Set point1 To {"x": 5, "y": 7, "space": 2, "name": "p1"}
Set point2 To {"x": 7, "y":29, "space": 2, "name": "p2"}
Set point3 To {"x": 9, "y":31, "z": -7, "space": 3, "name": "p3"}
Set point4 To {"x":11, "y":37, "z": None, "space": 3, "name": "p4"}
Set points To [point1, point2, point3, point4]

points.LookupItem("x", 5) → [{"x": 5, "y": 7, "space": 2, "name": "p1"}]
points.LookupItem("z", None).GetKeyValue("name") → ["p4"]
points.LookupItem("space", 1).GetKeyValue("name") → []
points.LookupItem("space", [1, 2]).GetKeyValue("name") → ["p1", "p2"]
points.LookupItem("space", [2, 1]).GetKeyValue("name") → ["p1", "p2"]
points.LookupItem("space", 3).LookupItem("z", None).GetKeyValue("name")
    → ["p4"]
points.LookupItem("name", CompilePattern("p[24]")).GetKeyValue("name")
    → ["p2", "p4"]

Set filter(x) -> x.EndsWith("2", "3")
points.LookupItem("name", filter).GetKeyValue("name") → ["p2", "p3"]
```

Also see `GetKeyValue()` and `CompilePattern()`
"""
    if x is None: return []
    # We must always have a list to search
    if not isinstance(x, list): x = list(x)
    # We must always have a path
    path = _normalize_path(path)
    if path is None: return []
    # We must always have a value
    if isinstance(values, list) and len(values) == 0: return []
    # Constrain limit to either None or a positive non-zero integer
    if limit is not None:
        limit = int_arg(limit, "Limit")
        if limit <= 0: limit = None
    def _test(x: Any, y: Any) -> bool:
        # If the desired value is a function, then x is passed to it for evaluation
        if isinstance(y, VgrCallable): return poly_bool(y.evaluate(ctx, [x]))
        # If the desired value is a Pattern, use matches rather than equals
        return poly_matches(x, y) if isinstance(y, Pattern) else poly_eq(x, y)
    def _in_list(value: Any, values: list) -> bool:
        # Our own value of "in" which includes Patterns as per above
        for v in values:
            if _test(value, v): return True
        return False
    def _find(data: Any, path: Any) -> tuple:
        return (True, data[path]) if path in data else (False, None)
    # Determine the comparison operation
    comparator = _in_list if isinstance(values, list) else _test
    finder = _deref if isinstance(path, list) else _find
    results = []
    # Sweep the data for matching elements and add to the results
    for data in x:
        # Skip over non-dict instances in the list
        if isinstance(data, dict):
            # Determine the attribute and compare it if found
            # Note that you can't use lookup() to find entries which
            # do not posses an attribute
            found, value = finder(data, path)
            if found and comparator(value, values):
                results.append(data)
                # Terminate search if we exceed our limit
                if limit is not None and len(results) >= limit: break
    return results

def _deref(data: Any, path: list) -> tuple:
    for step in path:
        if not isinstance(data, dict) or step not in data:
            return (False, None)
        data = data[step]
    return (True, data)

def _normalize_path(path: Any) -> Any:
    def _validate_step(step: Any) -> Any:
        if isinstance(step, (str, bool, int, float)): return step
        raise TypeError(f'Dereferencing with a {poly_type(step)!r} not supported')
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
