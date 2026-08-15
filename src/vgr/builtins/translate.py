from typing import Any

from .registry import builtin
from .as_str import as_str

@builtin("TranslateStr")
def poly_translate(x: Any=None, from_str: Any=None, to_str: Any=None) -> Any:
    """
**Perform character-by-character conversion or deletion**

* TranslateStr(*value*, *expression*)
* TranslateStr(*value*, *expression*, *expression*)
* *value*.TranslateStr(*expression*)
* *value*.TranslateStr(*expression*, *expression*)

If the two-arguments form is used, or the replacement string is empty or `None`,
the characters are deleted.

```vgr
"abc".TranslateStr("b") → "ac"
"abc".TranslateStr("b","*") → "a*c"
"dog".TranslateStr(string.ascii_lowercase, string.ascii_uppercase) → "DOG"
["cat", "dog"].TranslateStr("ao", "40") → ["c4t", "d0g"]
"cat".TranslateStr({"c".Ord(): "r".Ord()}) → "rat"
```
"""
    def _maketrans(from_str: str, to_str: str=''):
        return str.maketrans({from_str[i]: to_str[i] if i < len(to_str) else None for i in range(len(from_str))})
    if x is not None and from_str is not None:
        if isinstance(x, str):
            # A lot of assumptions here, but we'll try to use it as requested
            # This would be a good case for somebody to make a JSON object (or save it)
            # and do a Load-From into a top-level object
            # NB: this works ordinal-to-ordinal
            if isinstance(from_str, dict): return x.translate(from_str)
            from_str = as_str(from_str)
            if isinstance(from_str, str) and len(from_str) > 0:
                to_str = '' if to_str is None else as_str(to_str)
                if isinstance(to_str, str): return x.translate(_maketrans(from_str, to_str))
        else:
            x = as_str(x)
            if isinstance(x, str): return poly_translate(x, from_str, to_str)
            if isinstance(x, list): return list(poly_translate(x1, from_str, to_str) for x1 in x)
    return x
