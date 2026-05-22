"""
List related functions
"""

from collections.abc import Iterable
from copy import copy
from functools import reduce
from itertools import zip_longest
from typing import Any

from .common import (
    bound_ops,
    int_arg,
    requires_exec_context,
)

from ..vgr_callable import VgrCallable

@bound_ops("[...]")
def build_list(*args: Any) -> list[Any]:
    """
**Create a list from the collected values**

* **[** **]**
* **[** *expression* [, *expression*]&hellip; **]**
* List()
* List(*expression* [, *expression*]&hellip;)

Lists can contain any type including `None`, other lists, and dictionaries.

```vgr
Set empty To []
Set a_none To [None]
Set numbers To [1, 2, 3, 4, 5]
Set names To ["Alice", "Bob", "Charlie"]
Set matrix To [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]
Set records To [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35}
]
Set mixed To [
    42,
    "apple",
    3.14,
    True,
    None,
    {"key": "value"},
    [1, 2, 3]
]

List() → []
List(None) → [None]
List(2, 3, 4) → [2, 3, 4]
List(2, 3, [4]) → [2, 3, [4]]
```

Also see `Append`, `Insert`, `Prepend`, `Remove`, and `Replace` statements,
and the `List()` and `ToList()` functions
"""
    return list(args)

def poly_is_list(x: Any=None) -> bool:
    """
**Is the value a list**

* IsList(*value*)
* *value*.IsList()

```vgr
None.IsList() → False
"list".IsList() → False
[].IsList() → True
{}.IsList() → False
```

Also see `ToList()`
"""
    return isinstance(x, list)

def poly_list(x: Any=None) -> list:
    """
**Converts a value to a list**

* ToList(*value*)
* *value*.ToList()

Dictionaries are converted to a list of key/value pairs.
If *value* is `None` an empty list is returned.

```vgr
Set fruits To ["apple", "banana", "apple", "orange", "apple"]
Set fruit_colors To {"apple": "red", "banana": "yellow"}
None.ToList() → []
"list".ToList() → ["list"]
fruits.ToList() → ["apple", "banana", "apple", "orange", "apple"]
fruit_colors.ToList() → [["apple", "red"], ["banana", "yellow"]]
```

Also see `IsList()`
"""
    if x is None: return []
    if isinstance(x, list): return x
    if isinstance(x, dict): return [[key, x[key]] for key in sorted(x)] if x else []
    return [x]

def poly_list_append(*args) -> list:
    """
**Adds items to the end of a list**

* ListAppend(_list_, *value*&hellip;)
* _list_.ListAppend(*value*&hellip;)

If applied to a value that is not already a list, it is converted using `ToList()`.
A modified copy of the list is returned.

```vgr
Set fruits To ["apple", "banana", "orange"]
None.ListAppend() → []
None.ListAppend(None) → [None]
None.ListAppend("cantoloupe") → ["cantoloupe"]
None.ListAppend(["cantoloupe", "pear"]) → [["cantoloupe", "pear"]]
"apple".ListAppend("cantoloupe") → ["apple", "cantoloupe"]
fruits.ListAppend("cantoloupe", "pear")
    → ["apple", "banana", "orange", "cantoloupe", "pear"]
```

Also see `ListPrepend()`
and the `Append` statement, which acts directly on a variable
"""
    if not args: return []
    x: list = copy(poly_list(args[0]))
    for arg in args[1:]: x.append(arg)
    return x

