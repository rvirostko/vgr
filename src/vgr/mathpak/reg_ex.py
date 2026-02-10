"""
Functions using regular expressions
"""

from functools import reduce
from typing import Any
import re

from .common import NoneType
from .type import poly_type

def poly_is_pattern(x:Any) -> bool:
    """
**Is a value a pre-compiled regular expression pattern**

* IsPattern(*value*)
* *value*.IsPattern()

```vgr
"[abc]".IsPattern() → False
CompilePattern("[abc]").IsPattern() → True
```

Also see `CompilePattern()`
"""
    return isinstance(x, re.Pattern)

def compile_pattern(x: Any, flags: int=0) -> Any:
    """
**Create a pre-compiled regular expression pattern**

* CompilePattern(*pattern*)
* *pattern*.CompilePattern()

The compiled pattern can be used with `RegexReplace()`
If the *pattern* argument is a list, all the patterns
in the list are compiled.

```vgr
Set alpha To "^[A-Z][A-Za-z]*".CompilePattern()
**TODO**
```

Also see `RegexReplace()` and `IsPattern()`
"""
    if isinstance(x, (NoneType, re.Pattern)): return x
    if isinstance(x, str):
        try:
            return re.compile(x, flags)
        except Exception as e:
            raise ValueError(f'Pattern error: {x!r}') from e
    if isinstance(x, (list, tuple)):
        return list(compile_pattern(x1, flags) for x1 in x)
    raise ValueError(f'Cannot Compile {poly_type(x)!r} to a Pattern')

def poly_regex_replace(x: Any, *args) -> Any:
    """
**Regular Expression replacement**

* RegexReplace(*value*, *pattern*)
* RegexReplace(*value*, *pattern*&hellip;, *replacement*)
* *value*.RegexReplace(*pattern*)
* *value*.RegexReplace(*pattern*&hellip;, *replacement*)

The input value can be a string, list, or a dictionary.
Replacement is distributed over the contents of a list or dictionary.
The pattern can be a single string or pattern a list of either.
All *pattern* values are applied in order, all using the same *replacement* value.

The *replacement* must be a string, but can be empty or `None`, which results in deletion of
the matched patterns.

The pattern can start with *(?i)* for case indepenent replacement,
*(?m)* for multiline replacement, or combined as *(?im)* for both.
Capture groups can be referenced in the replacement.

```vgr
"catalogue".RegexReplace("at.*") → "c"
"catalogue".RegexReplace("at.*", "at") → "cat"
"cAt".RegexReplace("[AEIOU]", "[^A-Z]", "-") → "---"
["cat", "dog"].RegexReplace("[aeiou]", "-") → ["c-t", "d-g"]
```

Also see `CompilePattern()`
"""
    if not args: return x
    if len(args) == 1: return _regex_replace(x, args[0], '')
    if len(args) == 2: return _regex_replace(x, args[0], args[1]) # pattern and replacement
    return _regex_replace(x, args[:-1], args[-1]) # pattern is a list, single replacement

def _regex_replace(x: Any, pattern: Any, replacement: Any=None) -> Any:
    # For these types, the operation is idempotent
    if isinstance(x, (NoneType, bool, int, float)) or pattern is None: return x
    if replacement is None:
        replacement = ''
    else:
        if not isinstance(replacement, str):
            raise ValueError(f'RegEx Replacement argument must be a string, found {poly_type(replacement)!r}')
    if isinstance(pattern, (list, tuple)):
        return reduce(lambda x, pattern1: _regex_replace(x, pattern1, replacement), pattern, x)
    # in case we are going to loop, pre-compile the pattern
    if not isinstance(pattern, re.Pattern):
        if not isinstance(pattern, str):
            raise TypeError(f'Unexpected type for RegEx pattern: {poly_type(pattern)!r}')
        pattern = re.compile(pattern)
    if isinstance(x, str): return re.sub(pattern, replacement, x)
    if isinstance(x, (list, tuple)): return list(_regex_replace(x1, pattern, replacement) for x1 in x)
    if isinstance(x, dict): return {key: _regex_replace(value, pattern, replacement) for key, value in x.items() }
    raise TypeError(f'RegEx replacement on {poly_type(x)!r} not supported')
