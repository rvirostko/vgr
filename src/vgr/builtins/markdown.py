"""
Transformational functions to support Markdown
"""

from re import Pattern
from typing import Any
from urllib.parse import quote
import re

from .common import NoneType, unpack_vargs
from .registry import builtin

_MD_STRONG_DELIMITER = '**'
_MD_EMPHASIS_DELIMITER = '_'
_MD_STRIKETHROUGH_DELIMITER = '~~'
_MD_CODE_DELIMITER = '`'
_MD_CODE_FENCE = '```'
_MD_BLOCK_QUOTE_MARKER = '> '
_BLANK = ''

_TAG_BREAKER_PATTERN = re.compile(r'\n{2,}')
_WHITESPACE_PATTERN = re.compile(r'\s')
_INLINE_META_PATTERN = re.compile(r'(?<!\\)([' + re.escape(r'*_~[]()`') + r'])')
_LINE_START_PATTERN = re.compile(r'^([ \t]{0,3})(#{1,6}(?=[ \t]|$)|[->+](?=[ \t]|$))', re.MULTILINE)
_ORDERED_LIST_PATTERN = re.compile(r'^([ \t]{0,3}\d+)([.])([ \t]|$)', re.MULTILINE)
_CODE_DELIMITER_RUN_PATTERN = re.compile(_MD_CODE_DELIMITER + "+")

@builtin("MdStrong")
def md_strong(*args) -> Any:
    """
**Format text in Markdown as strong text**

* MdStrong(*value*)
* *value*.MdStrong()

```vgr
MdStrong(None) → ""
MdStrong("strong") → "**strong**"
MdStrong(["one", "two", "three"]) → ["**one**", "**two**", "**three**"]
```

Also see `Print` and using the *As Markdown* clause.
"""
    if len(args) == 0: return _BLANK
    text = args[0] if len(args) == 1 else list(args)
    if isinstance(text, list): return list(md_strong(item) for item in text)
    if isinstance(text, dict): return {k: md_strong(v) for (k, v) in text.items()}
    return _md_fmt(_md_sanitize(_md_to_string(text), _MD_STRONG_DELIMITER[0]), _MD_STRONG_DELIMITER)

@builtin("MdEmphasis")
def md_emphasis(*args) -> Any:
    """
**Format text in Markdown as emphasised text**

* MdEmphasis(*value*)
* *value*.MdEmphasis()

```vgr
MdEmphasis(None) → ""
MdEmphasis("emphasis") → "_emphasis_"
MdEmphasis(["one", "two", "three"]) → ["_one_", "_two*", "_three_"]
```

Also see `Print` and using the *As Markdown* clause.
"""
    if len(args) == 0: return _BLANK
    text = args[0] if len(args) == 1 else list(args)
    if isinstance(text, list): return list(md_emphasis(item) for item in text)
    if isinstance(text, dict): return {k: md_emphasis(v) for (k, v) in text.items()}
    return _md_fmt(_md_sanitize(_md_to_string(text), _MD_EMPHASIS_DELIMITER[0]), _MD_EMPHASIS_DELIMITER)

@builtin("MdStrikeThrough")
def md_strikethrough(*args) -> Any:
    """
**Format text in Markdown as strike-through**

* MdStrikeThrough(*value*)
* *value*.MdStrikeThrough()

```vgr
MdStrikeThrough(None) → ""
MdStrikeThrough("strikeThrough") → "~~strikeThrough~~"
MdStrikeThrough(["one", "two", "three"]) → ["~~one~~", "~~two~~", "~~three~~"]
```

Also see `Print` and using the *As Markdown* clause.
"""
    if len(args) == 0: return _BLANK
    text = args[0] if len(args) == 1 else list(args)
    if isinstance(text, list): return list(md_strikethrough(item) for item in text)
    if isinstance(text, dict): return {k: md_strikethrough(v) for (k, v) in text.items()}
    return _md_fmt(_md_sanitize(_md_to_string(text), _MD_STRIKETHROUGH_DELIMITER[0]), _MD_STRIKETHROUGH_DELIMITER)

