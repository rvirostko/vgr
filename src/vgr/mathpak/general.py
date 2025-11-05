from copy import copy
from functools import cmp_to_key
from typing import Any
import re

from .common import str_to_number, type_str, bool_arg, dist_x
from .inequ import poly_lt, poly_gt, poly_eq, poly_ne

def poly_reverse(x: Any) -> Any:
    """
**Reverses the contents of the lists and strings**

* Reverse(_value_)
* _value_.Reverse()

If _value_ is an ordinal rather than a list, it is returned unchanged.

```vgr
"five".Reverse() → "evif"
5.Reverse() → 5
5.0.Reverse() → 5.0
["five", 5, 5.0].Reverse() → [5.0, 5, "five"]
"One Two".Reverse() → "owT nenO"
```
"""
    if isinstance(x, (list, tuple)): return list(reversed(x))
    if isinstance(x, str): return x[::-1]
    return x

def poly_ascii(x: Any) -> str:
    """
**Returns a printable ASCII string for an item**

Similar to both `Repr()` and `ToString()`.
Characters outside of ASCII printables are encoded
with backslash sequences.

```vgr
"five".Ascii() → "five"
5.Ascii() → 5
5.0.Ascii() → 5.0
["five", 5, 5.0].Ascii() → ["five", 5, 5.0]
"One\\nTwo".Ascii() → "One\\nTwo"
```
"""
    return ascii(x)

def poly_hash(x: Any) -> int:
    """
**Returns the internal hashcode for an object**

* Hash(_value_)
* _value_.Hash()

This can be used in debugging but is of limited values in scripts.
Cannot be applied to lists or dictionaries.

```vgr
"five".Hash() → -3781267357408442496
5.Hash() → 5
5.0.Hash() → 5
```
"""
    return hash(x)

def poly_clone(x: Any) -> Any:
    """
**Ceates a copy of complex objects**

* Clone(_value_)
* _value_.Clone()

Only lists and dictionaries are cloned, as other
data types are not mutable in the same sense as
collections. This operation clones the container: if the
values within it are complex objects, their values will
still be shared.

**Examples**

_*Simple types return the same object*_
```vgr
Set x = 5
Print x.Id(), x.Clone().Id()
4335020464 4335020464 // same object
```

_*Cloning a complex object*_
```vgr
Set y = [1,2,3]
Print y.Id(), y.Clone().Id()
4808334400 4807906688 // different objects
```

_*Container is cloned, but complex objects are shared*_
```vgr
Set z = [ {"a" : 1} ]
Set z′ = z.Clone()
Print z.Id(), z′.Id()
4810281856 4708798208 // different lists
Print z.FirstItem().Id(), z′.FirstItem().Id()
4502192256 4502192256 // same contents
```

Also see `Id()` and `Hash()`
"""
    if isinstance(x, (list, dict)): return copy(x)
    return x

def poly_repr(x: Any) -> str:
    """
**Returns a string representation of an item

Differs slightly from `ToString()` as it surrounds string values with quotes
and escapes non-printable characters.

```vgr
"five".Repr() → 'five'
5.Repr() → 5
5.0.Repr() → 5.0
["five", 5, 5.0].Repr() → ['five', 5, 5.0]
```

Also see `Ascii()`
"""
    # These are of limited aesthetic value
    if isinstance(x, str) and '"' not in x:
        r = repr(x)
        if r[0] == r[-1] == "'":
            return '"' + r[1:-1] + '"'
        return r
    if isinstance(x, re.Pattern): return poly_repr(x.pattern)
    if isinstance(x, list): return '[' + ', '.join(poly_repr(x1) for x1 in x) + ']'
    return repr(x)

def poly_type(x: Any) -> str:
    """
**Return the internal data type of an item**

* Type(_value_)
* _value_.Type()

For _None_ the value _NoneType_ is returned.

```vgr
None.Type() → "NoneType"
"five".Type() → "str"
5.Type() → "int"
5.0.Type() → "float"
["five", 5, 5.0].Type() → "list"
{"One": 1, "Two": 2}.Type() → "dict"
```
"""
    return type(x).__name__

def poly_sort(x: Any, unique: bool=False, reverse: bool=False) -> Any:
    """
**Sort lists and strings with unique and reverse**

* Sort(_value_)
* Sort(_value_, _unique_)
* Sort(_value_, _unique_, _reverse_)
* _value_.Sort()
* _value_.Sort(_unique_)
* _value_.Sort(_unique_, _reverse_)

```vgr
None.Sort() → None
5.Sort() → 5
5.0.Sort() → 5.0
"dza".Sort() → "adz"
"dza".Sort(False, True) → "zda"
[5.1, 5, 5.0].Sort() → [5, 5.0, 5.1]
["five", 5, 5.0].Sort() → [5, 5.0, "five"]
```

Also see `Unique()`
"""
    unique = False if unique is None else bool_arg(unique, 'Unique')
    reverse = False if reverse is None else bool_arg(reverse, 'Reverse')
    if isinstance(x, str):
        return ''.join(chr(v) for v in poly_sort([ord(ch) for ch in x], unique, reverse))
    if isinstance(x, (list, tuple)):
        rc = list(sorted(x, key=cmp_to_key(_cmp_to_key_asc), reverse=reverse))
        return _unique_sorted(rc) if unique else rc
    return x

