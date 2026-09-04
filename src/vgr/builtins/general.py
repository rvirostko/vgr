from copy import copy
from functools import cmp_to_key
from typing import Any
from re import Pattern

from .common import (
    apply_vargs,
    bool_arg,
    dist_x,
    int_arg,
    str_to_int,
)
from .dict import poly_get_key_value
from .inequ import (
    poly_eq,
    poly_gt,
    poly_lt,
    poly_ne,
)
from .strings import poly_substr
from .type import poly_type
from .registry import builtin

@builtin("Reverse")
def poly_reverse(*args) -> Any:
    """
**Reverses the contents of a list or string**

* Reverse(*value*)
* *value*.Reverse()

If *value* is an ordinal rather than a list, it is returned unchanged.

```vgr
"five".Reverse() → "evif"
5.Reverse() → 5
5.0.Reverse() → 5.0
["five", 5, 5.0].Reverse() → [5.0, 5, "five"]
"One Two".Reverse() → "owT enO"
```
"""
    def _op(x):
        if isinstance(x, list): return list(reversed(x))
        if isinstance(x, Pattern): x = x.pattern
        if isinstance(x, str): return x[::-1]
        return x
    return apply_vargs(args, _op)

@builtin("Negate")
def poly_negate(*args) -> Any:
    """
**Returns the negation of a value**

* Negate(*value*)
* *value*.Negate()

The *value*'s type determines what is returned:

* `None` : always returns `True`
* String : returns *value* unchanged
* Boolean : returns the logical negation
* Int and Float : return the arithmetic negation
* Lists and Dictionaries : distributed negation

```vgr
None.Negate() → True
5.Negate() → -5
5.1.Negate() → -5.1
[5, 10, 15].Negate() → [-5, -10, -15]
{"c": "sea", "b": True, "a": 1}.Negate() → {"c": "sea", "b": False, "a": -1}
```
"""
    def _op(x):
        if x is None: return True
        if isinstance(x, bool): return not x
        if isinstance(x, (int, float)): return -x
        if isinstance(x, list): return list(poly_negate(x1) for x1 in x)
        if isinstance(x, dict): return {k: poly_negate(v) for k, v in x.items()}
        return x
    return apply_vargs(args, _op)

@builtin("Length")
def poly_length(*args) -> Any:
    """
**Return the length of an an item**

* Length(*value*)
* *value*.Length()

Returns the length of lists and strings.
For dictionaries, the number of attributes is returned.
For all other values `None` is returned.

```vgr
None.Length() → None
5.Length() → None
5.1.Length() → None
[5, 10, 15].Length() → 3
"frog".Length() → 4
{"c": "sea", "b": True, "a": 1}.Length() → 3
```

Also see `StringLen()`
"""
    def _op(x):
        if isinstance(x, Pattern): x = x.pattern
        return len(x) if hasattr(x, '__len__') else None
    return apply_vargs(args, _op)

@builtin("Hash")
def poly_hash(*args) -> int:
    """
**Returns the internal hashcode for an object**

* Hash(*value*)
* *value*.Hash()

This can be used in debugging but is of limited values in scripts.
Cannot be applied to lists or dictionaries.

```vgr
"five".Hash() → -3781267357408442496
5.Hash() → 5
5.0.Hash() → 5
```

Also see `Id()`
"""
    def _op(x): return None if isinstance(x, (list, dict)) else hash(x)
    return apply_vargs(args, _op)

@builtin("Id")
def poly_id(*args) -> Any:
    """
**Returns the internal, unique ID used by the value**

* Id(*value*)
* *value*.Id()

This can be used in debugging but is of limited values in scripts.

```vgr
None.Id() → 4387076688
5.Id() → 4374194608
5.1.Id() → 4669058608
[5, 10, 15].Id() → 4682578560
"frog".Id() → 4682576368
{"c": "sea", "b": True, "a": 1}.Id() → 4682896960
```

Also see `Hash()`
"""
    return apply_vargs(args, id)

