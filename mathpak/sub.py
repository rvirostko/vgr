from functools import reduce
from typing import Any

from .common import bound_ops, get_operation, numeric_operations

@bound_ops("-", "－")
def poly_sub(x: Any, *args):
    """
**Subtraction operation**

* _x_ - _y_
* _x_ － _y_
* _x_.Sub(_y_...)

| x     | y     | returns   | operation                 |
|-------|-------|-----------|---------------------------|
| int   | int   | int       | x - y                     |
| int   | float | float     | x - y                     |
| int   | str   | int/float | x - ToNumber(y)           |
| float | int   | float     | x - y                     |
| float | float | float     | x - y                     |
| float | str   | int/float | x - ToNumber(y)           |
| str   | int   | int/float | ToNumber(x) - y           |
| str   | float | int/float | ToNumber(x) - y           |
| str   | str   | int/float | ToNumber(x) - ToNumber(y) |
| list  | int   | list      | distributed               |
| list  | float | list      | distributed               |
| list  | str   | list      | distributed               |
| tuple | int   | tuple     | distributed               |
| tuple | float | tuple     | distributed               |
| tuple | str   | tuple     | distributed               |
| dict  | str   | dict      | remove key y from x       |
| dict  | list  | dict      | remove keys in y from x   |
| dict  | tuple | dict      | remove keys in y from x   |
| dict  | dict  | dict      | remove keys in y from x   |

TypeError raised on all other combinations
"""
    return reduce(_sub, args, x)

def _sub(x: Any, y: Any) -> Any:
    operation = get_operation(x, y, sub_operations, numeric_operations)
    return operation(_sub, x, y) if operation else x - y

def remove_keys(x: dict, y: Any) -> dict:
    return {k:v for k, v in x.items() if k not in y}

sub_operations = {
    (dict, int): lambda _, x, y: remove_keys(x, [y]),
    (dict, float): lambda _, x, y: remove_keys(x, [y]),
    (dict, str): lambda _, x, y:  remove_keys(x, [y]),
    (dict, list): lambda _, x, y: remove_keys(x, y),
    (dict, tuple): lambda _, x, y: remove_keys(x, y),
    (dict, dict): lambda _, x, y:  remove_keys(x, list(y.keys())),
}
