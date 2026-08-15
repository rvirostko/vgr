from typing import Any
import re
from re import Pattern

from .as_str import as_str
from .registry import builtin
from .type import poly_type
from .common import int_arg, str_arg

@builtin("Split")
def poly_split(x: Any=None, sep: str=None, maxsplit: int=-1) -> Any:
    """
**Split a string based on a separator string**

* Split(*value*)
* Split(*value*, *sep*)
* Split(*value*, *sep*, *maxsplit*)
* *value*.Split()
* *value*.Split(*sep*)
* *value*.Split(*sep*, *maxsplit*)

If *sep* is not specified, or is `None` or a blank string, the
split is performed on any whitespace character, and empty entries
are omitted.

A pattern can be used as *sep* for more complex parsing.

The *maxsplit* argument is the maximum number of times a split will
occur. If less than zero then there is no limit.

```vgr
None.Split() → []
"a  b \\t c".Split() → ["a", "b", "c"]
"a".Split(",") → ["a"]
",".Split(",") → ["", ""]
"a,b".Split(",") → ["a", "b"]
"a,b,c".Split(",", 1) → ["a", "b,c"]
["Hello", "Goodbye"].Split("oo") → [["Hello"], ["G", "dbye"]]
1234.Split(2) → ["1", "34"]
```

```vgr
"1,2:3".Split(r/[,;:]/)) → ["1", "2", "3"]
// Capture groups appear in the results
"1 2:3 4".Split(r/([,;:])/) → ["1 2", ":", "3 4"]
// When non-group causes split, None is returned
"1 2:3 4".Split(r/([,;:])|[ ]/) → ["1", None, "2", ":", "3", None, "4"]
```

Also see `RSplit()` and `CompilePattern()`
"""
    if isinstance(sep, Pattern): return _re_split(x, sep, maxsplit)
    return _split('Split', poly_split, str.split, x, sep, maxsplit)

@builtin("RSplit")
def poly_rsplit(x: Any=None, sep: str=None, maxsplit: int=-1) -> Any:
    """
**Split a string based on a separator string**

* RSplit(*value*)
* RSplit(*value*, *sep*)
* RSplit(*value*, *sep*, *maxsplit*)
* *value*.RSplit()
* *value*.RSplit(*sep*)
* *value*.RSplit(*sep*, *maxsplit*)

`RSplit()` is identical to `Split()` except that the splitting of
_value_ starts from the end of the string.

```vgr
None.RSplit() → []
"a  b \\t c".RSplit() → ["a", "b", "c"]
"a".RSplit(",") → ["a"]
",".RSplit(",") → ["", ""]
"a,b".RSplit(",") → ["a", "b"]
"a,b,c".RSplit(",", 1) → ["a,b", "c"] // different from Split()
["Hello", "Goodbye"].RSplit("oo") → [["Hello"], ["G", "dbye"]]
1234.RSplit(2) → ["1", "34"]
```

Also see `Split()`
"""
    if isinstance(sep, Pattern): return _re_rsplit(x, sep, maxsplit)
    return _split('RSplit', poly_rsplit, str.rsplit, x, sep, maxsplit)

def _re_split(x: Any, sep: Pattern, maxsplit: int=0):
    if x is None: x = ''
    x = as_str(x)
    if isinstance(x, str):  return re.split(sep, x, max(0, maxsplit))
    if isinstance(x, list): return list(_re_split(x1, sep, maxsplit) for x1 in x)
    if isinstance(x, dict): return {key: _re_split(value, sep, maxsplit) for key, value in x.items()}
    raise TypeError(f'Split of {poly_type(x)!r} not supported')

def _re_rsplit(x: Any, sep: Pattern, maxsplit: int=0):
    if x is None: x = ''
    x = as_str(x)
    if isinstance(x, str):
        maxsplit = max(0, maxsplit)
        if maxsplit == 0: return re.split(sep, x)
        matches = list(sep.finditer(x))
        if not matches: return [x]
        # Only the last `maxsplit` matches act as split points.
        split_matches = matches[-maxsplit:]
        result = []
        prev_end = 0
        for m in split_matches:
            result.append(x[prev_end:m.start()])
            # Include captured groups, same as re.split does
            result.extend(g if g is not None else None for g in m.groups())
            prev_end = m.end()
        result.append(x[prev_end:])
        return result
    if isinstance(x, list): return list(_re_rsplit(x1, sep, maxsplit) for x1 in x)
    if isinstance(x, dict): return {key: _re_rsplit(value, sep, maxsplit) for key, value in x.items()}
    raise TypeError(f'RSplit of {poly_type(x)!r} not supported')

def _split(name: str, p_op, str_op, x: Any, sep: str=None, maxsplit: int=-1):
    if sep is not None:
        if isinstance(sep, (bool, int, float)):
            sep = str(sep)
        else:
            sep = str_arg(sep, 'Sep', False)
            sep = None if sep is None or len(sep) == 0 else sep
    maxsplit = -1 if maxsplit is None else max(-1, int_arg(maxsplit, 'Maxsplit'))
    if x is None: x = ''
    x = as_str(x)
    if isinstance(x, str): return str_op(x, sep, maxsplit)
    if isinstance(x, list): return list(p_op(x1, sep, maxsplit) for x1 in x)
    if isinstance(x, dict): return {key: p_op(value, sep, maxsplit) for key, value in x.items()}
    raise TypeError(f'{name} of {poly_type(x)!r} not supported')