def poly_list_prepend(*args) -> list:
    """
**Adds items to the start of a list**

* ListPrepend(_list_, *value*&hellip;)
* _list_.ListPrepend(*value*&hellip;)

If applied to a value that is not already a list, it is converted using `ToList()`.
A modified copy of the list is returned.

```vgr
Set fruits To ["apple", "banana", "orange"]
None.ListPrepend() → []
None.ListPrepend(None) → [None]
None.ListPrepend("cantoloupe") → ["cantoloupe"]
None.ListPrepend(["cantoloupe", "pear"]) → [["cantoloupe", "pear"]]
"apple".ListPrepend("cantoloupe") → ["cantoloupe", "apple"]
fruits.ListPrepend("cantoloupe", "pear")
    → ["cantoloupe", "pear", "apple", "banana", "orange"]
```

Also see `ListAppend()`
and the `Prepend` statement, which acts directly on a variable
"""
    if not args: return []
    x: list = copy(poly_list(args[0]))
    index = 0
    for arg in args[1:]:
        x.insert(index, arg)
        index += 1
    return x

def poly_list_remove_first(x: Any=None) -> list:
    """
**Removes the first item from a list**

* ListRemoveFirst(_list_)
* _list_.ListRemoveFirst()

If applied to a value that is not already a list, it is converted using `ToList()`.
A modified copy of the list is returned.

```vgr
Set fruits To ["apple", "banana", "orange"]
None.ListRemoveFirst() → []
"apple".ListRemoveFirst() → []
fruits.ListRemoveFirst() → ["banana", "orange"]
```

Also see `ListRemoveLast()`, `ListRemove()`,
and the`Remove` statement, which acts directly on a variable
"""
    x: list = copy(poly_list(x))
    if len(x) > 0: x.pop(0)
    return x

def poly_list_remove_last(x: Any=None) -> list:
    """
**Removes the last item from a list**

* ListRemoveLast(_list_)
* _list_.ListRemoveLast()

If applied to a value that is not already a list, it is converted using `ToList()`.
A modified copy of the list is returned.

```vgr
Set fruits To ["apple", "banana", "orange"]
None.ListRemoveLast() → []
"apple".ListRemoveLast() → []
fruits.ListRemoveLast() → ["apple", "banana"]
```

Also see `ListRemoveFirst()`, `ListRemove()`,
and the`Remove` statement, which acts directly on a variable
"""
    x: list = copy(poly_list(x))
    if len(x) > 0: x.pop()
    return x

def poly_list_remove(x: Any=None, index: int=0) -> list:
    """
**Removes an item from a list by index**

* ListRemove(_list_, *index*)
* _list_.ListRemove(*index*)

If applied to a value that is not already a list, it is converted using `ToList()`.
If *index* is out of range, the operation is ignored.
A modified copy of the list is returned.

```vgr
Set fruits To ["apple", "banana", "orange"]
None.ListRemove(0) → []
"apple".ListRemove(0) → []
fruits.ListRemove(1) → ["apple", "orange"]
fruits.ListRemove(-1) → ["apple", "banana", "orange"]
fruits.ListRemove(5) → ["apple", "banana", "orange"]
```

Also see `ListRemoveFirst()`, `ListRemoveLast()`,
and the `Remove` statement, which acts directly on a variable
"""
    x: list = poly_list(x)
    if index is not None:
        index = int_arg(index, "Index")
        if 0 <= index < len(x):
            x = copy(x)
            x.pop(index)
    return x

def poly_list_replace(x: Any=None, index: Any=0, value: Any=None) -> list:
    """
**Replace an item in a list by index**

* ListReplace(_list_, *index*, *value*)
* _list_.ListRemove(*index*, *value*)

If applied to a value that is not already a list, it is converted using `ToList()`.
If *index* is out of range, the operation is ignored.
A modified copy of the list is returned.

```vgr
Set fruits To ["apple", "banana", "orange"]
None.ListReplace(0, "cantoloupe") → []
"apple".ListReplace(0, None) → [None]
"apple".ListReplace(0, "cantoloupe") → ["cantoloupe"]
fruits.ListReplace(2, "cantoloupe") → ["apple", "banana", "cantoloupe"]
fruits.ListReplace(None, "cantoloupe") → ["apple", "banana", "orange"]
fruits.ListReplace(-1, "cantoloupe") → ["apple", "banana", "orange"]
fruits.ListReplace(5, "cantoloupe") → ["apple", "banana", "orange"]
```

Also see `ListInsert()`
and the `Replace` statement, which acts directly on a variable
"""
    x: list = poly_list(x)
    if index is not None:
        index = int_arg(index, "Index")
        if 0 <= index <= len(x):
            x = copy(x)
            x[index] = value
    return x

