"""
Functions for working with attrs and dictionaries
"""

from typing import Any

from .common import type_str, NoneType

def poly_vdig(x: Any, *args) -> Any:
    data = x
    for arg in args:
        data = poly_dig(data, arg)
        if data is None: break
    return data

def poly_dig(x: Any, path: Any) -> Any:
    """
Path can be:
* a list to be traversed
* a dotted string path (or just a single item)
Other types will be treated as strings
"""
    if isinstance(x, (NoneType, bool, int, float, str, tuple, list)): return x
    if isinstance(x, dict):
        if isinstance(path, str):
            path = [step.strip() for step in path.split('.') if not step.isspace()]
        elif isinstance(path, (bool, int, float)):
            path = [path]
        elif not isinstance(path, (tuple, list)):
            raise TypeError(f'Digging with a {type_str(path)} not supported')
        data = x
        for key in path:
            if not isinstance(data, dict) or key not in data: return None
            data = data[key]
        return data
    raise TypeError(f'Digging into {type_str(x)} not supported')
