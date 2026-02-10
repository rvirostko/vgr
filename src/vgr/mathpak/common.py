"""
Routines and values that can be used by operator and function implementations.
"""

from typing import Any, Callable, Union

from .type import poly_type

Number = Union[int, float]

NoneType = type(None)
AnyType = type(Any)

# Operations table key for when the x value is None
X_None_Op = (NoneType, AnyType)

# Operations table key for when the Y value is None
Y_None_Op = (AnyType, NoneType)

# Operations table key for when Y value is a collection
Y_Coll_Op = (AnyType, list)

# See matching_default()
_DEFAULTS_BY_TYPE = {
    dict : {},
    float : 0.0,
    int : 0,
    list : [],
    str : '',
}

def bound_ops(*operators):
    """Attach a list of operators to a function so they show up in help"""
    def decorator(func):
        func.bound_ops = tuple(operators)
        return func
    return decorator

def requires_exec_context(func):
    """Mark a function as requiring an ExecContext"""
    func.requires_exec_context = True
    return func

def get_requires_exec_context(func) -> bool:
    """Check if a function requires an ExecContext"""
    return getattr(func, "requires_exec_context", False)

_TRUE_STRS = ('true', 't', 'yes', 'y', 'on')
_FALSE_STRS = ('false', 'f', 'no', 'n', 'off')

def str_to_number(s: str) -> Number:
    """
    Attempts to convert a string to a number value.
    Raises ValueError if it can't.
    May return None
    """
    if s is None or s.isspace(): return None
    s = s.strip()
    try:
        x: float = float(s)
        return int(x) if x.is_integer() else x
    except ValueError as e:
        raise ValueError(f'Cannot convert {s!r} to a number') from e

def str_to_int(x: str) -> int:
    """
    See str_to_number - forces an int result
    May return None
    """
    n = str_to_number(x)
    return None if n is None else int(n)

def str_to_bool(s: str) -> bool:
    """
    Attempts to convert a string to a boolean.
    Understand "true" and "false" and other versions.
    If the string can be converted to a number,
    it is compared against zero.
    """
    if s is None or s.isspace(): return False
    s = s.strip().lower()
    if s in _TRUE_STRS: return True
    if s in _FALSE_STRS: return False
    try:
        return str_to_number(s) != 0
    except ValueError as e:
        raise ValueError(f'Cannot convert {s!r} to a boolean') from e

def bool_arg(arg: Any, name: str) -> bool:
    """
    Type checks the argument as a boolean.
    None is considered false; string representations of T/F are parsed.
    Int/float are compared against zero.
    All other types are invalid.
    See str_to_bool() for conversion details.
    """
    if arg is None: return False
    if isinstance(arg, bool): return arg
    if isinstance(arg, str):
        try:
            return str_to_bool(arg)
        except ValueError:
            # Not, null, and not empty, so Python truthy
            return True
    if isinstance(arg, (int, float)): return arg != 0
    raise ValueError(f'{name} argument must be a boolean, found {poly_type(arg)!r}')

def int_arg(arg: Any, name: str) -> int:
    """
    Type checks the argument as an integer number (int, float, or converted string)
    None is treated as zero.
    """
    if isinstance(arg, str): arg = str_to_number(arg)
    if arg is None: arg = 0
    if not isinstance(arg, (int, float)):
        raise ValueError(f'{name} argument must be a number, found {poly_type(arg)!r}')
    return int(arg)

def str_arg(arg: Any, name: str, req_value: bool=True) -> str:
    """Type checks the argument as string and optionally, non-None, non-blank"""
    if req_value and arg is None:
        raise ValueError(f'{name} argument cannot be None')
    if isinstance(arg, str):
        if req_value and len(arg) == 0:
            raise ValueError(f'{name} argument cannot be blank')
        return arg
    raise ValueError(f'{name} argument must be a string, found {poly_type(arg)!r}')

def empty_is_zero(v: str) -> Any:
    return 0 if len(v) == 0 else str_to_number(v)

def dist_x(op: Callable[[Any, Any], Any], x: list, y: Any) -> list:
    """
    Distribute op over the colleciton: op(<list>, y)
    See dist_y()
    """
    return list(op(x1, y) for x1 in x)

def dist_y(op: Callable[[Any, Any], Any], x: Any, y: list) -> list:
    """
    Distribute op over the collection: op(x, <list>)
    Used by commutative operations with a scalar x and list y
    See dist_x()
    """
    return list(op(x, y1) for y1 in y)

def matching_default(x: Any) -> Any:
    """Given an object, return a *default* value that matches its type"""
    default = _DEFAULTS_BY_TYPE.get(type(x))
    if default is not None: return default
    raise TypeError(f'No default value for {poly_type(x)!r}') # SNO

def op_key(x: Any, y: Any) -> tuple:
    """The key used to look up behavior by operand type"""
    if x is None: return X_None_Op
    if y is None: return Y_None_Op
    return (type(x), type(y))

def get_operation(x, y, *op_tables) -> Callable[[Any, Any], Any]:
    """Using the list of tables, find an applicable operation"""
    key = op_key(x, y)
    for op_table in op_tables:
        op = op_table.get(key)
        if op is not None: return op
    return None

# For non-commutative numeric operations that don't define behaviors for
# dictionaries and have "natural" operations on int/float
# Generally it attempts to cast strings to numbers and
# distributes operations over collections.
numeric_operations = {
    X_None_Op: lambda op, _, y: None if y is None else op(matching_default(y), y),
    Y_None_Op: lambda op, x, _: op(x, matching_default(x)),
    (int, str): lambda op, x, y: op(x, str_to_number(y)),
    (float, str): lambda op, x, y: op(x, str_to_number(y)),
    (str, int): lambda op, x, y: op(str_to_number(x), y),
    (str, float): lambda op, x, y: op(str_to_number(x), y),
    (str, str): lambda op, x, y: op(str_to_number(x), str_to_number(y)),
    (list, int): dist_x,
    (list, float): dist_x,
    (list, str): dist_x,
    (tuple, int): dist_x,
    (tuple, float): dist_x,
    (tuple, str): dist_x,
}
