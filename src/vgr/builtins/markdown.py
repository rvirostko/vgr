"""
Transformational functions to support markdown
"""

from itertools import starmap
from typing import Any

from .common import int_arg
from .types import poly_to_string
from .registry import builtin

_MD_STRONG_DELIMITER = '**'
_MD_EMPHASIS_DELIMITER = '*'
_MD_STRIKETHROUGH_DELIMITER = '~~'
_MD_CODE_DELIMITER = '`'
_MD_CODE_FENCE = '```'
_MD_BLOCK_QUOTE_MARKER = '> '
_BLANK = ''

def _meld(func, coll1, coll2):
    return type(coll1)(starmap(func, zip(coll1, coll2)))

def _to_str(s):
    if s is None: return _BLANK
    s = str(s)
    if s.isspace(): return _BLANK
    return s

def _fmt(text: str, code: str) -> str:
    return _BLANK if len(text) == 0 else f"{code}{text}{code}"

@builtin("MdStrong")
def md_strong(text: Any=None) -> Any:
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
    if isinstance(text, list): return type(text)(md_strong(item) for item in text)
    return _fmt(_to_str(text), _MD_STRONG_DELIMITER)

@builtin("MdEmphasis")
def md_emphasis(text: Any=None) -> Any:
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
    if isinstance(text, list): return type(text)(md_emphasis(item) for item in text)
    return _fmt(_to_str(text), _MD_EMPHASIS_DELIMITER)

@builtin("MdStrikeThrough")
def md_strikethrough(text: Any=None) -> Any:
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
    if isinstance(text, list): return type(text)(md_strikethrough(item) for item in text)
    return _fmt(_to_str(text), _MD_STRIKETHROUGH_DELIMITER)

@builtin("MdCode")
def md_code(text: Any=None) -> Any:
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
    if isinstance(text, list): return type(text)(md_code(item) for item in text)
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
def md_heading(text: Any=None, level: int=1) -> Any:
    """
**Format the text in Markdown as a heading**

* MdHeading(*value*)
* MdHeading(*value*, *level*)
* *value*.MdHeading()
* *value*.MdHeading(*level*)

```vgr
MdHeading(None) → ""
MdHeading("Heading") → "# Heading\\n"
MdHeading("Heading", 3) → "### Heading\\n"
```

Also see `Print` and using the *As Markdown* clause.
"""
    level = int_arg(level, "Level")
    # NB: Markdown only goes to 6, not 11
    level = 1 if level is None else max(1, min(level, 6))
    if isinstance(text, (list, type)): return type(text)(md_heading(item, level) for item in text)
    text = _to_str(text)
    return _BLANK if len(text) == 0 else f"{'#' * level} {text}\n"

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
