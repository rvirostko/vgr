"""
Transformational functions to support Markdown
"""

from itertools import starmap
from re import Pattern
from typing import Any

from .types import poly_to_string
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
    return _fmt(_to_str(text), _MD_STRONG_DELIMITER)

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
    return _fmt(_to_str(text), _MD_EMPHASIS_DELIMITER)

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
    return _fmt(_to_str(text), _MD_STRIKETHROUGH_DELIMITER)

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
    return _fmt(_to_str(text), _MD_CODE_DELIMITER)

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
    if isinstance(text, list) and isinstance(url, list):
        return _meld(md_link, text, url)
    text = _to_str(text)
    url = _to_str(url)
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
    text = _to_str(text)
    return _BLANK if len(text) == 0 else ('#' * level) + " " + text + "\n"

@builtin("MdBlockQuote")
def md_blockquote(text: Any=None) -> Any:
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
    if isinstance(text, list):
        if not text: return _BLANK
        return "\n" + ("\n".join([f"{_MD_BLOCK_QUOTE_MARKER}{line}" for line in [poly_to_string(i) for i in text] if line is not None])) + "\n"
    text = _to_str(text)
    return _BLANK if len(text) == 0 else md_blockquote(text.splitlines())

@builtin("MdUnorderedList")
def md_unordered_list(text: Any=None) -> Any:
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
    if isinstance(text, list):
        if not text: return _BLANK
        return "\n" + ("\n".join([f"- {item}" for item in [poly_to_string(i) for i in text] if item is not None])) + "\n"
    text = _to_str(text)
    return _BLANK if len(text) == 0 else md_unordered_list(text.splitlines())

@builtin("MdOrderedList")
def md_ordered_list(text: Any=None) -> Any:
    """
**Format the text in Markdown as an ordered list item**

* MdOrderedList(*value*)
* *value*.MdOrderedList()

If *value* is a list, each element in it is formated as a list item.

```vgr
MdOrderedList(None) → ""
MdOrderedList("One\\nTwo\\nThree") →
    "\\n1. One\\n2. Two\\n3. Three\\n"
MdOrderedList(["One", "Two", "Three"]) →
    "\\n1. One\\n2. Two\\n3. Three\\n"
```

Also see `Print` and using the *As Markdown* clause.
"""
    if isinstance(text, list):
        if not text: return _BLANK
        # Convert to strings, then filter out the nulls
        strs = [poly_to_string(i) for i in text]
        strs = [item for item in strs if item is not None and len(item) != 0]
        # Now enumerate to get the index
        return "\n" + ("\n".join([f"{index + 1}. {item}" for index, item in enumerate(strs)])) + "\n"
    text = _to_str(text)
    return _BLANK if len(text) == 0 else md_ordered_list(text.splitlines())

@builtin("MdCodeBlock")
def md_code_block(text: Any=None, lang: str=None) -> Any:
    """
**Format the text in Markdown as a code block**

* MdCodeBlock(*value*)
* MdCodeBlock(*value*, *language*)
* *value*.MdCodeBlock()
* *value*.MdCodeBlock(*language*)

If *value* is a list, each element in it is formatted as part of the block.

```vgr
MdCodeBlock(None) → ""
MdCodeBlock("print('Hello, World')") →
    "\\n```\\nprint('Hello, World')\\n```\\n\\n"
MdCodeBlock("print('Hello, World')", "python") →
    "\\n```python\nprint('Hello, World')\\n```\\n\\n"
MdCodeBlock(["primes = [2, 3, 5]", "for p in primes:", "    print(p)"]) →
    "\\n\\n```\\nprimes = [2, 3, 5]\\nfor p in primes:\\n    print(p)\\n```\\n\\n"
```

Also see `Print` and using the *As Markdown* clause.
"""
    lang = _to_str(lang)
    if isinstance(text, list):
        if not text: return _BLANK
        return "\n" + md_code_block("\n".join(item for item in text if item is not None), lang)
    text = _to_str(text)
    return _BLANK if len(text) == 0 else f"\n{_MD_CODE_FENCE}{lang}\n{text}\n{_MD_CODE_FENCE}\n\n"

def _meld(func, coll1, coll2):
    return type(coll1)(starmap(func, zip(coll1, coll2)))

def _to_str(s: Any) -> str:
    s = _BLANK if s is None else s.pattern if isinstance(s, Pattern) else str(s)
    return _BLANK if s.isspace() else s

def _fmt(text: str, code: str) -> str:
    return _BLANK if len(text) == 0 else f"{code}{text}{code}"
