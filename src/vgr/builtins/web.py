"""
Functions applicable to Web data.
"""
from typing import Any

from urllib.parse import urlparse, quote
from urllib.error import URLError

from .common import dist_x, str_arg
from .types import poly_to_boolean
from .registry import builtin

@builtin("ParseUrl")
def parse_url(url: Any=None, remove_nulls: bool=True) -> Any:
    """
**Decompose a URL string into a dictionary of its components**

* ParseUrl(*value*)
* *value*.ParseUrl()

In addition, the result will contain *error* indicating if there was an error
and *error_msg* describing the error. It always includes the URL itself.

Distributive over lists but not dictionaries.

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
    def _empty_to_none(s:str) -> str: return None if s is None or len(s) == 0 else s
    if url is None: return None
    remove_nulls = poly_to_boolean(remove_nulls)
    if isinstance(url, list): return dist_x(parse_url, url, remove_nulls)
    if not isinstance(url, str): return None
    url = url.strip()
    if len(url) == 0: return None
    try:
        parsed = urlparse(url)
        components = {
            "url":        url,
            "error":      False,
            "error_msg":  None,
            "netloc":    _empty_to_none(parsed.netloc),
            "scheme":    _empty_to_none(parsed.scheme),
            "hostname":  _empty_to_none(parsed.hostname),
            "path":      _empty_to_none(parsed.path),
            "params":    _empty_to_none(parsed.params),
            "query":     _empty_to_none(parsed.query),
            "fragment":  _empty_to_none(parsed.fragment),
            "port":      parsed.port,
            "username":  _empty_to_none(parsed.username),
            "password":  _empty_to_none(parsed.password),
        }
        return {key: value for key, value in components.items() if value is not None} if remove_nulls else components
    except (ValueError, URLError, TypeError) as e:
        return {
            "url":       url,
            "error":     True,
            "error_msg": str(e),
        }

@builtin("EncodeUrl")
def encode_url(url: str=None, safe: str="/") -> str:
    """
**Encode reserved characters in a full or partial URL**

* EncodeUrl(*value*)
* EncodeUrl(*value*, *safe*)
* *value*.EncodeUrl()
* *value*.EncodeUrl(*safe*)

The *safe* argument is string which lists reserved characters that need
not be encoded. When omitted, it defaults to "/".

```vgr
None.EncodeUrl() → None
5.EncodeUrl() → "5"
"hello world".EncodeUrl() → "hello%20world"
"a/b/c".EncodeUrl() → "a/b/c"
"a/b/c".EncodeUrl("") → "a%2Fb%2Fc"
"role=admin".EncodeUrl() → "role%3Dadmin"
"Café Münster".EncodeUrl() → "Caf%C3%A9%20M%C3%BCnster"

// NB: use caution when quoting an entire URL
"http://example.com?q=lst".EncodeURL() → "http%3A//example.com%3Fq%3Dlst"
```
"""
    if url is None: return None
    safe = str_arg(safe, "Safe", False)
    if safe is None: safe = ''
    if isinstance(url, list): return list(encode_url(x1, safe) for x1 in url)
    if isinstance(url, (int, float)): url = str(url)
    if isinstance(url, str): return quote(url, safe=safe, errors='strict', encoding='utf-8')
    return url
