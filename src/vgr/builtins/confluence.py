"""
Transformational functions to support Confluence
"""

from typing import Any
from urllib.parse import quote

from .common import NoneType, unpack_vargs
from .registry import builtin
from .vpattern import VPattern

_STRONG_DELIMITER = '*'
_EMPHASIS_DELIMITER = '_'
_STRIKETHROUGH_DELIMITER = '-'
_UNDERLINE_DELIMITER = '+'
_CODE_START = '{{'
_CODE_END = '}}'
_BLANK = ''

_TAG_BREAKER_PATTERN = VPattern.compile(r'(\n|\r\n)')
_LINE_BREAK_REPLACEMENT = "\\\\\n"
_WHITESPACE_PATTERN = VPattern.compile(r'\s')

@builtin("ConfluenceStrong")
def cf_strong(*args) -> Any:
    """
**Format text in Confluence as strong text**

* ConfluenceStrong(*value*)
* *value*.ConfluenceStrong()

```vgr
ConfluenceStrong(None) → ""
ConfluenceStrong("strong") → "*strong*"
ConfluenceStrong(["one", "two", "three"]) → ["*one*", "*two*", "*three*"]
```
"""
    if len(args) == 0: return _BLANK
    text = args[0] if len(args) == 1 else list(args)
    if isinstance(text, list): return list(cf_strong(item) for item in text)
    if isinstance(text, dict): return {k: cf_strong(v) for (k, v) in text.items()}
    return _cf_fmt(_cf_sanitize(_cf_to_string(text).strip(), _STRONG_DELIMITER[0]), _STRONG_DELIMITER)

@builtin("ConfluenceEmphasis")
def cf_emphasis(*args) -> Any:
    """
**Format text in Confluence as emphasised text**

* ConfluenceEmphasis(*value*)
* *value*.ConfluenceEmphasis()

```vgr
ConfluenceEmphasis(None) → ""
ConfluenceEmphasis("emphasis") → "_emphasis_"
ConfluenceEmphasis(["one", "two", "three"]) → ["_one_", "_two_", "_three_"]
```
"""
    if len(args) == 0: return _BLANK
    text = args[0] if len(args) == 1 else list(args)
    if isinstance(text, list): return list(cf_emphasis(item) for item in text)
    if isinstance(text, dict): return {k: cf_emphasis(v) for (k, v) in text.items()}
    return _cf_fmt(_cf_sanitize(_cf_to_string(text).strip(), _EMPHASIS_DELIMITER[0]), _EMPHASIS_DELIMITER)

@builtin("ConfluenceUnderline")
def cf_underline(*args) -> Any:
    """
**Format text in Confluence as underlined**

* ConfluenceUnderline(*value*)
* *value*.ConfluenceUnderline()

```vgr
ConfluenceUnderline(None) → ""
ConfluenceUnderline("underlined") → "+underlined+"
ConfluenceUnderline(["one", "two", "three"]) → ["+one+", "+two+", "+three+"]
```
"""
    if len(args) == 0: return _BLANK
    text = args[0] if len(args) == 1 else list(args)
    if isinstance(text, list): return list(cf_underline(item) for item in text)
    if isinstance(text, dict): return {k: cf_underline(v) for (k, v) in text.items()}
    return _cf_fmt(_cf_sanitize(_cf_to_string(text).strip(), _UNDERLINE_DELIMITER[0]), _UNDERLINE_DELIMITER)

@builtin("ConfluenceStrikeThrough")
def cf_strikethrough(*args) -> Any:
    """
**Format text in Confluence as strike-through**

* ConfluenceStrikeThrough(*value*)
* *value*.ConfluenceStrikeThrough()

```vgr
ConfluenceStrikeThrough(None) → ""
ConfluenceStrikeThrough("strikeThrough") → "-strikeThrough-"
ConfluenceStrikeThrough(["one", "two", "three"]) → ["-one-", "-two-", "-three-"]
```
"""
    if len(args) == 0: return _BLANK
    text = args[0] if len(args) == 1 else list(args)
    if isinstance(text, list): return list(cf_strikethrough(item) for item in text)
    if isinstance(text, dict): return {k: cf_strikethrough(v) for (k, v) in text.items()}
    return _cf_fmt(_cf_sanitize(_cf_to_string(text).strip(), _STRIKETHROUGH_DELIMITER[0]), _STRIKETHROUGH_DELIMITER)