@builtin("Clone")
def poly_clone(*args) -> Any:
    """
**Ceates a copy of complex objects**

* Clone(*value*)
* *value*.Clone()

Only lists and dictionaries are cloned, as other
data types are not mutable in the same sense as
collections. This operation clones the container: if the
values within it are complex objects, their values will
still be shared.

***Simple types return the same object***

```vgr
Set x To 5
Print x.Id(), x.Clone().Id()
4335020464 4335020464 // same object
```

***Cloning a complex object***

```vgr
Set y To [1,2,3]
Print y.Id(), y.Clone().Id()
4808334400 4807906688 // different objects
```

***Container is cloned, but complex objects are shared***

```vgr
Set z To [ {"a" : 1} ]
Set z′ To z.Clone()
Print z.Id(), z′.Id()
4810281856 4708798208 // different lists
Print z.FirstItem().Id(), z′.FirstItem().Id()
4502192256 4502192256 // same contents
```

Also see `Id()` and `Hash()`
"""
    def _op(x): return copy(x) if isinstance(x, (list, dict)) else x
    return apply_vargs(args, _op)

@builtin("Repr")
def poly_repr(*args) -> str:
    """
**Returns a string representation of an item**

* Repr(*value*)
* *value*.Repr()

Differs slightly from `ToString()` as it surrounds string values with quotes
and escapes non-printable characters.

```vgr
"five".Repr() → '"five"'
5.Repr() → '5'
5.0.Repr() → '5.0'
["five", 5, 5.0].Repr() → ['"five"', '5', '5.0']
```
"""
    import re
    def _decode_flags(x: Pattern) -> str:
        rc = ''
        f = x.flags
        if f > 0:
            if f & re.A: rc += 'a'
            if f & re.DEBUG: rc += 'd'
            if f & re.I: rc += 'i'
            # re.L unlikely since it can only be used with bytes
            if f & re.M: rc += 'm'
            if f & re.S: rc += 's'
            # We don't support templates (re.T)
            # If not re.A, then re.U, so we skip it
            if f & re.X: rc += 'x'
        return rc
    def _op(x):
        # These are of limited aesthetic value
        if isinstance(x, str) and '"' not in x:
            r = repr(x)
            if r[0] == r[-1] == "'":
                return '"' + r[1:-1] + '"'
            return r
        if isinstance(x, Pattern):
            # NB: there are probably escaping issue with "/"
            #     inside the pattern...
            return 'r/' + x.pattern + '/' + _decode_flags(x)
        if isinstance(x, list): return '[' + ', '.join(poly_repr(x1) for x1 in x) + ']'
        return repr(x)
    return apply_vargs(args, _op)

@builtin("Enumerate")
def poly_enumerate(obj: Any=None, start_at: int=0) -> Any:
    """
**Create an enumeration for a collection**

* Enumerate(*value*)
* Enumerate(*value*, *start_at*)
* *value*.Enumerate()
* *value*.Enumerate(*start_at*)

The *start_at* argument defines the number used in the enumerated value.
The default value for *start_at* is zero.
Enumeration of values that are not collections produces an enumeration of a single entry.
Enumerating `None` returns an empty list.

```vgr
None.Enumerate() → []
5.Enumerate() → [[0, 5]]
[5].Enumerate() → [[0, 5]]
[5].Enumerate(-3) → [[-3, 5]]
math.float.Enumerate(1) → [[1, "max", 1.7976931348623157e+308],
    [2, "min", 2.2250738585072014e-308]]
```
"""
    if obj is None: return []
    start_at = int_arg(start_at, "StartAt")
    if isinstance(obj, dict):
        return [[i, k, v] for i, (k, v) in enumerate(obj.items(), start=start_at)]
    if isinstance(obj, list):
        return [[i, x] for i, x in enumerate(obj, start=start_at)]
    return [[start_at, obj]]

@builtin("Sort")
def poly_sort(x: Any=None, unique: bool=False, reverse: bool=False) -> Any:
    """
**Sort lists and strings with unique and reverse**

* Sort(*value*)
* Sort(*value*, _unique_)
* Sort(*value*, _unique_, _reverse_)
* *value*.Sort()
* *value*.Sort(_unique_)
* *value*.Sort(_unique_, _reverse_)

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
    if isinstance(x, list):
        rc = list(sorted(x, key=cmp_to_key(_cmp_to_key_asc), reverse=reverse))
        return _unique_sorted(rc) if unique else rc
    return x

def poly_subscript(x:Any=None, index: Any=None) -> Any:
    if isinstance(x, (list, str)): return poly_get_item(x, index)
    if isinstance(x, dict): return poly_get_key_value(x, index)
    return x

@builtin("Item")
def poly_get_item(x:Any=None, index: Any=0) -> Any:
    """