@builtin("MdCode")
def md_code(*args) -> Any:
    """
**Format text in Markdown as code/monospaced text**

* MdCode(*value*)
* *value*.MdCode()

```vgr
MdCode(None) → ""
MdCode("code") → "`code`"
MdCode(["one", "two", "three"]) → ["`one`", "`two`", "`three`"]
```

Also see `Print` and using the *As Markdown* clause.
"""
    if len(args) == 0: return _BLANK
    text = args[0] if len(args) == 1 else list(args)
    if isinstance(text, list): return list(md_code(item) for item in text)
    if isinstance(text, dict): return {k: md_code(v) for (k, v) in text.items()}
    s = _md_to_string(text)
    if s == _BLANK: return _BLANK
    delimiter = _MD_CODE_DELIMITER
    if delimiter in s:
        delimiter *= max((len(r) for r in re.findall(_CODE_DELIMITER_RUN_PATTERN, s))) + 1
    # We need to add some separator between the existing backticks and what we'll
    # add: Markdown seems to ignore this leading/trailing in presentation
    s = " " + s + " " if s.startswith('`') or s.endswith('`') else s
    return _md_fmt(s, delimiter)

@builtin("MdEscape")
def md_escape(*args):
    """**Escape Markdown meta characters so text is treated literally**
* MdEscape(*value)
* *value*.MdEscape()

Most Markdown functions escape only those characters which would "break"
their particular renderings. When working with text that should be
rendedered verbatim, regardless of content, use `MdEscape()`.
"""
    if len(args) == 0: return _BLANK
    text = args[0] if len(args) == 1 else list(args)
    if isinstance(text, list): return list(md_escape(item) for item in text)
    if isinstance(text, dict): return {k: md_escape(v) for (k, v) in text.items()}
    if isinstance(text, str):
        if text.isspace(): return text
        s = text
    else:
        s = _md_to_string(text)
    s = _INLINE_META_PATTERN.sub(r'\\\1', s)
    s = _LINE_START_PATTERN.sub(lambda m: m.group(1) + '\\' + m.group(2), s)
    return _ORDERED_LIST_PATTERN.sub(lambda m: m.group(1) + '\\' + m.group(2) + m.group(3), s)

@builtin("MdLink")
def md_link(*args) -> Any:
    """
**Format a Markdown link tag**

* MdLink(*url*)
* MdLink(*url*, *text*)
* MdLink(*url*, *text*, *title*)
* *url*.MdLink()
* *url*.MdLink(*text*)
* *url*.MdLink(*text*, *title*)

```vgr
MdLink(None) → ""
MdLink("https://en.wikipedia.org/wiki/Hello,_world") →
    "<https://en.wikipedia.org/wiki/Hello,_world>"
MdLink("https://en.wikipedia.org/wiki/Hello,_world", "Hello World") →
    "[Hello World](https://en.wikipedia.org/wiki/Hello,_world)"
MdLink("https://en.wikipedia.org/wiki/Hello,_world", "Hello World", "A link to Wikipedia") →
    '[Hello World](https://en.wikipedia.org/wiki/Hello,_world "A link to Wikipedia")'
```

Also see `Print` and using the *As Markdown* clause.
"""
    url, text, title, _ = unpack_vargs(args, 3)
    url = _md_to_string(url)
    if not url: return _BLANK
    text = _md_to_string(text)
    title = _md_sanitize(_md_to_string(title), '"')
    if not text:
        if title: # [foo.net](foo.net "the foo")
            return "[" + _md_sanitize(url, "[]") + "](" + _md_sanitize_url(url, "()") + ' "' + title  + '")'
        # <foo.net>
        return "<" + _md_sanitize_url(url, "<>") + ">"
    if title: # [Foo Net](foo.net "the foo")
        return "[" + _md_sanitize(text, "[]") + "](" + _md_sanitize_url(url, "()") + ' "' + title + '")'
    # [Foo Net](foo.net)
    return "[" + _md_sanitize(text, "[]") + "](" + _md_sanitize_url(url, "()") + ")"