@builtin("ConfluenceCode")
def cf_code(*args) -> Any:
    """
**Format text in Confluence as code/monospaced text**

* ConfluenceCode(*value*)
* *value*.ConfluenceCode()

```vgr
ConfluenceCode(None) → ""
ConfluenceCode("code") → "{{code}}"
ConfluenceCode(["one", "two", "three"]) → ["{{one}}", "{{two}}", "{{three}}"]
```
"""
    if len(args) == 0: return _BLANK
    text = args[0] if len(args) == 1 else list(args)
    if isinstance(text, list): return list(cf_code(item) for item in text)
    if isinstance(text, dict): return {k: cf_code(v) for (k, v) in text.items()}
    return _cf_fmt(_cf_sanitize(_cf_to_string(text).strip(), _CODE_START[0] + _CODE_END[0]), _CODE_START, _CODE_END)

@builtin("ConfluenceLink")
def cf_link(*args) -> Any:
    """
**Format a Confluence link tag**

* ConfluenceLink(*url*)
* ConfluenceLink(*url*, *text*)
* ConfluenceLink(*url*, *text*, *title*)
* *url*.ConfluenceLink()
* *url*.ConfluenceLink(*text*)
* *url*.ConfluenceLink(*text*, *title*)

```vgr
ConfluenceLink(None) → ""
ConfluenceLink("https://en.wikipedia.org/wiki/Hello,_world") →
    "[https://en.wikipedia.org/wiki/Hello,_world]"
ConfluenceLink("https://en.wikipedia.org/wiki/Hello,_world", "Hello World") →
    "[Hello World|https://en.wikipedia.org/wiki/Hello,_world]"
ConfluenceLink("https://en.wikipedia.org/wiki/Hello,_world", "Hello World", "A link to Wikipedia") →
    '[Hello World|https://en.wikipedia.org/wiki/Hello,_world|A link to Wikipedia]'
```
"""
    url, text, title, _ = unpack_vargs(args, 3)
    url = _cf_sanitize_url(_cf_to_string(url), "[]|")
    if not url: return _BLANK
    text = _cf_sanitize(_cf_to_string(text), "[]|")
    title = _cf_sanitize(_cf_to_string(title), "[]|")
    if not text:
        if title: # [foo.net|foo.net|the foo")
            return "[" + url + "|" + url + '|' + title + ']'
        # [foo.net]
        return "[" + url + "]"
    if title: # [Foo Net|foo.net|the foo]
        return "[" + text + "|" + url + '|' + title + ']'
    # [Foo Net|foo.net]
    return "[" + text + "|" + url + "]"

@builtin("ConfluenceHeading")
def cf_heading(*args) -> Any:
    """
**Format text in Confluence as a heading**

* ConfluenceHeading(*value*)
* ConfluenceHeading(*value*, *level*)
* *value*.ConfluenceHeading()
* *value*.ConfluenceHeading(*level*)

The default *level* is 1.

```vgr
ConfluenceHeading(None) → ""
ConfluenceHeading("Heading") → "h1. Heading\\n"
ConfluenceHeading("Heading", 3) → "h3. Heading\\n"
ConfluenceHeading("Chapter 1", "Chapter 2") → ["h1. Chapter 1\\n", "h1. Chapter 2\\n"]
```
"""
    if len(args) == 0: return _BLANK
    level = 1
    if len(args) == 1:
        text = args[0] # its the text and level is default
    elif isinstance(args[-1], (int, float)):
        text = args[0] if len(args) == 2 else list(args[0:-1]) # var args w/level at end
        # NB: Confluence only goes to 6, not 11
        level = max(1, min(int(args[-1]), 6))
    else:
        text = list(args) # var args, all text
    if isinstance(text, list): return list(cf_heading(item, level) for item in text)
    if isinstance(text, dict): return {k: cf_heading(v, level) for (k, v) in text.items()}
    text = _cf_to_string(text)
    return _BLANK if len(text) == 0 else ('h' + str(level) + ". " + text).rstrip() + "\n"

@builtin("ConfluenceUnorderedList")
def cf_unordered_list(*args) -> Any:
    """
**Format text in Confluence as an unordered list item**

* ConfluenceUnorderedList(*value*)
* *value*.ConfluenceUnorderedList()

If *value* is a list, each element in it is formated as a list item.

```vgr
ConfluenceUnorderedList(None) → ""
ConfluenceUnorderedList("One\\nTwo\\nThree") → "\\n* One\\n* Two\\n* Three\\n"
ConfluenceUnorderedList(["One", "Two", "Three"]) → "\\n* One\\n* Two\\n* Three\\n"
```
"""
    def _unordered(text: list) -> str:
        return "\n" + ("\n".join([("* " + item.strip()).strip() for item in [_cf_to_string(i) for i in text] if item is not None])) + "\n"
    return _cf_block(_unordered, *args)

