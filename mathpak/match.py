"""
Operators that match part or all of a regular expression.
Includes case independent variations.
"""

from typing import Any
import re

from .common import bound_ops, NoneType, type_str

@bound_ops("~", "Matches", "Matches-Any")
def poly_matches(x: Any, *args) -> Any:
    """
**Perform a regular expression match**

* _value_ ~ _pattern_
* _value_ ~ [ _pattern_... ]
* _value_ Matches [Any] _pattern_
* _value_ Matches [Any] [ _pattern_... ]
* _value_.Matches(_pattern_...)

If _value_ is a collection, then _all_ values in it must match _pattern_
for the expression to be _True_. If _pattern_ is a collection, then one or
more of its contents must match for the expression to be _True_.

* `"aaa" Matches "^(a|b)+$"` → `True`
* `["aaa", "abba"] Matches "^(a|b)+$"` → `True`
* `["aaa", "abba", "bad"] Matches "^(a|b)+$"` → `False`

In its functional form, one or values for _pattern_ may be specified, acting as
if it was a collection of patterns.

* `"aaa".Matches("^a+$", "^b+$")` → `True`
* `"bbb".Matches("^a+$", "^b+$")` → `True`
* `"abba".Matches("^a+$", "^b+$")` → `False`

While fundamentally a string/regular expression operation, it will
work with ordinals, but only if the _pattern_ is also an ordinal, performing an
equality comparison.

* `5 ~ 5` → `True`
* `5 ~ 10` → `False`
* `5 ~ [5, 10]` → _error_

Also see operators `!~` and `~*`
"""
    if not args: args = [None]
    return _do_match(x, args[0] if len(args) == 0 else [*args])

@bound_ops("~*")
def poly_imatches(x: Any, y: Any) -> Any:
    """
**Perform a case independent regular expression match**

* _value_ ~* _pattern_
* _value_ ~* [ _pattern_... ]

Operates identically to `Matches` except matching is performed independent
of case. This applies to characters in both the _value_ and the _pattern_.

* `"aaa" ~* "^(a|b)+$"` → `True`
* `"Aaa" ~* "^(a|b)+$"` → `True`
* `"aaa" ~* "^(A|b)+$"` → `True`

Also see operators `~` and `!~*`
"""
    return _do_match(x, y, True)

@bound_ops("Matches-All")
def poly_matches_all(x: Any, *args) -> Any:
    """
**Perform a regular expression match**

* _value_ Matches All _pattern_
* _value_ Matches All [_pattern_...]
* _value_.MatchesAll(_pattern_...)

Operates indentically to `Matches` except _value_ must match _all_ of the
patterns. When _pattern_ is a single value, or a collection with exactly one
value, it operates identically to `Matches`. When a colleciton of patterns
of is provided, _all_ must match.

* `"aaa".MatchesAll("^a+$")` → `True`
* `"aaa".MatchesAll("^a+$", "^b+$")` → `False`
"""
    if not args: args = [None]
    return _do_match(x, args[0] if len(args) == 0 else [*args], False, True)

@bound_ops("!~")
def poly_not_matches(x: Any, y: Any) -> Any:
    """
**Perform a negated regular expression match**

* _value_ !~ _pattern_
* _value_ !~ [ _pattern_... ]

Operates identically to `Matches` except that it requires that _value_
does _not_ match any of the patterns.

* `"aaa" !~ "^b+$"` → `True`
* `"aaa" !~ ["^a+$", "^b+$"]` → `False`
* `"abba" !~ ["^a+$", "^b+$"]` → `True`

Also see operators `~` and `!~*`
"""
    return not _do_match(x, y)

@bound_ops("!~*")
def poly_not_imatches(x: Any, y: Any) -> Any:
    """
**Perform a negated case independent regular expression match**

* _value_ !~* _pattern_
* _value_ !~* [ _pattern_... ]

Operates identically to `Matches` except that the match is performed independent
of case and it request that _value_ does _not_ match any of the patterns.

* `"Aaa" !~* "^b+$"` → `True`
* `"aaa" !~* ["^A+$", "^B+$"]` → `False`
* `"Abba" !~* ["^a+$", "^b+$"]` → `True`

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
        raise TypeError(f'Cannot perform Match on {type_str(x)}')
    if isinstance(y, str):
        try:
            y = re.compile(y, re.IGNORECASE if ci else 0)
        except Exception as e:
            raise ValueError(f'Match Pattern error: {repr(y)}') from e
    # "Ziggy" Matches "^Z" -> True
    if isinstance(y, re.Pattern):
        return re.search(y, x) is not None
    # "Bobby" Matches ["Rob", "Bob"] -> True
    if isinstance(y, (list, tuple)):
        if do_all: return all(_do_match(x, y1, ci, do_all) for y1 in y)
        return any(_do_match(x, y1, ci, do_all) for y1 in y)
    raise TypeError(f'Cannot use {type_str(y)} as a Pattern with Match')
