"""
Operators that match part or all of a regular expression.
Includes case independent variations.
"""

from typing import Any
import re

from .common import bound_ops
from .inequ import poly_eq
from .types import poly_to_string

def _pop_single(args): return args[0] if len(args) == 1 else [*args]

@bound_ops("Matches", "~")
def poly_matches(*args) -> bool:
    """
**Perform a regular expression match**

* *value* Matches *pattern*
* *value* Matches [ _pattern&hellip; ]
* *value* ~ *pattern*
* *value* ~ [ *pattern*&hellip; ]
* Matches(*value*, *pattern*&hellip;)
* *value*.Matches(*pattern*&hellip;)

If pattern is a string it is compiled to a regular expression.
Additionally, regular expression literals can also be used.

```vgr
"aaa" Matches "^(a|b)+$"                 # automatically compiled
"aaa" Matches CompilePattern("^(a|b)+$") # explicit compilation
"aaa" Matches r/^(a|b)+$/                # literal regular expression
```

If *value* is a collection, then *all* values in it must match *pattern*
for the expression to be `True`. If *pattern* is a collection, then
at least one its contents must match for the expression to be `True`.

```vgr
"aaa" Matches "^(a|b)+$" → True
"bb" Matches "^(a|b)+$" → True
["aaa", "bb"] Matches "^(a|b)+$" → True
["aaa", "bb", "cab"] Matches "^(a|b)+$"
 → False  # "cab" did not match
```

In its functional form, one or values for *pattern* may be specified, acting as
if it was a collection of patterns connected by *or*.

```vgr
"aaa".Matches("^a+$", "^b+$") → True    # all "a"s
"bbb".Matches("^a+$", "^b+$") → True    # all "b"s
"abba".Matches("^a+$", "^b+$") → False  # neither all "a"s or "b"s
```

While fundamentally a string/regular expression operation, it will
work with ordinals, but only if the *pattern* is also an ordinal, performing an
equality comparison.

```vgr
5 Matches 5 → True
5 Matches 10 → False
5 Matches [5, 10] → True
```

Also see operators `Does Not Match` and `Matches All` as well as `CompilePattern()`
"""
    if not args: return False
    x, *args = args
    return _do_match(x, _pop_single(args)) if args else False

@bound_ops("Matches All")
def poly_matches_all(*args) -> bool:
    """
**Perform a regular expression match**

* *value* Matches All *pattern*
* *value* Matches All [*pattern*&hellip;]
* MatchesAll(*value*, *pattern*&hellip;)
* *value*.MatchesAll(*pattern*&hellip;)

Operates indentically to `Matches` except *value* must match *all* of the
patterns. When *pattern* is a single value, or a collection with exactly one
value, it operates identically to `Matches`. When a colleciton of patterns
of is provided, *all* must match.

```vgr
"aaa".MatchesAll("^a+$") → True
"aaa".MatchesAll("^a+$", "^b+$") → False
```

Also see `Matches` and `!~`
"""
    if not args: return False
    x, *args = args
    return _do_match(x, _pop_single(args), True) if args else False

@bound_ops("Does Not Match", "!~")
def poly_not_match(*args) -> bool:
    """
**Perform a negated regular expression match**

* *value* Does Not Match *pattern*
* *value* Does Not Match [*pattern*&hellip;]
* *value* !~ *pattern*
* *value* !~ [ *pattern*&hellip; ]
* DoesNotMatch(*value*, *pattern*&hellip;)
* *value*.DoesNotMatch(*pattern*&hellip;)

Operates identically to `Matches` except that it requires that *value*
does *not* match any of the patterns.

```vgr
"aaa" !~ "^b+$" → True
"aaa" !~ ["^a+$", "^b+$"] → False
"abba" !~ ["^a+$", "^b+$"] → True
```

Also see operator `~`
"""
    if not args: return False
    x, *args = args
    return not _do_match(x, _pop_single(args)) if args else False

def _do_match(x: Any, y: Any, do_all: bool=False) -> bool:
    if isinstance(y, list):
        if do_all: return all(_do_match(x, y1, do_all) for y1 in y)
        return any(_do_match(x, y1, do_all) for y1 in y)
    if x is None: return y is None
    if isinstance(x, list):
        return all(_do_match(x1, y, do_all) for x1 in x)
    if isinstance(x, (bool, int, float)) and isinstance(y, (bool, int, float)): return poly_eq(x, y)
    if y is None: return False
    if not isinstance(y, re.Pattern):
        try:
            y = re.compile(str(y))
        except Exception as e:
            raise ValueError(f'Match Pattern error: {y!r}') from e
    return re.search(y, poly_to_string(x)) is not None
