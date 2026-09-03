
from typing import Any

from .registry import builtin

from ..user_callable import VgrCallable, lookup_function_cache

@builtin("IsFunction")
def poly_is_function(*args) -> Any:
    """
**Is a value a function**

* IsFunction(*value*)
* *value*.IsFunction()

```vgr
None.IsFunction() → False
Function f(x) -> x+1
f.IsFunction() → True
```
"""
    def _is_func(obj) -> bool: return isinstance(obj, VgrCallable)
    length: int = len(args)
    return None if length == 0 else _is_func(args[0]) if length == 1 else [_is_func(item) for item in args]

@builtin("GetCacheUsage")
def poly_get_cache_usage(*args: Any) -> Any:
    """
**Get usage information for a function's cache**

* GetCacheUsage(*function**&hellip;)
* *function*.GetCacheUsage([*function*&hellip;])

The *function* argument can be any variable which references a function
or the string key of a function's result cache.

```vgr
Define Cached Function square(b) -> b*b
For x = 1 To 10_000: Call square(Random(100)); Next
Print square.GetCacheUsage().FormatJson()
{
  "key": "F@10b13f580",
  "size": 64,
  "requests": 10000,
  "hits": 6255,
  "hit_percentage": 62.55,
  "evictions": 3681,
  "eviction_percentage": 36.809999999999995
}
```

Also see `EmptyCache()` and `vgr.caches`
"""
    def _get_info(obj) -> dict:
        if isinstance(obj, str):
            cache = lookup_function_cache(obj)
            return None if cache is None else cache.info
        if isinstance(obj, VgrCallable): return obj.cache_info
        if isinstance(obj, list): return [_get_info(item) for item in obj]
        if isinstance(obj, dict): return {k: _get_info(v) for k, v in obj.items()}
        return None
    length: int = len(args)
    return None if length == 0 else _get_info(args[0]) if length == 1 else _get_info([args])

@builtin("EmptyCache")
def poly_empty_cache(*args: Any) -> Any:
    """
**Removes all entries from a function's cache**

* EmptyCache(*function*&hellip;)
* *function*.EmptyCache([*function*&hellip;])

The *function* argument can be any variable which references a function
or the string key of a function's result cache.

```vgr
Define Cached Function square(b) -> b*b
For x = 1 To 10_000: Call square(Random(100)); Next
Print square.GetCacheUsage().FormatJson()
{
  "key": "F@10b13f580",
  "size": 64,
  "requests": 10000,
  "hits": 6255,
  "hit_percentage": 62.55,
  "evictions": 3681,
  "eviction_percentage": 36.809999999999995
}
Print square.EmptyCache().FormatJson()
{
  "key": "F@10b13f580",
  "size": 64,
  "requests": 0,
  "hits": 0,
  "hit_percentage": 0,
  "evictions": 0,
  "eviction_percentage": 0
}
```

Also see `GetCacheUsage()` and `vgr.caches`
"""
    def _clear(obj) -> dict:
        if isinstance(obj, str):
            cache = lookup_function_cache(obj.strip())
            return None if cache is None else cache.clear()
        if isinstance(obj, VgrCallable): return obj.clear_cache()
        if isinstance(obj, list): return [_clear(item) for item in obj]
        if isinstance(obj, dict): return {k: _clear(v) for k, v in obj.items()}
        return None
    length: int = len(args)
    return None if length == 0 else _clear(args[0]) if length == 1 else _clear([args])