@builtin("ConfluenceOrderedList")
def cf_ordered_list(*args) -> Any:
    """
**Format text in Confluence as an ordered list item**

* ConfluenceOrderedList(*value*)
* *value*.ConfluenceOrderedList()

If *value* is a list, each element in it is formated as a list item.
The number for each entry will always be "1." which allows
Confluence to automatically number the entries itself.

```vgr
ConfluenceOrderedList(None) → ""
ConfluenceOrderedList("One\\nTwo\\nThree") →
    "\\n# One\\n# Two\\n# Three\\n"
ConfluenceOrderedList(["One", "Two", "Three"]) →
    "\\n# One\\n# Two\\n# Three\\n"
```
"""
    def _ordered(text: list) -> str:
        return "\n" + ("\n".join([("# " + item.strip()).strip() for item in [_cf_to_string(i) for i in text] if item is not None])) + "\n"
    return _cf_block(_ordered, *args)

@builtin("ConfluenceCodeBlock")
def cf_code_block(*args) -> Any:
    """
**Format text in Confluence as a code block**

* ConfluenceCodeBlock(*value*)
* ConfluenceCodeBlock(*language*, *value*[, &hellip;])
* *value*.ConfluenceCodeBlock()
* *language*.ConfluenceCodeBlock(*value*[, &hellip;])

If *value* is a list, each element in it is formatted as part of the block.

```vgr
ConfluenceCodeBlock(None) → ""
ConfluenceCodeBlock("print('Hello, World')") →
    "\\n```\\nprint('Hello, World')\\n```\\n"
ConfluenceCodeBlock("python", "print('Hello, World')") →
    "\\n```python\nprint('Hello, World')\\n```\\n"
ConfluenceCodeBlock(["primes = [2, 3, 5]", "for p in primes:", "    print(p)"]) →
    "\\n```\\nprimes = [2, 3, 5]\\nfor p in primes:\\n    print(p)\\n```\\n"
```
"""
    lang = ""
    def _code(text: list) -> str:
        s = "\n".join(_cf_to_string(item) for item in text if item is not None)
        if len(s) == 0: return _BLANK
        return ( "\n" +
                ("{code" + (":" + lang if lang else "")) + "}\n" +
                s.rstrip() + "\n" +
                "{code}\n")
    if len(args) == 0: return _BLANK
    if len(args) == 1:
        text = args[0] # its the text and lang is default
    elif isinstance(args[0], (NoneType, str)):
        text = args[1] if len(args) == 2 else list(args[1:]) # var args
        lang = (args[0] or "").strip()
    else:
        text = list(args) # var args, all text
    return _cf_block(_code, text)

def _cf_block(func, *args) -> str:
    if len(args) == 0: return _BLANK
    text = args[0] if len(args) == 1 else list(args)
    if isinstance(text, list): return _BLANK if not text else func(text)
    if isinstance(text, dict): return {k: _cf_block(func, v) for (k, v) in text.items()}
    text = _cf_to_string(text)
    return _BLANK if len(text) == 0 else _cf_block(func, text.splitlines())

def _cf_to_string(s: Any) -> str:
    # NB: most of the time, the caller has performed
    # special processing on lists and dictionaries, so
    # this simplistic text conversion doesn't take place
    if isinstance(s, list): # recursively join elements of a list
        return _BLANK if not s else "\n".join([_cf_to_string(i) for i in s])
    if isinstance(s, dict): # recusively join the items of a dict
        return "\n".join([_cf_to_string(k) + " : " + _cf_to_string(v) for (k, v) in s.items()])
    s = _BLANK if s is None else repr(s) if isinstance(s, VPattern) else str(s)
    return _BLANK if s.isspace() else s

def _cf_fmt(text: str, code_start: str, code_end: str=None) -> str:
    return _BLANK if len(text) == 0 else code_start + text + (code_end or code_start)

def _cf_sanitize(s: str, escape_chars: str="") -> str:
    # We escape any other character that might
    # break the tag, but only if the caller has
    # not passed in pre-escaped versions
    s = VPattern.compile(r'(?<!\\)([' + VPattern.escape(escape_chars) + r'])').sub(r'\\\1', s)
    return _TAG_BREAKER_PATTERN.sub(lambda _: _LINE_BREAK_REPLACEMENT, s) if s else s

def _cf_sanitize_url(s: str, escape_chars: str="") -> str:
    # First perform URL encoding on stripped version
    # which deals with embedded WS breaking things
    s = _WHITESPACE_PATTERN.sub(lambda m: quote(m.group()), s.strip())
    return _cf_sanitize(s, escape_chars)
