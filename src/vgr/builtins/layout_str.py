
from typing import Any

from .common import int_arg, str_arg
from .as_str import as_str
from .registry import builtin
from .types import poly_str

@builtin("Center")
def poly_center(x: Any=None, width: int=0, fillchar: str=' ') -> Any:
    """
**Create a centered string of the given width**

* Center(*value*, *width*)
* Center(*value*, *width*, _pad_)
* *value*.Center(_width_)
* *value*.Center(_width_, _pad_)

If the *value* to be centered is `None`, it is treated as an empty string.
The *width* argument is interpreted as a numeric value. If `None`, zero is assumed.
The _pad_ argument, if provided, is interpreted as a string value. Only the first character is used.
If not provided, the default is a space.

```vgr
None.Center(3) → "   "
"aaaBc".Center(3) → "aaaBc"
"aaaBc".Center(7) → " aaaBc "
"aaaBc".Center(8) → " aaaBc  "
"aaaBc".Center(7, "-") → "-aaaBc-"
"aaaBc".Center(9, "-=") → "--aaaBc--"
["A.b.c", "X.y.z"].Center(7, ".") → [".A.b.c.", ".X.y.z."]
123.Center(5, "0") → "01230"
```

Also see `LeftJustify()` and `RightJustify()`
"""
    return _layout_opt(x, width, fillchar, poly_center, str.center)

@builtin("LeftJustify")
def poly_left_justify(x: Any=None, width: int=0, fillchar: str=' ') -> Any:
    """
**Create a string of the given width with contents left aligned**

* LeftJustify(*value*, *width*)
* LeftJustify(*value*, *width*, _pad_)
* *value*.LeftJustify(_width_)
* *value*.LeftJustify(_width_, _pad_)

If the *value* to be centered is `None`, it is treated as an empty string.
The *width* argument is interpreted as a numeric value. If `None`, zero is assumed.
The _pad_ argument, if provided, is interpreted as a string value. Only the first character is used.
If not provided, the default is a space.

```vgr
None.LeftJustify(3) → "   "
"aaaBc".LeftJustify(3) → "aaaBc"
"aaaBc".LeftJustify(7) → "aaaBc  "
"aaaBc".LeftJustify(8) → "aaaBc   "
"aaaBc".LeftJustify(7, "-") → "aaaBc--"
"aaaBc".LeftJustify(9, "-=") → "aaaBc----"
["A.b.c", "X.y.z"].LeftJustify(7, ".") → ["A.b.c..", "X.y.z.."]
123.LeftJustify(5, "0") → "12300"
```

Also see `Center()` and `RightJustify()`
"""
    return _layout_opt(x, width, fillchar, poly_left_justify, str.ljust)

@builtin("RightJustify")
def poly_right_justify(x: Any=None, width: int=0, fillchar: str=' ') -> Any:
    """
**Create a string of the given width with contents right aligned**

* RightJustify(*value*, *width*)
* RightJustify(*value*, *width*, _pad_)
* *value*.RightJustify(_width_)
* *value*.RightJustify(_width_, _pad_)

If the *value* to be centered is `None`, it is treated as an empty string.
The *width* argument is interpreted as a numeric value. If `None`, zero is assumed.
The _pad_ argument, if provided, is interpreted as a string value. Only the first character is used.
If not provided, the default is a space.

```vgr
None.RightJustify(3) → "   "
"aaaBc".RightJustify(3) → "aaaBc"
"aaaBc".RightJustify(7) → "  aaaBc"
"aaaBc".RightJustify(8) → "   aaaBc"
"aaaBc".RightJustify(7, "-") → "--aaaBc"
"aaaBc".RightJustify(9, "-=") → "----aaaBc"
["A.b.c", "X.y.z"].RightJustify(7, ".") → ["..A.b.c", "..X.y.z"]
123.RightJustify(5, "0") → "00123"
```

Also see `Center()` and `LeftJustify()`
"""
    return _layout_opt(x, width, fillchar, poly_right_justify, str.rjust)

@builtin("ZeroFill")
def poly_zero_fill(x: Any=None, width: int=0) -> Any:
    """
**Create a string of the given width with contents right aligned, padded with zeroes**

* ZeroFill(*value*, *width*)
* *value*.ZeroFill(_width_)

If the *value* to be centered is `None`, it is treated as an empty string.
The *width* argument is interpreted as a numeric value. If `None`, zero is assumed.

```vgr
None.ZeroFill(3) → "000"
"aaaBc".ZeroFill(3) → "aaaBc"
"aaaBc".ZeroFill(7) → "00aaaBc"
"aaaBc".ZeroFill(8) → "000aaaBc"
["A.b.c", "X.y.z"].ZeroFill(7) → ["00A.b.c", "00X.y.z"]
123.ZeroFill(5) → "00123"
```

Also see `RightJustify()`
"""
    return poly_right_justify(x, width, '0')

def _layout_opt(x: Any, width: int, fillchar: str, op, str_op) -> Any:
    width = 0 if width is None else min(max(0, int_arg(width, "Width")), 256)
    fillchar = ' ' if fillchar is None else str_arg(fillchar, "Fillchar")[0]
    if x is None: return fillchar * width
    if isinstance(x, list): return list(op(x1, width, fillchar) for x1 in x)
    x = poly_str(x) if isinstance(x, dict) else as_str(x)
    return str_op(x, width, fillchar)
