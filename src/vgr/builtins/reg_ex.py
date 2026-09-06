"""
Functions using regular expressions
"""

from functools import reduce
from typing import Any
from sys import maxsize
import re

from .common import NoneType, apply_vargs
from .type import poly_type
from .registry import builtin

@builtin("IsPattern")
def poly_is_pattern(x:Any=None) -> bool:
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

@builtin("CompilePattern")
def compile_pattern(x: Any=None, flags: int=0) -> Any:
    """
**Create a pre-compiled regular expression pattern**

* CompilePattern(*pattern*)
* CompilePattern(*pattern*, *flags*)
* *pattern*.CompilePattern()
* *pattern*.CompilePattern(*flags*)

The compiled pattern can be used with `RegexReplace()`.
If the *pattern* argument is a list, all the patterns
in the list are compiled.

Use `Exhibit re` to see the values that can be used with *flags*.

```vgr
Set vowel_pattern To CompilePattern("[aeiou]", re.IGNORECASE)
Print ["cat", "DOG"].RegexReplace(vowel_pattern, "-") → ["c-t", "D-G"]
```

Also see `RegexReplace()` as well as `IsPattern()` and `PatternFlags()`.
"""
    if x is None: return None
    if isinstance(x, re.Pattern):
        # Recompile with the provided flags if we have a mismatch
        flags = _compose_flags(flags)
        if flags == x.flags: return x
        x = x.pattern
    if isinstance(x, str):
        try:
            return re.compile(x, _compose_flags(flags))
        except Exception as e:
            raise ValueError(f'Pattern error: {x!r}') from e
    if isinstance(x, list):
        flags = _compose_flags(flags)
        return list(compile_pattern(x1, flags) for x1 in x)
    raise ValueError(f'CompilePattern on {poly_type(x)!r} not supported')

@builtin("PatternFlags")
def poly_pattern_flags(*args) -> Any:
    """
**Creates the flag value for CompilePattern()**

* PatternFlags(*value*)
* *value*.PatternFlags()

The *value* argument may be a number or a string. When a string,
the characters represent the options:

* a - ASCII matching mode for character classes. Unicode is the default.
* d - Displays debug information when a pattern is compiled
* i - Case insensitive matching
* m - Multiline mode which affects `^` `$` matching in text with newlines
* s - "Dot All" mode which affects `.` so it matches newlines
* x - Verbose mode which allows for "verbose" patterns that contain
  extra whitespace for alignment and `#` for the addition of comments

If *value* is a pattern itself, its flags are returned.

"""
    def _pattern_flags(flag) -> Any:
        # this is the only additional check we need here
        if isinstance(flag, list): return list(_pattern_flags(flag1) for flag1 in flag)
        return _compose_flags(flag)
    return apply_vargs(args, _pattern_flags)

def _compose_flags(f: Any) -> int:
    """Called directly by compile pattern, but also used for a builtin"""
    if f is None: return 0
    if isinstance(f, (int, float)): return int(f)
    if isinstance(f, re.Pattern): return f.flags
    if isinstance(f, str):
        flags = 0
        for fc in f.lower():
            if   fc == 'a': flags += re.ASCII
            elif fc == 'd': flags += re.DEBUG
            elif fc == 'i': flags += re.IGNORECASE
            # NB: locale not support as it only works with bytes
            elif fc == 'm': flags += re.MULTILINE
            elif fc == 's': flags += re.DOTALL
            # NB: template not supported as obsolted by verbose
            # NB: unicode not supported as it is redundant
            elif fc == 'x': flags += re.VERBOSE
            else:           raise ValueError(f'Unknown regular expression pattern flag: {fc!r}')
        return flags
    raise ValueError(f'Cannot convert a {poly_type(f)!r} to flags for a pattern')