def poly_list_insert(*args) -> list:
    """
**Insert items into a list by index**

* ListInsert(_list_, *index*, *value*&hellip;)
* _list_.ListInsert(*index*, *value*&hellip;)

If applied to a value that is not already a list, it is converted using `ToList()`.
If *index* is out of range, the operation is ignored.
A modified copy of the list is returned.

```vgr
Set fruits To ["apple", "banana", "orange"]
None.ListInsert(0, "cantoloupe") → []
"apple".ListInsert(0, None) → [None, "apple"]
"apple".ListInsert(0, "cantoloupe") → ["cantoloupe", "apple"]
fruits.ListInsert(2, "cantoloupe") →
    ["apple", "banana", "cantoloupe", "orange"]
fruits.ListInsert(2, "cantoloupe", "pear") →
    ["apple", "banana", "cantoloupe", "pear", "orange"]
fruits.ListInsert(None, "cantoloupe") → ["apple", "banana", "orange"]
fruits.ListInsert(-1, "cantoloupe") → ["apple", "banana", "orange"]
fruits.ListInsert(5, "cantoloupe") → ["apple", "banana", "orange"]
```

Also see `ListReplace()`
and the `Insert` statement, which acts directly on a variable
"""
    x, index = (args + (None, 0))[:2]
    values = args[2:]
    x: list = poly_list(x)
    if index is not None:
        index = int_arg(index, "Index")
        if 0 <= index <= len(x):
            x = copy(x)
            for value in values:
                x.insert(index, value)
                index += 1
    return x

@requires_exec_context
def poly_apply(x: Any, funct, *args, ctx=None) -> Any:
    """
**Applies one or more user defined functions to a value or a list of values**

* Apply(*value*, _function_ [, *arg*&hellip;])
* *value*.Apply(_function_ [, *arg*&hellip;])

When *value* is a list, each value within it is passed to _function_. Additional arguments, if
any, passed following it.
When not a list, *value* is passed as the first argument to _function_ followed by any additional
arguments.
If _function_ is not a user defined function, it acts as a function returning that value.
If _function_ is a list, the functions within it are executed in order, chaining their results.
The same additional arguments are passed to all functions, which may use or ignore as appropriate.

```vgr
Set by_two(x) -> x * 2
None.Apply(by_two) → None
5.Apply(by_two) → 10
5.Apply(None) → None
5.Apply(6) → 6
[5, 6].Apply(by_two) → [10, 12]

Set adder(x, y, z) -> x + y + z
6.Apply(adder) → 6
6.Apply(adder, 2) → 8
6.Apply(adder, 2, 3) → 11
6.Apply(adder, 2, 3, 4) → 11

Set v_adder() -> Sum($args)
6.Apply(v_adder, 2, 3, 4) → 15
[0, 1, 2].Apply(v_adder, 4, 5, 6) → [15, 16, 17]

[5, 6].Apply([adder, by_two], 5, 6) → [32, 34]
[5, 6].Apply([by_two, adder], 5, 6) → [21, 23]

Set slen(x, default_value) -> Type(x) Is "str" ? StringLen(x) : default_value.DefaultTo(0)
["hello", "world", 5].Length() → 3
["hello", "world", 5].StringLen() → [5, 5, None]
["hello", "world", 5].Apply(slen) → [5, 5, 0]
["hello", "world", 5].Apply(slen, -1) → [5, 5, -1]
```

Also see `CombineUsing()`
"""
    def _apply_it(value: Any, f) -> Any:
        if isinstance(f, VgrCallable): return f.evaluate(ctx, [value, *args])
        if isinstance(f, list): return reduce(_apply_it, f, value)
        return f
    return [_apply_it(x1, funct) for x1 in x] if isinstance(x, list) else _apply_it(x, funct)

