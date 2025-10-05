"""
Boolean logic functions
"""

from typing import Any

from .common import bound_ops

def poly_true(x: Any) -> bool:
    """
**Check for logical True**

* IsTrue(_value_)
* _value_.IsTrue()

Numbers are evaluated as _False_ for zero and True for non-zero.
All non-_None_ values are consider _True_.

```vgr
None.IsTrue() → False
0.IsTrue() → False
1.IsTrue() → True
1.0.IsTrue() → True
"".IsTrue() → True
"x".IsTrue() → True
"false".IsTrue() → True
"false".ToBool().IsTrue() → False
True.IsTrue() → True
False.IsTrue() → False
```

Also see `ToBool()`
"""
    if x is None: return False
    if isinstance(x, (int, float)): return bool(x)
    return True

@bound_ops("!", "！", "¬")
def poly_false(x: Any) -> bool:
    """
**Logical Negation (Not) operation**

* ! _x_
* ！_x_
* ¬ _x_
* IsFalse(_value_)
* _value_.IsFalse()

Numbers are evaluated as _False_ for zero and _True_ for non-zero.
All non-_None_ values are consider _True_.

```vgr
None.IsFalse() → True
0.IsFalse() → True
1.IsFalse() → False
1.0.IsFalse() → False
"".IsFalse() → False
"x".IsFalse() → False
"true".IsFalse() → False
True.IsFalse() → False
False.IsFalse() → True
```

Also see `ToBool()`
"""
    if x is None: return True
    if isinstance(x, (int, float)): return not bool(x)
    return False
