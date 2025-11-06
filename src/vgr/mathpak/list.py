"""
List related functions
"""

from copy import copy
from typing import Any

from .common import int_arg

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
