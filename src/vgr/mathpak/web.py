"""
Functions applicable to Web data.
"""
from typing import Any

from urllib.parse import urlparse, quote
from urllib.error import URLError

from .common import dist_x
from .types import poly_bool

def parse_url(url: Any, remove_nulls: bool=True) -> Any:
    """
Decompose a URL as a string and return a dictionary of its components.

In addition, the result will contain _error_ indicating if there was an error,
_error_msg_ describing the error, and will always include the URL itself.
Distributive over lists and tuples, but not dictionaries.

```vgr
**TODO**
```
"""
    if url is None: return None
    remove_nulls = poly_bool(remove_nulls)
    if isinstance(url, (list, tuple)): return dist_x(parse_url, url, remove_nulls)
    if not isinstance(url, str): return None
    url = url.strip()
    if len(url) == 0: return None
    try:
        parsed = urlparse(url)
        components = {
            "url": url,
            "error": False,
            "error_msg": None,
            "scheme": _empty_to_none(parsed.scheme),
            "hostname": _empty_to_none(parsed.hostname),
            "path": _empty_to_none(parsed.path),
            "params": _empty_to_none(parsed.params),
            "query": _empty_to_none(parsed.query),
            "fragment": _empty_to_none(parsed.fragment),
            "port": parsed.port,
            "username": _empty_to_none(parsed.username),
            "password": _empty_to_none(parsed.password),
        }
        return {key: value for key, value in components.items() if value is not None} if remove_nulls else components
    except (ValueError, URLError, TypeError) as e:
        return {
            "url": url,
            "error": False,
            "error_msg": str(e),
        }

def encode_url(url: str) -> str:
    """
```vgr
**TODO**
```
"""
    if url is None: return None
    if isinstance(url, (list, tuple)): return type(url)(encode_url(x1) for x1 in url)
    return quote(url, errors='strict', encoding='utf-8') if isinstance(url, str) else None

def _empty_to_none(s:str) -> str:
    return None if s is None or len(s) == 0 else s
