"""
JSON (dict) related functions
"""

import json

from .common import int_arg, bool_arg

def parse_json(s):
    """
**Parse a string as JSON**

Returns `None` if input is `None`.

```vgr
**TODO**
```
"""
    return None if s is None else json.loads(s)

def strip_nulls(obj):
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

def format_json(obj, indent: int=2, sort_keys: bool=True):
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
    return None if obj is None else json.dumps(to_json(obj), indent=indent, default=str, sort_keys=sort_keys)

def to_json_string(obj):
    """
**Format the object as a compact JSON string**

* ToJSONStr(*value*)
* *value*.ToJSONStr()

```vgr
**TODO**
```

"""
    return None if obj is None else json.dumps(to_json(obj), separators=(',', ':'), default=str, ensure_ascii=False)

def to_json(obj):
    """
**Convert the object into a JSON (dictionary or list) object**

* ToJSON(*value*)
* *value*.ToJSON()

Scalar values are wrapped into an object.

```vgr
**TODO**
```
"""
    return obj if isinstance(obj, (dict, list)) else { "value": obj }