@builtin("MdImage")
def md_image(*args):
    """
**Format a Markdown image tag**

* MdImage(*url*)
* MdImage(*url*, *alt*)
* MdImage(*url*, *alt*, *title*)
* *url*.MdImage()
* *url*.MdImage(*alt*)
* *url*.MdImage(*alt*, *title*)

```vgr
MdImage(None) → ""
MdImage("https://upload.wikimedia.org/wikipedia/commons/4/48/Markdown-mark.svg") →
    "![](https://upload.wikimedia.org/wikipedia/commons/4/48/Markdown-mark.svg)"
MdImage("https://upload.wikimedia.org/wikipedia/commons/4/48/Markdown-mark.svg", "Markdown logo") →
    "![Markdown logo](https://upload.wikimedia.org/wikipedia/commons/4/48/Markdown-mark.svg)"
MdImage("https://upload.wikimedia.org/wikipedia/commons/4/48/Markdown-mark.svg", "Markdown logo", "The Markdown Mark") →
    '![Markdown logo](https://upload.wikimedia.org/wikipedia/commons/4/48/Markdown-mark.svg "The Markdown Mark")'
```

Also see `Print` and using the *As Markdown* clause.
"""
    url, alt, title, _ = unpack_vargs(args, 3)
    url = _md_to_string(url)
    if not url: return _BLANK
    alt = _md_to_string(alt)
    title = _md_sanitize(_md_to_string(title), '"')
    if title: # ![A Foo](foo.net/img "A foo!")
        return "![" + _md_sanitize(alt, "[]") + "](" + _md_sanitize_url(url, "()") + ' "' + title + '")'
    # ![A Foo](foo.net/img)
    return "![" + _md_sanitize(alt, "[]") + "](" + _md_sanitize_url(url, "()") + ")"

@builtin("MdHeading")
def md_heading(*args) -> Any:
    """
**Format text in Markdown as a heading**

* MdHeading(*value*)
* MdHeading(*value*, *level*)
* *value*.MdHeading()
* *value*.MdHeading(*level*)

The default *level* is 1.

```vgr
MdHeading(None) → ""
MdHeading("Heading") → "# Heading\\n"
MdHeading("Heading", 3) → "### Heading\\n"
MdHeading("Chapter 1", "Chapter 2") → ["# Chapter 1\\n", "# Chapter 1\\n"]
```

Also see `Print` and using the *As Markdown* clause.
"""
    if len(args) == 0: return _BLANK
    level = 1
    if len(args) == 1:
        text = args[0] # its the text and level is default
    elif isinstance(args[-1], (int, float)):
        text = args[0] if len(args) == 2 else list(args[0:-1]) # var args w/level at end
        # NB: Markdown only goes to 6, not 11
        level = max(1, min(int(args[-1]), 6))
    else:
        text = list(args) # var args, all text
    if isinstance(text, list): return list(md_heading(item, level) for item in text)
    if isinstance(text, dict): return {k: md_heading(v, level) for (k, v) in text.items()}
    text = _md_to_string(text)
    return _BLANK if len(text) == 0 else ('#' * level) + " " + text + "\n"

@builtin("MdBlockQuote")
def md_blockquote(*args) -> Any:
    """
**Format text in Markdown as a block quote**

* MdBlockQuote(*value*)
* *value*.MdBlockQuote()

If *value* is a list, each element in it is formatted as part of the block.

```vgr
MdBlockQuote(None) → ""
MdBlockQuote("The Block") →
    "\\n> The Block\\n"
MdBlockQuote(["One", "Two", "Three"]) →
    "\\n> One\\n> Two\\n> Three\\n"
```

Also see `Print` and using the *As Markdown* clause.
"""
    def _quote(text: list) -> str:
        return "\n" + ("\n".join([f"{_MD_BLOCK_QUOTE_MARKER}{line}" for line in [_md_to_string(i) for i in text] if line is not None])) + "\n"
    return _md_block(_quote, *args)

@builtin("MdUnorderedList")
def md_unordered_list(*args) -> Any:
    """
**Format text in Markdown as an unordered list item**

* MdUnorderedList(*value*)
* *value*.MdUnorderedList()

If *value* is a list, each element in it is formated as a list item.

```vgr
MdUnorderedList(None) → ""
MdUnorderedList("One\\nTwo\\nThree") → "\\n- One\\n- Two\\n- Three\\n"
MdUnorderedList(["One", "Two", "Three"]) → "\\n- One\\n- Two\\n- Three\\n"
```

Also see `Print` and using the *As Markdown* clause.
"""
    def _unordered(text: list) -> str:
        return "\n" + ("\n".join([f"- {item}" for item in [_md_to_string(i) for i in text] if item is not None])) + "\n"
    return _md_block(_unordered, *args)

