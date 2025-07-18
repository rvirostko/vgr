"""
Functions for working with attrs and dictionaries
"""

from typing import Any

from .common import type_str

def poly_dig(data: Any, *args) -> Any:
    """
**Traverse a path in a dictionary object**

* _value_.Dig()
* _value_.Dig(_path_ [, _path_])

The _value_ must either be a dictionary or _None_.

Path parts can be:
* A _None_, str, bool, int, or float
* A list composed of path components
"""
    if data is None: return data
    if not isinstance(data, dict): raise TypeError(f'Digging into {type_str(data)} not supported')
    # Always go through the path parts just to validate them
    for arg in args: data = _dig(data, arg)
    return data

def _dig(data: dict, path: Any) -> Any:
    if path is None or isinstance(path, (str, bool, int, float)):
        path = [path]
    elif not isinstance(path, (tuple, list)):
        raise TypeError(f'Digging with a {type_str(path)} not supported')
    for key in path:
        if not isinstance(data, dict) or key not in data: return None
        data = data[key]
    return data
