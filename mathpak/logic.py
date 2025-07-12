"""
Boolean logic functions
"""

from typing import Any

from .common import bound_ops
from .types import poly_bool

@bound_ops("&&", "And", "∧")
def poly_and(x: Any, y: Any) -> Any:
    """
**Logical And operation**

* _x_ && _y_
* _x_ And _y_
* _x_ ∧ _y_

The values for _x_ and _y_  are evaluated as booleans:
see ToBool() for conversion details.
"""
    return poly_bool(x) and poly_bool(y)

@bound_ops("||", "Or", "∨")
def poly_or(x: Any, y: Any) -> Any:
    """
**Logical Or operation**

* _x_ || _y_
* _x_ Or _y_
* _x_ ∨ _y_

The values for _x_ and _y_  are evaluated as booleans:
see _ToBool()_ for conversion details.
"""
    return poly_bool(x) or poly_bool(y)

@bound_ops("!", "！", "¬")
def poly_not(x: Any) -> Any:
    """
**Logical Negation (Not) operation**

* ! _x_
* ！_x_
* ¬ _x_

The value of _x_ is evaluated as a boolean:
see _ToBool()_ for conversion details.
"""
    return not poly_bool(x)
