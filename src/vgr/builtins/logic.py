"""
Boolean logic functions
"""

from typing import Any

from .common import bound_ops

def poly_true(x: Any=None) -> bool:
    """
**Check for logical True**

* IsTrue(*value*)
* *value*.IsTrue()

Numbers are evaluated as `False` for zero and `True` for non-zero.
All non-`None` values are consider `True`.

```vgr
None.IsTrue() → False
0.IsTrue() → False
1.IsTrue() → True
1.0.IsTrue() → True
"".IsTrue() → True
"x".IsTrue() → True
"false".IsTrue() → True
"false".ToBoolean().IsTrue() → False
True.IsTrue() → True
False.IsTrue() → False
```

Also see `ToBoolean()` and `IsFalse()`
"""
    if x is None: return False
    if isinstance(x, (int, float)): return bool(x)
    return True

@bound_ops("!", "！", "¬")
def poly_false(x: Any=None) -> bool:
    """
**Logical Negation (Not) operation**

* ! *x*
* ！*x*
* ¬ *x*
* IsFalse(*value*)
* *value*.IsFalse()

Numbers are evaluated as `False` for zero and `True` for non-zero.
All non-`None` values are consider `True`.

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

Also see `ToBoolean()` and `IsTrue()`
"""
    if x is None: return True
    if isinstance(x, (int, float)): return not bool(x)
    return False
