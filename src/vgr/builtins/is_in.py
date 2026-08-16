"""
Implementations of an "in", "not in", "contains any" and "contains all" functions.
These can work on collections, dictionaries, strings and to some extent
scalar values.
"""

from typing import Any

from .common import bound_ops
from .strings import poly_index_of
from .registry import builtin

@bound_ops("Is In", "∈")
@builtin("IsIn")
def poly_in(value: Any=None, expr: Any=None) -> bool:
    """
**Is a value contained in another value or collection**

* *value* Is In *expression*
* *value* ∈ *expression*
* IsIn(*value*, *expression*)
* *value*.IsIn(*expression*)

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

Also see `IsNotIn()` and `Contains()`
"""
    if isinstance(expr, dict): expr = list(expr.keys())
    if isinstance(value, list): return any(poly_index_of(expr, v) != -1 for v in value)
    return poly_index_of(expr, value) != -1

@bound_ops("Is Not In", "∉")
@builtin("IsNotIn")
def poly_not_in(value: Any=None, expr: Any=None) -> Any:
    """
**Is a value _not_ contained in another value or collection**

* *value* Is Not In *expression*
* *value* ∉ *expression*
* IsNotIn(*value*, *expression*)
* *value*.IsNotIn(*expression*)

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
    if isinstance(expr, dict): expr = list(expr.keys())
    if isinstance(value, list): return all(poly_index_of(expr, v) == -1 for v in value)
    return poly_index_of(expr, value) == -1

@bound_ops("Contains")
@builtin("Contains")
def poly_contains(value: Any=None, expr: Any=None) -> Any:
    """
**Is a value contained in another value or collection**

* *value* Contains *expression*
* Contains(*value*, *expression*)
* *value*.Contains(*expression*)

Functions identically to `IsIn()` except that the sense of the
operands are reverse.

```vgr
None.Contains(None) → True
"cat".Contains(None) → False

2 Contains 2 → True // equality
20 Contains 2 → False

Set animals To ["cat", "dog", "fish"]
None.Contains("cat") → False
animals Contains "cat" → True
animals Contains ["cat", "frog"] → True  // cat or frog in animals
animals Contains ["rat", "frog"] → False // neither in animals
"dog".Contains("do") → True              // string operation
animals.Contains("do") → False           // list operation

Set point To {"x": 5, "y": 10}
point Contains "x" → True  // key in dictionary
point Contains "z" → False // key not in dictionary
```

Also see `ContainsAll()`, `IsIn()`, and `IndexOf()`
"""
    if isinstance(value, dict): value = list(value.keys())
    if isinstance(expr, list): return any(poly_index_of(value, e) != -1 for e in expr)
    return poly_index_of(value, expr) != -1

@bound_ops("Does Not Contain")
def poly_not_contains(value: Any=None, expr: Any=None) -> Any:
    """
**Is a value *not* contained in another value or collection**

* *value* Does Not Contain *expression*

See `Contains` operator
"""
    if isinstance(value, dict): value = list(value.keys())
    if isinstance(expr, list): return all(poly_index_of(value, e) == -1 for e in expr)
    return poly_index_of(value, expr) == -1

@bound_ops("Contains All")
@builtin("ContainsAll")
def poly_contains_all(value: Any=None, expr: Any=None) -> Any:
    """
**Is a value contained in another value or collection**

* *value* Contains All *expression*
* ContainsAll(*value*, *expression*)
* *value*.ContainsAll(*expression*)

Functions identically to `Contains()` except that when working with lists,
all tests are satisfied.

```vgr
Set animals To ["cat", "dog", "fish"]
animals Contains All "cat" → True
animals Contains All ["cat", "dog"] → True
animals Contains All ["cat", "frog"] → False

Set point To {"x": 5, "y": 10}
point Contains All "x" → True
point Contains All ["x", "y"] → True
point Contains All ["x", "y", "z"] → False
```

Also see `Contains()` and `IsIn()`
"""
    if isinstance(value, dict): value = list(value.keys())
    if isinstance(expr, list): return all(poly_index_of(value, e) != -1 for e in expr)
    return poly_index_of(value, expr) != -1
