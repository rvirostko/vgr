"""
Boolean logic functions
"""

from typing import Any

from .common import bound_ops

def poly_true(x: Any) -> bool:
    """
**Check for logical True**

* _value_.IsTrue()

Numbers are evaluated as _False_ for zero and True for non-zero.
All non-_None_ values are consider _True_.
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
* _value_.IsFalse()

Numbers are evaluated as _False_ for zero and _True_ for non-zero.
All non-_None_ values are consider _True_.
"""
    if x is None: return True
    if isinstance(x, (int, float)): return not bool(x)
    return False