**Return the N-th item from a list**

* Item(*value*, *index*)
* *value*.Item(*index*)
* *value*[*index*]

For non-list types *value* is returned unchanged.
If *index* itself is a list, the corresponding items
will be returned in an list. Index values are zero-based.

Requests for items outside the list's bounds results in `None`.

```vgr
None.Item(0) → None
[].Item(0) → None
[None].Item(0) → None
["apple", "banana", "cantaloupe"].Item(1) → "banana"
["apple", "banana", "cantaloupe"].Item(5) → None
["apple", "banana", "cantaloupe"].Item(-2) → "banana"
["apple", "banana", "cantaloupe"].Item(-5) → None
"apple".Item(1) → "p"
5.Item(1) → 5
```

Also see `FirstItem()` and `LastItem()`
"""
    if isinstance(x, str): return poly_substr(x, index)
    if not isinstance(x, list): return x
    if isinstance(index, list): return dist_x(poly_get_item, x, index)
    i: int = int(index) if isinstance(index, (int, float)) else str_to_int(index) if isinstance(index, str) else None
    if i is None: i = 0
    l = len(x)
    if i >= 0: return x[i] if i < l else None
    return x[i] if l >= abs(i) else None

@builtin("FirstItem")
def poly_first_item(x: Any=None) -> Any:
    """
**Return the first item from a list**

* FirstItem(*value*)
* *value*.FirstItem()
* *value*[0]

If the list is empty then `None` is returned.
For non-list types *value* is returned unchanged.

```vgr
None.FirstItem() → None
[].FirstItem() → None
[None].FirstItem() → None
["apple", "banana", "cantaloupe"].FirstItem() → "apple"
"apple".FirstItem() → "a"
5.FirstItem() → 5
```

Also see `Item()` and `LastItem()`
"""
    return poly_get_item(x, 0)

@builtin("LastItem")
def poly_last_item(x: Any=None) -> Any:
    """
**Return the last item from a list**

* LastItem(*value*)
* *value*.LastItem()
* *value*[-1]

If the list is empty then `None` is returned.
For non-list types *value* is returned unchanged.

```vgr
None.LastItem() → None
[].LastItem() → None
[None].LastItem() → None
["apple", "banana", "cantaloupe"].LastItem() → "cantaloupe"
"apple".LastItem() → "e"
5.LastItem() → 5
```

Also see `Item()` and `FirstItem()`
"""
    return poly_get_item(x, -1)

@builtin("Unique")
def poly_unique(x: Any=None) -> Any:
    """
**A unique that works with lists or strings**

* Unique(*value*)
* *value*.Unique()

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
    if isinstance(x, list):
        unique = []
        for x1 in x:
            if not any(poly_eq(x1, existing) for existing in unique):
                unique.append(x1)
        return unique
    return x

def dsort(data: dict, keys: list[str], ascending: list[bool], unique: bool, unique_cols: list[str]) -> list:
    """
    Sort by fields in a list of dictionaries
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
    if not isinstance(keys, list):
        raise TypeError(f'For {name} expected list, found {poly_type(keys)!r}')
    for i, s in enumerate(keys):
        if s is None or isinstance(s, (str, int, float)): continue
        raise TypeError(f'{name}[{i}]: expected simple type, found {poly_type(s)!r}')
    return keys

def _check_sort_dir(lst: list[bool]) -> list[bool]:
    if not isinstance(lst, list):
        raise TypeError(f'Sort Direction: expected list, found {poly_type(lst)!r}')
    result = []
    for i, val in enumerate(lst):
        if val is None:
            result.append(False)
        elif isinstance(val, bool):
            result.append(val)
        else:
            raise TypeError(f"Sort Direction[{i}]: expected boolean, found {poly_type(val)!r}")
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
