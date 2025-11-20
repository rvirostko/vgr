"""
List related functions
"""

from collections.abc import Iterable
from copy import copy
from functools import reduce
from itertools import zip_longest
from typing import Any

from .common import (
    int_arg,
    requires_exec_context,
)

from ..vgr_callable import VgrCallable

def poly_islist(x: Any) -> bool:
    """
**Returns _True_ if the value is a list**

* IsList(_value_)
* _value_.IsList()

```vgr
None.IsList() → False
"list".IsList() → False
[].IsList() → True
{}.IsList() → False
```

Also see `ToList()`
"""
    return isinstance(x, (list, tuple))

def poly_list_create(*args) -> list:
    """
**Create and/or initialize a list**

* List(_value_...)
* **[** _value_... **]**

The items in the list may be constants, expressions, or _None_,
and include other lists and dictionaries.

```vgr
List() → []
List(None) → [None]
List(2, 3, 4) → [2, 3, 4]
List(2, 3, [4]) → [2, 3, [4]]
```

Also see `ToList()` and `IsList()`
"""
    return list(args)

def poly_list(x: Any) -> list:
    """
**Converts a value to a list**

* ToList(_value_)
* _value_.ToList()

Dictionaries are converted to a list of key/value pairs.
If _value_ is _None_ an empty list is returned.

```vgr
Set fruits To ["apple", "banana", "apple", "orange", "apple"]
Set fruit_colors To {"apple": "red", "banana": "yellow"}
None.ToList() → []
"list".ToList() → ["list"]
fruits.ToList() → ["apple", "banana", "apple", "orange", "apple"]
fruit_colors.ToList() → [["apple", "red"], ["banana", "yellow"]]

Also see `IsList()`
```
"""
    if x is None: return []
    if isinstance(x, list): return x
    if isinstance(x, tuple): return [*x] if x else []
    if isinstance(x, dict): return [[key, x[key]] for key in sorted(x)] if x else []
    return [x]

def poly_list_append(x: Any, *args) -> list:
    """
**Adds items to the end of a list**

* ListAppend(_list_, _value_...)
* _list_.ListAppend(_value_...)

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
    x: list = copy(poly_list(x))
    for arg in args: x.append(arg)
    return x

def poly_list_prepend(x: Any, *args) -> list:
    """
**Adds items to the start of a list**

* ListPrepend(_list_, _value_...)
* _list_.ListPrepend(_value_...)

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
    x: list = copy(poly_list(x))
    index = 0
    for arg in args:
        x.insert(index, arg)
        index += 1
    return x

def poly_list_remove_first(x: Any) -> list:
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

def poly_list_remove_last(x: Any) -> list:
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

def poly_list_remove(x: Any, index: int=0) -> list:
    """
**Removes an item from a list by index**

* ListRemove(_list_, _index_)
* _list_.ListRemove(_index_)

If applied to a value that is not already a list, it is converted using `ToList()`.
If _index_ is out of range, the operation is ignored.
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

def poly_list_replace(x: Any, index, value: Any=None) -> list:
    """
**Replace an item in a list by index**

* ListReplace(_list_, _index_, _value_)
* _list_.ListRemove(_index_, _value_)

If applied to a value that is not already a list, it is converted using `ToList()`.
If _index_ is out of range, the operation is ignored.
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
        if 0 <= index < len(x):
            x = copy(x)
            x[index] = value
    return x

def poly_list_insert(x: Any, index, *values) -> list:
    """
**Insert items into a list by index**

* ListInsert(_list_, _index_, _value_...)
* _list_.ListInsert(_index_, _value_...)

If applied to a value that is not already a list, it is converted using `ToList()`.
If _index_ is out of range, the operation is ignored.
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
    x: list = poly_list(x)
    if index is not None:
        index = int_arg(index, "Index")
        if 0 <= index < len(x):
            x = copy(x)
            for value in values:
                x.insert(index, value)
                index += 1
    return x

@requires_exec_context
def poly_apply(x: Any, funct, *args, ctx=None) -> Any:
    """
**Applies one or more user defined functions to a value or a list of values**

* Apply(_value_, _function_ [, _arg_...])
* _value_.Apply(_function_ [, _arg_...])

When _value_ is a list, each value within it is passed to _function_. Additional arguments, if
any, passed following it.
When not a list, _value_ is passed as the first argument to _function_ followed by any additional
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

Set slen(x, default_value) -> Type(x) Is "str" ? StrLen(x) : default_value.DefaultTo(0)
["hello", "world", 5].Length() → 3
["hello", "world", 5].StrLen() → [5, 5, None]
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

* CombineUsing(_value_, _function_ [, _initial_value_ [, _arg_...]])
* _value_.CombineUsing(_function_ [, _initial_value_ [, _arg_...]])

When _value_ is a list, each value within it is passed to _function_. Additional arguments, if
any, passed following it.
When not a list, _value_ is passed as the first argument to _function_ followed by any additional
arguments.

The signature for _function_ should be _f(accumulator, value [,args])_ where
_accumulator_ is the result of previous calls, starting with _initial_value_.
The default value for _initial_value_ is _None_, and while optional,
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
Set counters = [
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

# TODO rename and move to lists
def poly_combine_lists(first: Any, *rest) -> Any:
    """
**Combine elements of collections into a list of lists**

* CombineLists(_expresssion_ [,_expression_...])
* _value_.CombineLists(_expresssion_ [,_expression_...])

Combines the elements of the listed collections into an array of arrays.
Each element will have the Nth matching values joined together.
If the lists are of unequal length, values of _None_ are used for the
missing items.

```vgr
**TODO**
```
"""
    def normalize(x):
        return x if isinstance(x, Iterable) and not isinstance(x, (str, bytes, bytearray)) else [x]
    iterables = [normalize(first)] + [normalize(arg) for arg in rest]
    return list(map(list, zip_longest(*iterables)))