@builtin("EscapePattern")
def poly_escape_pattern(*args) -> Any:
    """
**Escape regular expression characters for use in literal matching**

* EscapePattern(*pattern*[, *pattern*&hellip;])
* *pattern*.EscapePattern()

Use `EscapePattern()` to perform exact character matching where the
text may contain regular expression meta characters.

```vgr
EscapePattern(None) → None
r/(a|b)+/.EscapePattern() → "\\\\(a\\\\|b\\\\)\\\\+"
EscapePattern("*bold*") → "\\*bold\\*"
"*BOLD*".Matches(CompilePattern(EscapePattern("*bold*"), re.IGNORECASE)) → True
```

Also see `CompilePattern()` and `EscapeGlobPattern()`
"""
    def _escape_pattern(pattern: str) -> str:
        if pattern is None: return None
        if isinstance(pattern, list): return list(_escape_pattern(pattern1) for pattern1 in pattern)
        if isinstance(pattern, (bool, int, float)):
            pattern = str(pattern)
        elif isinstance(pattern, re.Pattern):
            pattern = pattern.pattern
        if isinstance(pattern, str): return re.escape(pattern)
        raise ValueError(f'EscapePattern on {poly_type(pattern)!r} not supported')
    return apply_vargs(args, _escape_pattern)

@builtin("ExtractMatch")
def poly_extract_match(*args) -> Any:
    """
**Extract the first substring matching a Regular Expression**

* ExtractMatch(*value*, *pattern*&hellip;)
* *value*.ExtractMatch(*pattern*&hellip;)

The *value* can be a string or a list. Matching is distributed over lists,
returning a list of matching information.
Individual *pattern* values can be a string or pattern or a list of either.
They can can start with *(?i)* for case indepenent replacement,
*(?m)* for multiline replacement, or combined as *(?im)* for both.
When multiple *pattern* values are provided, information about
the first match is returned.

If nothing matches, then `None` is returned.

```vgr
"food".ExtractMatch("[A-Z]+", r"\\d+") → None

"food".ExtractMatch("[aeiou]+") →
{ "pattern": "[aeiou]+", "match": "oo", "start": 1, "end": 3 }
```

```vgr
["food", "found"].ExtractMatch("[aeiou]+") →
[
  { "pattern": "[aeiou]+", "match": "oo", "start": 1, "end": 3 },
  { "pattern": "[aeiou]+", "match": "ou", "start": 1, "end": 3 }
]
```

```vgr
"food".ExtractMatch("([^aeiou])([aeiou]+)") →
{
  "pattern": "([^aeiou])([aeiou]+)",
  "match": "foo",
  "groups": 2, "group1": "f", "group2": "oo",
  "span": {
    "match":  { "start": 0, "end": 3 },
    "group1": { "start": 0, "end": 1 },
    "group2": { "start": 1, "end": 3 }
  }
}
```

```vgr
"food".ExtractMatch("(?P<cons>[^aeiou])(?P<vowel>[aeiou]+)") →
{
  "pattern": "(?P<cons>[^aeiou])(?P<vowel>[aeiou]+)",
  "match": "foo",
  "groups": [ "cons", "vowel" ],
  "cons": "f", "vowel": "oo",
  "span": {
    "match":  { "start": 0, "end": 3 },
    "cons":   { "start": 0, "end": 1 },
    "vowel":  { "start": 1, "end": 3 }
  }
}
```

Also see `CompilePattern()` and `ExtractAllMatches()`
"""
    if not args: return None
    value, *patterns = args
    if not patterns: return None
    return _regex_search(value, patterns)

