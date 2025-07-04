"""
Functions for working with attrs and dictionaries
"""

from typing import Any

from .common import type_str, NoneType

def poly_dig(x: Any, *args) -> Any:
    """Traverse a path in a dictionary object.

* _dict_.Dig(_path_ [, _path_]) [;]

Path parts can be:
* A string with periods intoducing subpath components
* Bool, int, float are converted to single step paths
* A list composed of path components
"""
    data = x
    for arg in args:
        data = _dig(data, arg)
        if data is None: break
    return data

def _dig(x: Any, path: Any) -> Any:
    if isinstance(x, (NoneType, bool, int, float, str, tuple, list)): return x
    if isinstance(x, dict):
        if isinstance(path, str):
            # DO NOT STRIP!
            # Crap headers in CSVs frequently have trailing spaces
            path = [step for step in path.split('.') if not step.isspace()]
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
