"""
Functions using regular expressions
"""

from functools import reduce
from typing import Any
import re

from .common import NoneType, type_str

def compile_pattern(x: Any, flags: int=0) -> Any:
    """
**Create a pre-compiled regular expression pattern**

* CompilePattern(_pattern_)
* _pattern_.CompilePattern()

The compiled pattern can be used with `RegexReplace()`
If the _pattern_ argument is a list, all the patterns
in the list are compiled.

```vgr
Set alpha To "^[A-Z][A-Za-z]*".CompilePattern()
```

Also see `RegexReplace()`
"""
    if isinstance(x, (NoneType, re.Pattern)): return x
    if isinstance(x, str):
        try:
            return re.compile(x, flags)
        except Exception as e:
            raise ValueError(f'Pattern error: {x!r}') from e
    if isinstance(x, (list, tuple)):
        return list(compile_pattern(x1, flags) for x1 in x)
    raise ValueError(f'Cannot Compile {type_str(x)} to a Pattern')

def poly_regex_replace(x: Any, *args) -> Any:
    """
**Regular Expression replacement**

* RegexReplace(_value_, _pattern_)
* RegexReplace(_value_, _pattern_... _replacement_)
* _value_.RegexReplace(_pattern_)
* _value_.RegexReplace(_pattern_... _replacement_)

The input value can be a string, list, or a dictionary.
Replacement is distributed over the contents of a list or dictionary.
The pattern can be a single string or pattern a list of either.
All _pattern_ values are applied in order, all using the same _replacement_ value.

The _replacement_ must be a string, but can be empty or _None_, which results in deletion of
the matched patterns.

The pattern can start with _(?i)_ for case indepenent replacement,
_(?m)_ for multiline replacement, or combined as _(?im)_ for both.
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
            raise ValueError(f'RegEx Replacement argument must be a string, found {type_str(replacement)}')
    if isinstance(pattern, (list, tuple)):
        return reduce(lambda x, pattern1: _regex_replace(x, pattern1, replacement), pattern, x)
    # in case we are going to loop, pre-compile the pattern
    if not isinstance(pattern, re.Pattern):
        if not isinstance(pattern, str):
            raise TypeError(f'Unexpected type for RegEx pattern {type_str(pattern)}')
        pattern = re.compile(pattern)
    if isinstance(x, str): return re.sub(pattern, replacement, x)
    if isinstance(x, (list, tuple)): return list(_regex_replace(x1, pattern, replacement) for x1 in x)
    if isinstance(x, dict): return {key: _regex_replace(value, pattern, replacement) for key, value in x.items() }
    raise TypeError(f'RegEx replacement on {type_str(x)} not supported')