@builtin("ExtractAllMatches")
def poly_extract_all_matches(*args) -> Any:
    """
**Extract all substrings matching a Regular Expression**

* ExtractAllMatches(*value*, *pattern*&hellip;)
* *value*.ExtractAllMatches(*pattern*&hellip;)

The *value* can be a string or a list. Matching is distributed over lists,
returning a list of matching information. Successful matches are returned
in a list.
Individual *pattern* values can be a string or pattern or a list of either.
They can can start with *(?i)* for case indepenent replacement,
*(?m)* for multiline replacement, or combined as *(?im)* for both.
When multiple *pattern* values are provided, information about
the first match is returned.

If nothing matches, then `None` is returned.

```vgr
"dog food".ExtractAllMatches("[aeiou]+") →
[
  { "pattern": "[aeiou]+", "match": "o",  "start": 1, "end": 2 },
  { "pattern": "[aeiou]+", "match": "oo", "start": 5, "end": 7 }
]

"dog food".ExtractAllMatches("(?![aeiou])[a-z]") →
[
  { "pattern": "(?![aeiou])[a-z]", "match": "d", "start": 0, "end": 1 },
  { "pattern": "(?![aeiou])[a-z]", "match": "g", "start": 2, "end": 3 },
  { "pattern": "(?![aeiou])[a-z]", "match": "f", "start": 4, "end": 5 },
  { "pattern": "(?![aeiou])[a-z]", "match": "d", "start": 7, "end": 8 }
]

["dog", "food"].ExtractAllMatches("[aeiou]+") →
[
  [ { "pattern": "[aeiou]+", "match": "o",  "start": 1, "end": 2 } ],
  [ { "pattern": "[aeiou]+", "match": "oo", "start": 1, "end": 3 } ]
]
```

```vgr
["dog", "food"].ExtractAllMatches("g") →
[
  [ { "pattern": "g", "match": "g", "start": 2, "end": 3 } ],
  null
]

["dog", "food"].ExtractAllMatches("g", "f") →
[
  [ { "pattern": "g", "match": "g", "start": 2, "end": 3 } ],
  [ { "pattern": "f", "match": "f", "start": 0, "end": 1 } ]
]
```

Also see `CompilePattern()` and `ExtractMatch()`
"""
    if not args: return None
    value, *patterns = args
    if not patterns: return None
    return _regex_search_all(value, patterns)

