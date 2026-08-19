"""
Boolean logic functions
"""

from typing import Any

from .common import bound_ops
from .registry import builtin

def _apply_vargs(args, op):
    """Super simple handling for variable arguments"""
    return None if len(args) == 0 else op(args[0]) if len(args) == 1 else [op(x) for x in args]

@builtin("IsTrue")
def poly_is_true(*args) -> bool:
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
    def _op(x):
        if x is None: return False
        if isinstance(x, (int, float)): return bool(x)
        return True
    return _apply_vargs(args, _op)

@bound_ops("!", "！", "¬")
@builtin("IsFalse", "Not")
def poly_is_false(*args) -> bool:
    """
**Logical Negation (Not) operation**

* !*x*
* ！*x*
* ¬*x*
* Not(*value*)
* *value*.Not()
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
    def _op(x):
        if x is None: return True
        if isinstance(x, (int, float)): return not bool(x)
        return False
    return _apply_vargs(args, _op)
