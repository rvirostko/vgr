from itertools import chain
from typing import Any

from .inequ import poly_eq

def poly_lookup(x: Any, attr: Any, *args) -> Any:
    if not isinstance(x, (list, tuple)): return None
    if not isinstance(attr, str): raise TypeError(f'String required for lookup attribute; found {type(attr).__name__}')
    attr = attr.strip()
    if not attr: return None
    if len(args) == 0: return []
    if len(args) > 1: return _multi_lookup(x, attr, args)
    arg = args[0]
    return _multi_lookup(x, attr, arg) if isinstance(arg, (list, tuple)) else _lookup(x, attr, arg)

def _multi_lookup(x:Any, attr: str, values: Any) -> list[Any]:
    # This chain takes all the results and handles as if it were a single iterator
    return list(chain.from_iterable(_lookup(x, attr, value) for value in values))

def _lookup(x: Any, attr: str, value: Any) -> list[Any]:
    # NB: since poly_eq() uses the first param to drive conversions,
    #     we use the data we have in the records as the "right" type
    #     and let value be adjusted accordingly
    return [x1 for x1 in x if isinstance(x1, dict) and poly_eq(x1.get(attr), value)]
