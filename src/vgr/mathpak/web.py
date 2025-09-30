"""
Functions applicable to Web data.
"""
from typing import Any

from urllib.parse import urlparse, quote
from urllib.error import URLError

from .common import dist_x, str_arg
from .types import poly_bool

def parse_url(url: Any, remove_nulls: bool=True) -> Any:
    """
**Decompose a URL string and return a dictionary of its components**

* _value_.ParseUrl()

In addition, the result will contain _error_ indicating if there was an error
and _error_msg_ describing the error. It always include the URL itself.

Distributive over lists and tuples, but not dictionaries.

```vgr
Set url to "https://user:pass@example.com:8080/path/to/page?x=1&y=2#frag"
Set parsed To url.ParseUrl()
parsed.url → "https://user:pass@example.com:8080/path/to/page?x=1&y=2#frag"
parsed.error → False
parsed.error_msg → None
parsed.scheme → "https"
parsed.hostname → "example.com"
parsed.port → 8080
parsed.netloc → "user:pass@example.com:8080"
parsed.username → "user"
parsed.password → "pass"
parsed.params → None
parsed.path → "/path/to/page"
parsed.query → "x=1&y=2"
parsed.fragment → "frag"
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
            "netloc": _empty_to_none(parsed.netloc),
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

def encode_url(url: str, safe: str="/") -> str:
    """
**Encode reserved characters in a full or partial URL**

* _value_.EncodeURL()
* _value_.EncodeURL(_safe_)

The _safe_ argument is string which lists reserved characters that need
not be encoded. When omitted, it defaults to "/".

```vgr
None.EncodeURL() → None
5.EncodeURL() → "5"
"hello world".EncodeURL() → "hello%20world"
"a/b/c".EncodeURL() → "a/b/c"
"a/b/c".EncodeURL("") → "a%2Fb%2Fc"
"role=admin".EncodeURL() → "role%3Dadmin"
"Café Münster".EncodeURL() → "Caf%C3%A9%20M%C3%BCnster"

// NB: use care when quoting an entire URL
"http://example.com?q=lst".EncodeURL() → "http%3A//example.com%3Fq%3Dlst"
```

"""
    if url is None: return None
    safe = str_arg(safe, "Safe", False)
    if safe is None: safe = ''
    if isinstance(url, (list, tuple)): return type(url)(encode_url(x1, safe) for x1 in url)
    if isinstance(url, (int, float)): url = str(url)
    if isinstance(url, str): return quote(url, safe=safe, errors='strict', encoding='utf-8')
    return url

def _empty_to_none(s:str) -> str:
    return None if s is None or len(s) == 0 else s
