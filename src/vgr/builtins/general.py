from copy import copy
from functools import (
    cmp_to_key,
    reduce,
)
from typing import Any

from .common import (
    apply_vargs,
    bool_arg,
    int_arg,
    str_to_int,
    unpack_vargs,
)
from .inequ import (
    poly_eq,
    poly_gt,
    poly_lt,
    poly_ne,
)
from .type import poly_type
from .registry import builtin
from .vpattern import VPattern

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
        if isinstance(x, VPattern): x = x.pattern
        if isinstance(x, str): return x[::-1]
        return x
    return apply_vargs(args, _op)

@builtin("Negate")
def poly_negate(*args: Any) -> Any:
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
def poly_length(*args: Any) -> Any:
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
        if isinstance(x, VPattern): x = x.pattern
        return len(x) if hasattr(x, '__len__') else None
    return apply_vargs(args, _op)

@builtin("Hash")
def poly_hash(*args: Any) -> int:
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
def poly_id(*args: Any) -> Any:
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
def poly_clone(*args: Any) -> Any:
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
def poly_repr(*args: Any) -> str:
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
    def _op(x):
        # These are of limited aesthetic value
        if isinstance(x, str) and '"' not in x:
            r = repr(x)
            if r[0] == r[-1] == "'":
                return '"' + r[1:-1] + '"'
            return r
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

@builtin("Item")
def poly_get_item(*args: Any) -> Any:
    """
**Return the N-th item from a list**

* Item(*value*, *index*&hellip;)
* *value*.Item(*index*&hellip;)
* *value*[*index*]

For non-list/string *value*s the value is returned unchanged.
Index values are zero-based.
Requests for items outside a list's bounds results in `None`.
Requests for items outside a strings's bounds results in an empty string.

```vgr
None.Item(0) → None
5.Item(1) → 5
[].Item(0) → None
[None].Item(0) → None
["apple", "banana", "cantaloupe"].Item(1) → "banana"
["apple", "banana", "cantaloupe"].Item(5) → None
["apple", "banana", "cantaloupe"].Item(-2) → "banana"
["apple", "banana", "cantaloupe"].Item(-5) → None
"apple".Item(1) → "p"
["apple", "banana", "cantaloupe"].Item(0,1) → "p"
```

Also see `FirstItem()` and `LastItem()`
"""
    def _item(x: Any, index: Any) -> Any:
        # A number becomes an int, strings coerced, None becomes 0
        if index is None:
            index: int = 0
        else:
            index: int = int(index) if isinstance(index, (int, float)) else str_to_int(index) if isinstance(index, str) else 0
            if index is None: index = 0
        if isinstance(x, str):
            # in-range returns the character, out of range returns empty string
            length: int = len(x)
            if index >= 0: return x[index] if index < length else ''
            return x[index] if length >= abs(index) else ''
        if isinstance(x, list):
            # in-range returns the element, out of range returns None
            length: int = len(x)
            if index >= 0: return x[index] if index < length else None
            return x[index] if length >= abs(index) else None
        return x
    # args is a list of indicies to be sequentially dereferenced
    value, args = unpack_vargs(args, 1)
    return reduce(_item, args, value)

@builtin("FirstItem")
def poly_first_item(*args: Any) -> Any:
    """
**Return the first item from a list**

* FirstItem(*value*&hellip;)
* *value*.FirstItem()
* *value*[0]

If the list is empty then `None` is returned.
For non-list types *value* is returned unchanged.

```vgr
None.FirstItem() → None
5.FirstItem() → 5
[].FirstItem() → None
[None].FirstItem() → None
["apple", "banana", "cantaloupe"].FirstItem() → "apple"
"apple".FirstItem() → "a"
FirstItem("apple", "banana", "cantaloupe") → ["a", "b", "c"]
```

Also see `Item()` and `LastItem()`
"""
    return apply_vargs(args, lambda x: poly_get_item(x, 0))

@builtin("LastItem")
def poly_last_item(*args: Any) -> Any:
    """
**Return the last item from a list**

* LastItem(*value*&hellip;)
* *value*.LastItem()
* *value*[-1]

If the list is empty then `None` is returned.
For non-list types *value* is returned unchanged.

```vgr
None.LastItem() → None
5.LastItem() → 5
[].LastItem() → None
[None].LastItem() → None
["apple", "banana", "cantaloupe"].LastItem() → "cantaloupe"
"apple".LastItem() → "e"
LastItem("apple", "banana", "cantaloupe") → ["e", "a", "e"]
```

Also see `Item()` and `FirstItem()`
"""
    return apply_vargs(args, lambda x: poly_get_item(x, -1))

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
