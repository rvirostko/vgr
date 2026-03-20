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

def format_json(obj: Any=None, indent: int=2, sort_keys: bool=False) -> Any:
    """
Format the object as a JSON string

* FormatJson(*value*)
* FormatJson(*value*, *indent*)
* FormatJson(*value*, *indent*, *sort_keys*)
* *value*.FormatJson()
* *value*.FormatJson(*indent*)
* *value*.FormatJson(*indent*, *sort_keys*)

If *indent* is None then the value is formatted without indentation or line breaks.
When zero, only line breaks are added. The value for *indent* is constrained from
zero to 32. The default value is 2.

The default value for *sort_key* is `False`.

`Nan` and `Inf` values will generate an error as they are not JSON compliant.

```vgr
None.FormatJson() → "null"
5.FormatJson() → "5"
5.1.FormatJson() → "5.1"
"Hello".FormatJson() → "Hello"
True.FormatJson() → true
[5, 10, 15].FormatJson() → "[
  5,
  10,
  15
]"
[5, 10, 15].FormatJson(None) → "[5, 10, 15]"
[True, "Hello", None].FormatJson(None) → "[true, "Hello", null]"

{"c": "sea", "b": "bee", "a": "eh"}.FormatJson(4) →
{
    "c": "sea",
    "b": "bee",
    "a": "eh"
}

{"c": "sea", "b": "bee", "a": "eh"}.FormatJson(4, True) → {
    "a": "eh",
    "b": "bee",
    "c": "sea"
}

Nan.FormatJson()
    ^
Out of range float values are not JSON compliant: nan
```
"""
    indent = None if indent is None else min(max(0, int_arg(indent, 'Indent')), 32)
    sort_keys = bool_arg(sort_keys, "SortKeys")
    return json.dumps(obj, indent=indent, default=str, sort_keys=sort_keys, allow_nan=False, ensure_ascii=False)
