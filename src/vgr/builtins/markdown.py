"""
Transformational functions to support Markdown
"""

from itertools import starmap
from re import Pattern
from typing import Any

from .common import NoneType
from .registry import builtin

_MD_STRONG_DELIMITER = '**'
_MD_EMPHASIS_DELIMITER = '*'
_MD_STRIKETHROUGH_DELIMITER = '~~'
_MD_CODE_DELIMITER = '`'
_MD_CODE_FENCE = '```'
_MD_BLOCK_QUOTE_MARKER = '> '
_BLANK = ''

@builtin("MdStrong")
def md_strong(*args) -> Any:
    """
**Format the text in Markdown as strong text**

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
    return _md_fmt(_md_to_string(text), _MD_STRONG_DELIMITER)

@builtin("MdEmphasis")
def md_emphasis(*args) -> Any:
    """
**Format the text in Markdown as emphasised text**

* MdEmphasis(*value*)
* *value*.MdEmphasis()

```vgr
MdEmphasis(None) → ""
MdEmphasis("emphasis") → "*emphasis*"
MdEmphasis(["one", "two", "three"]) → ["*one*", "*two*", "*three*"]
```

Also see `Print` and using the *As Markdown* clause.
"""
    if len(args) == 0: return _BLANK
    text = args[0] if len(args) == 1 else list(args)
    if isinstance(text, list): return list(md_emphasis(item) for item in text)
    if isinstance(text, dict): return {k: md_emphasis(v) for (k, v) in text.items()}
    return _md_fmt(_md_to_string(text), _MD_EMPHASIS_DELIMITER)

@builtin("MdStrikeThrough")
def md_strikethrough(*args) -> Any:
    """
**Format the text in Markdown as strike-through**

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
    return _md_fmt(_md_to_string(text), _MD_STRIKETHROUGH_DELIMITER)

@builtin("MdCode")
def md_code(*args) -> Any:
    """
**Format the text in Markdown as code text**

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
    return _md_fmt(_md_to_string(text), _MD_CODE_DELIMITER)

@builtin("MdLink")
def md_link(text: Any=None, url: Any=None) -> Any:
    """
**Format the text in Markdown as a link**

* MdLink(*url*)
* MdLink(*value*, *url*)
* *value*.MdLink(*url*)
* *url*.MdLink()

```vgr
MdLink(None) → ""
MdLink("https://en.wikipedia.org/wiki/Hello,_world") →
    "<https://en.wikipedia.org/wiki/Hello,_world>"
MdLink("Hello World", "https://en.wikipedia.org/wiki/Hello,_world") →
    "[Hello World](https://en.wikipedia.org/wiki/Hello,_world)"
```

Also see `Print` and using the *As Markdown* clause.
"""
    def _meld(func, coll1, coll2):
        return type(coll1)(starmap(func, zip(coll1, coll2)))
    if isinstance(text, list) and isinstance(url, list):
        return _meld(md_link, text, url)
    text = _md_to_string(text)
    url = _md_to_string(url)
    if len(url) == 0:
        return _BLANK if len(text) == 0 else "<" + text + ">"
    return "[" + text + "](" + url + ")"

@builtin("MdHeading")
def md_heading(*args) -> Any:
    """
**Format the text in Markdown as a heading**

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
**Format the text in Markdown as a block quote**

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
**Format the text in Markdown as an unordered list item**

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
**Format the text in Markdown as an ordered list item**

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
**Format the text in Markdown as a code block**

* MdCodeBlock(*value*)
* MdCodeBlock(*language*, *value*[, &hellip;])
* *value*.MdCodeBlock()
* *language*.MdCodeBlock(*value*[, &hellip;])

If *value* is a list, each element in it is formatted as part of the block.

```vgr
MdCodeBlock(None) → ""
MdCodeBlock("print('Hello, World')") →
    "\\n```\\nprint('Hello, World')\\n```\\n\\n"
MdCodeBlock("python", "print('Hello, World')") →
    "\\n```python\nprint('Hello, World')\\n```\\n\\n"
MdCodeBlock(["primes = [2, 3, 5]", "for p in primes:", "    print(p)"]) →
    "\\n\\n```\\nprimes = [2, 3, 5]\\nfor p in primes:\\n    print(p)\\n```\\n\\n"
```

Also see `Print` and using the *As Markdown* clause.
"""
    print("!!", repr(args))
    if len(args) == 0: return _BLANK
    lang = ""
    if len(args) == 1:
        text = args[0] # its the text and lang is default
    elif isinstance(args[0], (NoneType, str)):
        text = args[1] if len(args) == 2 else list(args[1:]) # var args
        lang = args[0] or ""
    else:
        text = list(args) # var args, all text
    def _code(text: list) -> str:
        t = "\n".join(_md_to_string(item) for item in text if item is not None)
        return _BLANK if len(t) == 0 else f"\n{_MD_CODE_FENCE}{lang}\n{t}\n{_MD_CODE_FENCE}\n\n"
    return _md_block(_code, text)

def _md_block(func, *args) -> str:
    if len(args) == 0: return _BLANK
    text = args[0] if len(args) == 1 else list(args)
    if isinstance(text, list):
        return _BLANK if not text else func(text)
    if isinstance(text, dict): return {k: _md_block(func, v) for (k, v) in text.items()}
    text = _md_to_string(text)
    return _BLANK if len(text) == 0 else _md_block(func, text.splitlines())

def _md_to_string(s: Any) -> str:
    s = _BLANK if s is None else s.pattern if isinstance(s, Pattern) else str(s)
    return _BLANK if s.isspace() else s

def _md_fmt(text: str, code: str) -> str:
    return _BLANK if len(text) == 0 else f"{code}{text}{code}"