@builtin("MdOrderedList")
def md_ordered_list(*args) -> Any:
    """
**Format text in Markdown as an ordered list item**

* MdOrderedList(*value*)
* *value*.MdOrderedList()

If *value* is a list, each element in it is formated as a list item.
The number for each entry will always be "1." which allows
Markdown to automatically number the entries itself.

```vgr
MdOrderedList(None) → ""
MdOrderedList("One\\nTwo\\nThree") →
    "\\n1. One\\n1. Two\\n1. Three\\n"
MdOrderedList(["One", "Two", "Three"]) →
    "\\n1. One\\n1. Two\\n1. Three\\n"
```

Also see `Print` and using the *As Markdown* clause.
"""
    def _ordered(text: list) -> str:
        # Using "1." for all elements lets MD auto number
        return "\n" + ("\n".join([f"1. {item}" for item in [_md_to_string(i) for i in text] if item is not None])) + "\n"
    return _md_block(_ordered, *args)

@builtin("MdCodeBlock")
def md_code_block(*args) -> Any:
    """
**Format text in Markdown as a code block**

* MdCodeBlock(*value*)
* MdCodeBlock(*language*, *value*[, &hellip;])
* *value*.MdCodeBlock()
* *language*.MdCodeBlock(*value*[, &hellip;])

If *value* is a list, each element in it is formatted as part of the block.

```vgr
MdCodeBlock(None) → ""
MdCodeBlock("print('Hello, World')") →
    "\\n```\\nprint('Hello, World')\\n```\\n"
MdCodeBlock("python", "print('Hello, World')") →
    "\\n```python\nprint('Hello, World')\\n```\\n"
MdCodeBlock(["primes = [2, 3, 5]", "for p in primes:", "    print(p)"]) →
    "\\n```\\nprimes = [2, 3, 5]\\nfor p in primes:\\n    print(p)\\n```\\n"
```

Also see `Print` and using the *As Markdown* clause.
"""
    lang = ""
    def _code(text: list) -> str:
        s = "\n".join(_md_to_string(item) for item in text if item is not None)
        if len(s) == 0: return _BLANK
        fence = _MD_CODE_FENCE
        if fence in s:
            fence = _MD_CODE_DELIMITER * (max((len(r) for r in re.findall(_CODE_DELIMITER_RUN_PATTERN, s))) + 1)
        return "\n" + \
            fence + lang + "\n" + \
            s + "\n" + \
            fence + "\n"
    if len(args) == 0: return _BLANK
    if len(args) == 1:
        text = args[0] # its the text and lang is default
    elif isinstance(args[0], (NoneType, str)):
        text = args[1] if len(args) == 2 else list(args[1:]) # var args
        lang = args[0] or ""
    else:
        text = list(args) # var args, all text
    return _md_block(_code, text)

def _md_block(func, *args) -> str:
    if len(args) == 0: return _BLANK
    text = args[0] if len(args) == 1 else list(args)
    if isinstance(text, list): return _BLANK if not text else func(text)
    if isinstance(text, dict): return {k: _md_block(func, v) for (k, v) in text.items()}
    text = _md_to_string(text)
    return _BLANK if len(text) == 0 else _md_block(func, text.splitlines())

def _md_to_string(s: Any) -> str:
    # NB: most of the time, the caller has performed
    # special processing on lists and dictionaries, so
    # this simplistic text conversion doesn't take place
    if isinstance(s, list): # recursively join elements of a list
        return _BLANK if not s else "\n".join([_md_to_string(i) for i in s])
    if isinstance(s, dict): # recusively join the items of a dict
        return "\n".join([_md_to_string(k) + " : " + _md_to_string(v) for (k, v) in s.items()])
    s = _BLANK if s is None else s.pattern if isinstance(s, Pattern) else str(s)
    return _BLANK if s.isspace() else s

def _md_fmt(text: str, code: str) -> str:
    return _BLANK if len(text) == 0 else code + text + code

def _md_sanitize(s: str, escape_chars: str="") -> str:
    # A run of 2 or more line breaks breaks the tag
    s = _TAG_BREAKER_PATTERN.sub('\n', s)
    if s:
        # Then we escape any other character that might
        # break the tag, but only if the caller has
        # passed in pre-escaped versions
        escaped = re.escape(escape_chars)
        pattern = re.compile(r'(?<!\\)([' + escaped + r'])')
        s = pattern.sub(r'\\\1', s)
    return s

def _md_sanitize_url(s: str, escape_chars: str="") -> str:
    # First perform URL encoding on stripped version
    # which deals with embedded WS breaking things
    s = _WHITESPACE_PATTERN.sub(lambda m: quote(m.group()), s.strip())
    return _md_sanitize(s, escape_chars)
