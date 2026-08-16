"""
JSON (dict) related functions
"""

from typing import Any
import json

from .common import int_arg, bool_arg

from .registry import builtin

@builtin("StripNulls")
def strip_nulls(obj: Any=None) -> Any:
    """
**Recursively remove `None` values from dictionaries and lists**

* StripNulls(*value*)
* *value*.StripNulls()

Typically used with data loaded from a JSON file.

```vgr
StripNulls(None) → None
StripNulls(False) → False
StripNulls(5) → 5
StripNulls(5.1) → 5.1
StripNulls("hello") → "hello"
[1, None, "text", None, {"a": None, "b": 2}, [None, 3, None], False].StripNulls()
  → [1, "text", {"b": 2}, [3], False]

Set data To {
  "name": "alpha",
  "count": null,
  "tags": [
    "one",
    null,
    "two",
    null
  ],
  "meta": {
    "owner": null,
    "active": true,
    "notes": [
      null,
      "ok",
      null
    ]
  },
  "value": 3.14,
  "empty": null
}
data.StripNulls() →
{
  "name": "alpha",
  "tags": [
    "one",
    "two"
  ],
  "meta": {
    "active": true,
    "notes": [
      "ok"
    ]
  },
  "value": 3.14
}

Also see `ParseJSON` and the `Load` statements.
```
"""
    if isinstance(obj, dict):
        return {k: strip_nulls(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return list(strip_nulls(v) for v in obj if v is not None)
    return obj

@builtin("FormatJSON")
def format_json(obj: Any=None, indent: int=2, sort_keys: bool=False) -> Any:
    """
**Format the object as a JSON string**

* FormatJSON(*value*)
* FormatJSON(*value*, *indent*)
* FormatJSON(*value*, *indent*, *sort_keys*)
* *value*.FormatJSON()
* *value*.FormatJSON(*indent*)
* *value*.FormatJSON(*indent*, *sort_keys*)

If *indent* is `None` then the value is formatted without indentation or line breaks.
When zero, only line breaks are added. The value for *indent* is constrained from
zero to 32. The default value is 2.

The default value for *sort_key* is `False`.

`Nan` and `Inf` values will generate an error as they are not JSON compliant.

```vgr
None.FormatJSON() → "null"
5.FormatJSON() → "5"
5.1.FormatJSON() → "5.1"
"Hello".FormatJSON() → "Hello"
True.FormatJSON() → true
[5, 10, 15].FormatJSON() → "[
  5,
  10,
  15
]"
[5, 10, 15].FormatJSON(None) → "[5, 10, 15]"
[True, "Hello", None].FormatJSON(None) → "[true, "Hello", null]"

{"c": "sea", "b": "bee", "a": "eh"}.FormatJSON(4) →
{
    "c": "sea",
    "b": "bee",
    "a": "eh"
}

{"c": "sea", "b": "bee", "a": "eh"}.FormatJSON(4, True) → {
    "a": "eh",
    "b": "bee",
    "c": "sea"
}

Nan.FormatJSON()
    ^
Out of range float values are not JSON compliant: nan
```
"""
    indent = None if indent is None else min(max(0, int_arg(indent, 'Indent')), 32)
    sort_keys = bool_arg(sort_keys, "SortKeys")
    return json.dumps(obj, indent=indent, default=str, sort_keys=sort_keys, allow_nan=False, ensure_ascii=False)
