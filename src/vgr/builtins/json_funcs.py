"""
JSON (dict) related functions
"""

from typing import Any
import json

from .common import int_arg, bool_arg

def strip_nulls(obj: Any=None) -> Any:
    """
**Recursively remove `None` values from dictionaries and lists**

```vgr
**TODO**
```
"""
    if isinstance(obj, dict):
        return {k: strip_nulls(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return list(strip_nulls(v) for v in obj if v is not None)
    return obj

def format_json(obj: Any=None, indent: int=2, sort_keys: bool=True) -> Any:
    """
Format the object as a JSON string

* FormatJSON(*value*)
* FormatJSON(*value*, *indent*)
* FormatJSON(*value*, *indent*, *sort_keys*)
* *value*.FormatJSON()
* *value*.FormatJSON(*indent*)
* *value*.FormatJSON(*indent*, *sort_keys*)

```vgr
**TODO**
```
"""
    indent = None if indent is None else int_arg(indent, 'Indent')
    sort_keys = bool_arg(sort_keys, "SortKeys")
    return None if obj is None else json.dumps(_to_json(obj), indent=indent, default=str, sort_keys=sort_keys)

def to_json_string(obj: Any=None) -> str:
    """
**Format the object as a compact JSON string**

* ToJSONStr(*value*)
* *value*.ToJSONStr()

```vgr
**TODO**
```

"""
    return None if obj is None else json.dumps(_to_json(obj), separators=(',', ':'), default=str, ensure_ascii=False)

def _to_json(obj: Any=None) -> dict:
    return obj if isinstance(obj, (dict, list)) else { "value": obj }