@requires_exec_context
def poly_combine_using(x: Any, funct, *args, **kwargs) -> Any:
    """
**Combine values into a single value using a user defined function**

* CombineUsing(*value*, _function_ [, _initial_value_ [, *arg*&hellip;]])
* *value*.CombineUsing(_function_ [, _initial_value_ [, *arg*&hellip;]])

When *value* is a list, each value within it is passed to _function_. Additional arguments, if
any, passed following it.
When not a list, *value* is passed as the first argument to _function_ followed by any additional
arguments.

The signature for _function_ should be _f(accumulator, value [,args])_ where
_accumulator_ is the result of previous calls, starting with _initial_value_.
The default value for _initial_value_ is `None`, and while optional,
depending upon the operations within _function_, you may need to
specify a starting value.

```vgr
Set add_it(acc, value) -> acc + value
None.CombineUsing(add_it) → None
5.CombineUsing(None) → None
5.CombineUsing(add_it) → 5
5.CombineUsing(6) → 6
[5, 6].CombineUsing(add_it) → 11

Set f(acc, value, scale) -> acc + (value * scale.DefaultTo(1))
2.CombineUsing(f) → 2
2.CombineUsing(f, 0) → 2
2.CombineUsing(f, 0, 2) → 4
2.CombineUsing(f, 0, .5) → 1.0

Set double_it(n) -> n * 2
Set get_count(d, default_value) -> d.GetKeyValue("count", default_value)
Set sum_positive(acc, n) -> n >= 0 ? acc + n : acc
Set counters To [
    { "name": "a", "count": 5 },
    { "name": "b" },
    { "name": "c", "count": 3 }
]
counters.
    Apply(get_count, -1).
    Apply(double_it).
    CombineUsing(sum_positive) → 16
```

Also see `Apply()`
"""
    ctx = kwargs.pop("ctx")
    if args:
        acc, *args = args
    else:
        acc, args = None, []
    def _combine_it(a: Any, value: Any) -> Any:
        if isinstance(funct, VgrCallable): return funct.evaluate(ctx, [a, value, *args])
        return funct
    if isinstance(x, list):
        for x1 in x: acc = _combine_it(acc, x1)
        return acc
    return _combine_it(acc, x)

def poly_combine_lists(*args) -> list:
    """
**Combine elements of collections into a list of lists**

* CombineLists(_expresssion_ [,*expression*&hellip;])
* *value*.CombineLists(_expresssion_ [,*expression*&hellip;])

Combines the elements of the listed collections into an array of arrays.
Each element will have the Nth matching values joined together.
If the lists are of unequal length, values of `None` are used for the
missing items.

```vgr
CombineLists(None) → [[None]]
CombineLists([], []) → []
CombineLists([], [1, 2]) → [[None, 1], [None, 2]]
CombineLists([1, 2], [3, 4]) → [[1, 3], [2, 4]]
CombineLists([1], [10, 20, 30]) → [[1, 10], [None, 20], [None, 30]]
CombineLists([1, 2], ["a", "b"], [True, False]) → [[1, "a", True], [2, "b", False]]
CombineLists(5, 10) → [[5, 10]]
CombineLists(1, [2, 3]) → [[1, 2], [None, 3]]
CombineLists([None], [1, 2]) → [[None, 1], [None, 2]]
CombineLists([1, 2, 3]) → [[1], [2], [3]]
```
"""
    def normalize(x):
        return x if isinstance(x, Iterable) and not isinstance(x, (str, bytes, bytearray)) else [x]
    if not args: return []
    iterables = [normalize(args[0])] + [normalize(arg) for arg in args[1:]]
    return list(map(list, zip_longest(*iterables)))
