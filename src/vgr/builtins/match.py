"""
Operators that match part or all of a regular expression.
Includes case independent variations.
"""

from typing import Any
import re

from .common import bound_ops

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

If *value* is a collection, then *all* values in it must match *pattern*
for the expression to be `True`. If *pattern* is a collection, then one or
more of its contents must match for the expression to be `True`.

```vgr
"aaa" Matches "^(a|b)+$" → True
"bb" Matches "^(a|b)+$" → True
["aaa", "bb"] Matches "^(a|b)+$" → False
["aaa", "bb", "abba"] Matches "^(a|b)+$" → False
```

In its functional form, one or values for *pattern* may be specified, acting as
if it was a collection of patterns.

```vgr
"aaa".Matches("^a+$", "^b+$") → True
"bbb".Matches("^a+$", "^b+$") → True
"abba".Matches("^a+$", "^b+$") → False
```

While fundamentally a string/regular expression operation, it will
work with ordinals, but only if the *pattern* is also an ordinal, performing an
equality comparison.

```vgr
5 ~ 5 → True
5 ~ 10 → False
5 ~ [5, 10] → Cannot perform Match on 'int'
```

Also see operators `!~` and `~*`
"""
    if not args: return False
    x, *args = args
    return _do_match(x, args[0] if len(args) == 1 else [*args])

@bound_ops("~*")
def poly_imatches(*args) -> bool:
    """
**Perform a case independent regular expression match**

* *value* ~* *pattern*
* *value* ~* [ *pattern*&hellip; ]

Operates identically to `Matches` except matching is performed independent
of case. This applies to characters in both the *value* and the *pattern*.

```vgr
"aaa" ~* "^(a|b)+$" → True
"Aaa" ~* "^(a|b)+$" → True
"aaa" ~* "^(A|b)+$" → True
```

Also see operators `~` and `!~*`
"""
    if not args: return False
    x, *args = args
    return _do_match(x,  args[0] if len(args) == 1 else [*args], True)

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
    return _do_match(x,  args[0] if len(args) == 1 else [*args], False, True)

@bound_ops("!~")
def poly_not_matches(*args) -> bool:
    """
**Perform a negated regular expression match**

* *value* !~ *pattern*
* *value* !~ [ *pattern*&hellip; ]

Operates identically to `Matches` except that it requires that *value*
does *not* match any of the patterns.

```vgr
"aaa" !~ "^b+$" → True
"aaa" !~ ["^a+$", "^b+$"] → False
"abba" !~ ["^a+$", "^b+$"] → True
```

Also see operators `~` and `!~*`
"""
    if not args: return False
    x, *args = args
    return not _do_match(x, args[0] if len(args) == 1 else [*args])

@bound_ops("!~*")
def poly_not_imatches(*args) -> bool:
    """
**Perform a negated case independent regular expression match**

* *value* !~* *pattern*
* *value* !~* [ *pattern*&hellip; ]

Operates identically to `Matches` except that the match is performed independent
of case and it request that *value* does _not_ match any of the patterns.

```vgr
"Aaa" !~* "^b+$" → True
"aaa" !~* ["^A+$", "^B+$"] → False
"Abba" !~* ["^a+$", "^b+$"] → True
```

Also see operators `~*` and `!~`
"""
    if not args: return False
    x, *args = args
    return not _do_match(x, args[0] if len(args) == 1 else [*args], True)

def _do_match(x: Any, y: Any, ci: bool=False, do_all: bool=False) -> bool:
    if isinstance(y, list):
        if do_all: return all(_do_match(x, y1, ci, do_all) for y1 in y)
        return any(_do_match(x, y1, ci, do_all) for y1 in y)
    if x is None: return y is None
    if isinstance(x, list):
        return all(_do_match(x1, y, ci, do_all) for x1 in x)
    if y is None: return False
    if not isinstance(y, re.Pattern):
        try:
            y = re.compile(str(y), re.IGNORECASE if ci else 0)
        except Exception as e:
            raise ValueError(f'Match Pattern error: {y!r}') from e
    return re.search(y, str(x)) is not None