@builtin("RegexReplace")
def poly_regex_replace(*args) -> Any:
    """
**Regular Expression replacement**

* RegexReplace(*value*, *pattern*)
* RegexReplace(*value*, *pattern*&hellip;, *replacement*)
* *value*.RegexReplace(*pattern*)
* *value*.RegexReplace(*pattern*&hellip;, *replacement*)

The *value* can be a string, list, or a dictionary.
Replacement is distributed over the contents of a list or dictionary.
The *pattern* can be a string or pattern or a list of either.
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
    if not args: return None
    x, *args = args
    if not args: return x
    if len(args) == 1: return _regex_replace(x, args[0], '')
    if len(args) == 2: return _regex_replace(x, args[0], args[1]) # pattern and replacement
    return _regex_replace(x, args[:-1], args[-1]) # pattern is a list, single replacement

def _regex_replace(value: Any, pattern: Any, replacement: Any=None) -> Any:
    # For these types, the operation is idempotent
    if isinstance(value, (NoneType, re.Pattern, bool, int, float)) or pattern is None: return value
    if replacement is None:
        replacement = ''
    else:
        if isinstance(replacement, (bool, int, float)): replacement = str(replacement)
        if not isinstance(replacement, str):
            raise ValueError(f'RegEx Replacement argument must be a string, found {poly_type(replacement)!r}')
    if isinstance(pattern, list):
        return reduce(lambda x, pattern1: _regex_replace(x, pattern1, replacement), pattern, value)
    # in case we are going to loop, pre-compile the pattern
    pattern = _to_pattern(pattern)
    if isinstance(value, re.Pattern): value = value.pattern
    if isinstance(value, str): return re.sub(pattern, replacement, value)
    if isinstance(value, list): return list(_regex_replace(x1, pattern, replacement) for x1 in value)
    if isinstance(value, dict): return {key: _regex_replace(value, pattern, replacement) for key, value in value.items() }
    raise TypeError(f'RegEx replacement on {poly_type(value)!r} not supported')

def _to_pattern(pattern: Any) -> re.Pattern:
    if isinstance(pattern, re.Pattern): return pattern
    if isinstance(pattern, str): return re.compile(pattern)
    raise TypeError(f'Unexpected type for RegEx pattern: {poly_type(pattern)!r}')

def _regex_search(value: Any, pattern: Any) -> Any:
    # For these types, the operation is idempotent
    if isinstance(value, (NoneType, re.Pattern, bool, int, float, dict)) or pattern is None: return None
    if isinstance(pattern, list):
        for p1 in pattern:
            m = _regex_search(value, p1)
            if m is not None: return m
        return None
    # in case we are going to loop, pre-compile the pattern
    pattern = _to_pattern(pattern)
    if isinstance(value, str): return _match(re.search(pattern, value))
    if isinstance(value, list): return list(_regex_search(v1, pattern) for v1 in value)
    raise TypeError(f'RegEx extraction from {poly_type(value)!r} not supported')

def _regex_search_all(value: Any, pattern: Any) -> Any:
    # For these types, the operation is idempotent
    if isinstance(value, (NoneType, re.Pattern, bool, int, float, dict)) or pattern is None: return None
    if isinstance(pattern, list):
        # precomp all patterns
        pattern = list(_to_pattern(p1) for p1 in pattern)
        if isinstance(value, str):
            for p1 in pattern:
                m = _regex_search_all(value, p1)
                if m is not None: return m
            return None
        if isinstance(value, list):
            found = False
            rc = []
            for v1 in value:
                m = None
                for p1 in pattern:
                    m = _regex_search_all(v1, p1)
                    if m is not None:
                        found = True
                        break
                rc.append(m)
            return rc if found else None
    else:
        # in case we are going to loop, pre-compile the pattern
        pattern = _to_pattern(pattern)
        if isinstance(value, str):
            rc = list(_match(m) for m in re.finditer(pattern, value))
            return rc if len(rc) > 0 else None
        if isinstance(value, list): return list(_regex_search_all(v1, pattern) for v1 in value)
    raise TypeError(f'RegEx extraction from {poly_type(value)!r} not supported')

def _match(m: re.Match) -> dict:
    if m is None: return None
    rc = {
        "pattern": m.re.pattern,
    }
    groups = len(m.groups())
    if groups == 0:
        # Simple pattern match produces a very simple output
        rc["match"] = m.group(0)
        rc["start"] = m.start()
        rc["end"] = m.end()
    else:
        if m.lastgroup is not None:
            rc["lastgroup"] = m.lastgroup
        else:
            if m.lastindex is not None: rc["lastgroup"] = f"group{m.lastindex}"
        # When there are groups, start/end info
        # is partioned into "span" by the name
        def _add_group(name, value, start, end):
            if value is not None: rc[name] = value
            if start != -1 and end != -1:
                rc.setdefault("span", {})[name] = { "start": start, "end": end }
        # If no named groups, then groups is how may groups there are
        # If named groups exist, it is the keys for them
        named_groups = list()
        spans = dict()
        for name, value in m.groupdict().items():
            if value is not None:
                named_groups.append(name)
                spans[m.span(name)] = name # we don't use the value...
        rc["groups"] = groups if len(named_groups) == 0 else named_groups
        spans[(m.start(), m.end(),)] = "match"
        _add_group("match", m.group(0), m.start(),m.end())
        # If a positional group does is not already
        # recorded as the match or as a named group, add it
        for i, value in enumerate(m.groups(), start=1):
            span = m.span(i)
            if span not in spans: _add_group(f"group{i}", value, span[0], span[1])
        # NB: If a named group conflicts with one of the numbered (or "matched" or something else)
        #     add a numbered suffix to the old one
        for name in named_groups:
            if name in rc:
                rename = name + "_"
                for n in range(1, maxsize):
                    if rename + str(n) not in rc:
                        rename += str(n)
                        break
                    re
                rc[rename] = rc.pop(name)
                rc["span"][rename] = rc["span"].pop(name)
            start, end = m.span(name)
            _add_group(name, m.groupdict().get(name), start, end)
    return rc