def poly_getitem(x:Any, index: Any) -> Any:
    """
**Return the N-th item from a list**

* Item(_value_, _index_)
* _value_.Item(_index_)

For non-list types _value_ is returned unchanged.
If _index_ itself is a list, the corresponding items
will be returned in an list. Index values are zero-based.

Requests for items outside the list's bounds results in _None_.

```vgr
None.Item(0) → None
[].Item(0) → None
[None].Item(0) → None
["apple", "banana", "cantaloupe"].Item(1) → "banana"
["apple", "banana", "cantaloupe"].Item(5) → None
["apple", "banana", "cantaloupe"].Item(-5) → None
"apple".Item(1) → "apple"
5.Item(1) → 5
```

Also see `FirstItem()` and `LastItem()`
"""
    if not isinstance(x, (list, tuple)): return x
    if isinstance(index, (list, tuple)): return dist_x(poly_getitem, x, index)
    i: int = int(index) if isinstance(index, (int, float)) else str_to_number(index) if isinstance(index, str) else None
    return x[i] if i is not None and 0 <= i < len(x) else None

def poly_firstitem(x: Any) -> Any:
    """
**Return the first item from a list**

* FirstItem(_value_)
* _value_.FirstItem()

If the list is empty then _None_ is returned.
For non-list types _value_ is returned unchanged.

```vgr
None.FirstItem() → None
[].FirstItem() → None
[None].FirstItem() → None
["apple", "banana", "cantaloupe"].FirstItem() → "apple"
"apple".FirstItem() → "apple"
5.FirstItem() → 5
```

Also see `Item()` and `LastItem()`
"""
    return poly_getitem(x, 0)

def poly_lastitem(x: Any) -> Any:
    """
**Return the last item from a list**

* LastItem(_value_)
* _value_.LastItem()

If the list is empty then _None_ is returned.
For non-list types _value_ is returned unchanged.

```vgr
None.LastItem() → None
[].LastItem() → None
[None].LastItem() → None
["apple", "banana", "cantaloupe"].LastItem() → "cantaloupe"
"apple".LastItem() → "apple"
5.LastItem() → 5
```

Also see `Item()` and `FistItem()`
"""
    if not isinstance(x, (list, tuple)): return x
    return x[-1] if len(x) > 0 else None

def poly_unique(x: Any) -> Any:
    """
**A unique that works with lists or strings**

* Unique(_value_)
* _value_.Unique()

For strings, a string containing all the unique characters in
the string is returned.
For lists, a list of unique values is returned.
For all other types the value is returned unchanged.

```vgr
None.Unique() → None
[].Unique() → []
[None].Unique() → [None]
"senselessness".Unique() → "senl"
["a", "b", "c", "b"].Unique() → ["a", "b", "c"]
5.Unique() → 5
```

Also see `Sort()`
"""
    if isinstance(x, str): return "".join(dict.fromkeys(x))
    if isinstance(x, (list, tuple)):
        unique = []
        for x1 in x:
            if not any(poly_eq(x1, existing) for existing in unique):
                unique.append(x1)
        return unique
    return x

def dsort(data: dict, keys: list[str], ascending: list[bool], unique: bool, unique_cols: list[str]) -> list:
    """
    Sort by fields in a list of dictionary
    Also unique support
    """
    keys = _check_keys(keys, 'Sort Key')
    if ascending is None or len(ascending) == 0:
        ascending = [True] * len(keys)
    else:
        ascending = _check_sort_dir(ascending)
        if len(ascending) != len(keys):
            raise ValueError('Length of Ascending and Keys must match')
    unique = bool_arg(unique, 'Unique')
    unique_cols = _check_keys(unique_cols, 'Unique Key') if unique else []
    def compare_keys(x: dict, y: dict):
        for key, asc in zip(keys, ascending):
            vx, vy = x.get(key), y.get(key)
            if not asc: vx, vy = vy, vx
            rc = _cmp_to_key_asc(vx, vy)
            if rc != 0: return rc
        return 0
    rc = sorted(data, key=cmp_to_key(compare_keys))
    return _unique_sorted_dict(rc, unique_cols) if unique else rc

def _check_keys(keys: list[str], name: str):
    if keys is None or not keys:
        raise ValueError(f'{name} may not be empty')
    if not isinstance(keys, (list, tuple)):
        raise TypeError(f'For {name} expected list, found {type_str(keys)}')
    for i, s in enumerate(keys):
        if s is None or isinstance(s, (str, int, float)): continue
        raise TypeError(f'{name}[{i}]: expected simple type, found {type_str(s)}')
    return keys

def _check_sort_dir(lst: list[bool]) -> list[bool]:
    if not isinstance(lst, (list, tuple)):
        raise TypeError(f'Sort Direction: expected list, found {type_str(lst)}')
    result = []
    for i, val in enumerate(lst):
        if val is None:
            result.append(False)
        elif isinstance(val, bool):
            result.append(val)
        else:
            raise TypeError(f"Sort Direction[{i}]: expected boolean, found {type_str(val)}")
    return result

def _cmp_to_key_asc(x: Any, y: Any):
    """For ascending comparisons; reverse x/y for descending"""
    return -1 if poly_lt(x, y) else (1 if poly_gt(x, y) else 0)

def _unique_sorted(x: list):
    """Special pupose unique for a sorted iterable"""
    if not x : return x
    unique = [x[0]]
    for curr in x[1:]:
        if poly_ne(curr, unique[-1]):
            unique.append(curr)
    return unique if isinstance(x, list) else list(unique)

def _unique_sorted_dict(x: list, keys: list) -> list:
    """Special pupose unique for a sorted iterable or dictionaries"""
    if not x: return x
    unique = [x[0]]
    for curr in x[1:]:
        prev = unique[-1]
        if any(poly_ne(curr[key], prev[key]) for key in keys):
            unique.append(curr)
    return unique
