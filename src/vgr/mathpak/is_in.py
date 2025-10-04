"""
Implementations of an "in", "not in", "contains any" and "contains all" functions.
These can work on collections, dictionaries, strings and to some extent
scalar values.
"""

from typing import Any

from .common import NoneType, bound_ops, type_str
from .inequ import poly_eq

@bound_ops("IsIn")
def poly_in(x: Any, y: Any) -> bool:
    """
**Is a value contained in another value or collection**

* _value_.IsIn(_expression_)
* _value_ Is In _expression_
* _value_ ∈ _expression_

```vgr
None.IsIn(None) → True
None.IsIn("cat") → False

2 Is In 2 → True // equality
2 Is In 20 → False

Set animals To ["cat", "dog", "fish"]
"cat".IsIn(None) → False
"cat" Is In animals → True
["cat", "frog"] Is In animals → True  // cat or frog in animals
["rat", "frog"] Is In animals → False // neither in animals
"do".IsIn("dog") → True               // string operation
"do".IsIn(animals) → False            // list operation

Set point To {"x": 5, "y": 10}
"x" Is In point → True  // key in dictionary
"z" Is In point → False // key not in dictionary
```

Also see `IsNotIn()` and `ContainsAny()`
"""
    return _is_in(x, y, False)

@bound_ops("Not-In", "Is-Not-In")
def poly_not_in(x: Any, y: Any) -> Any:
    """
**Is a value _not_ contained in another value or collection**

* _value_.IsNotIn(_expression_)
* _value_ Is Not In _expression_
* _value_ ∉ _expression_

```vgr
None.IsNotIn(None) → False
None.IsNotIn("cat") → True

2 Is Not In 2 → False // inequality
2 Is Not In 20 → True

Set animals To ["cat", "dog", "fish"]
"cat".IsNotIn(None) → True
"cat" Is Not In animals → False
["cat", "frog"] Is Not In animals → False // not cat and not frog in animals
["rat", "frog"] Is Not In animals → True  // neither in animals
"do".IsNotIn("dog") → False               // string operation
"do".IsNotIn(animals) → True              // list operation

Set point To {"x": 5, "y": 10}
"x" Is Not In point → False // key in dictionary
"z" Is Not In point → True  // key not in dictionary
```

Also see `IsIn()`
"""
    return not _is_in(x, y, False)

@bound_ops("Contains", "Contains-Any")
def poly_contains_any(x: Any, y: Any) -> Any:
    """
**Is a value contained in another value or collection**

* _value_.ContainsAny(_expression_)
* _value_ Contains [Any] _expression_

Functions identically to `IsIn()` except that the sense of the
operands are reverse.

```vgr
None.ContainsAny(None) → True
"cat".ContainsAny(None) → False

2 Contains 2 → True // equality
20 Contains 2 → False

Set animals To ["cat", "dog", "fish"]
None.ContainsAny("cat") → False
animals Contains "cat" → True
animals Contains ["cat", "frog"] → True  // cat or frog in animals
animals Contains ["rat", "frog"] → False // neither in animals
"dog".ContainsAny("do") → True           // string operation
animals.ContainsAny("do") → False        // list operation

Set point To {"x": 5, "y": 10}
point Contains "x" → True  // key in dictionary
point Contains "z" → False // key not in dictionary
```

Also see `ContainsAll()` and `IsIn()`
"""
    return _is_in(y, x, False)

@bound_ops("Contains-All")
def poly_contains_all(x: Any, y: Any) -> Any:
    """
**Is a value contained in another value or collection**

* _value_.ContainsAll(_expression_)
* _value_ Contains All _expression_

Functions identically to `ContainsAny()` except that when working with lists,
all tests are satisfied.

```vgr
Set animals To ["cat", "dog", "fish"]
animals Contains All "cat" → True
animals Contains All ["cat", "dog"] → True
animals Contains All ["cat", "frog"] → False
animals Contains All ["rat", "frog"] → False

Set point To {"x": 5, "y": 10}
point Contains All "x" → True
point Contains All ["x", "y", "z"] → False
```

Also see `ContainsAny()` and `IsIn()`
"""
    return _is_in(y, x, True)

def _is_in(x: Any, y: Any, do_all: bool) -> Any:
    """Does all the work for the in/contains operations"""
    if isinstance(x, (list, tuple)):
        t = (_is_in(x1, y, do_all) for x1 in x)
        return all(t) if do_all else any(t)
    if not isinstance(x, (NoneType, bool, int, str, float)):
        raise TypeError(f'Cannot use {type_str(x)} with In/Contains')
    if isinstance(y, str): return isinstance(x, str) and x in y
    if isinstance(y, (list, tuple)): return x in y
    if isinstance(y, dict): return x in y.keys()
    try:
        # TODO arguments could be made here for
        # using <= for numeric conditions "2 In 10"->T, "10 in 2"->F
        return poly_eq(x, y)
    except TypeError:
        return False
