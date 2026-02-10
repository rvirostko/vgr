"""
Operators that match part or all of a regular expression.
Includes case independent variations.
"""

from typing import Any
import re

from .common import bound_ops, NoneType
from .type import poly_type

@bound_ops("Matches Any", "~")
def poly_matches(x: Any, *args) -> Any:
    """
**Perform a regular expression match**

* *value* Matches [Any] *pattern*
* *value* Matches [Any] [ _pattern&hellip; ]
* *value* ~ *pattern*
* *value* ~ [ *pattern*&hellip; ]
* Matches(*value*, *pattern*&hellip;)
* *value*.Matches(*pattern*&hellip;)

If *value* is a collection, then *all* values in it must match *pattern*
for the expression to be `True`. If *pattern* is a collection, then one or
more of its contents must match for the expression to be `True`.

```vgr
"aaa" Matches "^(a|b)+$" → True
["aaa", "abba"] Matches "^(a|b)+$" → True
["aaa", "abba", "bad"] Matches "^(a|b)+$" → False
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
    if not args: args = [None]
    return _do_match(x, args[0] if len(args) == 0 else [*args])

@bound_ops("~*")
def poly_imatches(x: Any, y: Any) -> Any:
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
    return _do_match(x, y, True)

@bound_ops("Matches All")
def poly_matches_all(x: Any, *args) -> Any:
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

Also see `Matches Any` and `!~`
"""
    if not args: args = [None]
    return _do_match(x, args[0] if len(args) == 0 else [*args], False, True)

@bound_ops("!~")
def poly_not_matches(x: Any, y: Any) -> Any:
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
    return not _do_match(x, y)

@bound_ops("!~*")
def poly_not_imatches(x: Any, y: Any) -> Any:
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
    return not _do_match(x, y, True)

def _do_match(x: Any, y: Any, ci: bool=False, do_all: bool=False) -> Any:
    # None Matches <Any> and None Matches None
    if x is None: return y is None
    # <Any> Matches None
    if y is None: return False
    # ["aaa", "bb"] Matches "^(a|b)+$" -> True
    if isinstance(x, (list, tuple)):
        return all(_do_match(x1, y, ci, do_all) for x1 in x)
    # 27 Matches 27.0 -> True
    if isinstance(x, (NoneType, bool, int, float)):
        if isinstance(y, (NoneType, bool, int, float)): return x == y
    # a_dictionary Matches "abc" -> Exception
    if not isinstance(x, str):
        raise TypeError(f'Cannot perform Match on {poly_type(x)!r}')
    if isinstance(y, str):
        try:
            y = re.compile(y, re.IGNORECASE if ci else 0)
        except Exception as e:
            raise ValueError(f'Match Pattern error: {y!r}') from e
    # "Ziggy" Matches "^Z" -> True
    if isinstance(y, re.Pattern):
        return re.search(y, x) is not None
    # "Bobby" Matches ["Rob", "Bob"] -> True
    if isinstance(y, (list, tuple)):
        if do_all: return all(_do_match(x, y1, ci, do_all) for y1 in y)
        return any(_do_match(x, y1, ci, do_all) for y1 in y)
    raise TypeError(f'Cannot use {poly_type(y)!r} as a Pattern with Match')
