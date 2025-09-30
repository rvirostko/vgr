"""
Transformational functions to support markdown
"""

from itertools import starmap
from typing import Any

from .types import poly_str, poly_int

_MD_BOLD = '**'
_MD_CODE_BLOCK = '```'
_MD_BLOCK_QUOTE = '> '
_MD_ITALICS = '_'
_MD_STRIKETHROUGH = '~~'
_MD_CODE = '`'
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

def md_bold(text: Any) -> Any:
    """
**Format the text in Markdown as bold**

* _value_.MdBold()

```vgr
**TODO**
```
"""
    if isinstance(text, (list, type)): return type(text)(md_bold(item) for item in text)
    return _fmt(_to_str(text), _MD_BOLD)

def md_italics(text: Any) -> Any:
    """
**Format the text in Markdown as italics**

* _value_.MdItalics()

```vgr
**TODO**
```
"""
    if isinstance(text, (list, type)): return type(text)(md_italics(item) for item in text)
    return _fmt(_to_str(text), _MD_ITALICS)

def md_strikethrough(text: Any) -> Any:
    """
**Format the text in Markdown as strike-through**

* _value_.MdStrikeThrough()
"""
    if isinstance(text, (list, type)): return type(text)(md_strikethrough(item) for item in text)
    return _fmt(_to_str(text), _MD_STRIKETHROUGH)

def md_code(text: Any) -> Any:
    """
**Format the text in Markdown as code**

* _value_.MdCode()

```vgr
**TODO**
```
"""
    if isinstance(text, (list, type)): return type(text)(md_code(item) for item in text)
    return _fmt(_to_str(text), _MD_CODE)

def md_link(text: Any, url: Any) -> Any:
    """
**Format the text in Markdown as a link**

* _value_.MdLink(_url_)

```vgr
**TODO**
```
"""
    if isinstance(text, (list, tuple)) and isinstance(url, (list, tuple)):
        return _meld(md_link, text, url)
    text = _to_str(text)
    url = _to_str(url)
    return _BLANK if len(text) == 0 or len(url) == 0 else f"[{text}]({url})"

def md_heading(text: Any, level: int=1) -> Any:
    """
**Format the text in Markdown as a heading**

* _value_.MdHeading() _level_ _1_
* _value_.MdHeading(_level_) _range_ _1_ _to_ _6_

```vgr
**TODO**
```
"""
    level = poly_int(level)
    # NB: Markdown only goes to 6, not 11
    level = 1 if level is None else max(1, min(level, 6))
    if isinstance(text, (list, type)): return type(text)(md_heading(item, level) for item in text)
    text = _to_str(text)
    return _BLANK if len(text) == 0 else f"{'#' * level} {text}\n"

def md_blockquote(text: Any) -> Any:
    """
**Format the text in Markdown as a block quote**

* _value_.MdBlockQuote()

If _value_ is a list, each element in it is formatted as part of the block.

```vgr
**TODO**
```
"""
    if isinstance(text, (list, tuple)):
        if not text: return _BLANK
        return "\n".join([f"{_MD_BLOCK_QUOTE}{line}" for line in [poly_str(i) for i in text] if line is not None])
    text = _to_str(text)
    return _BLANK if len(text) == 0 else md_blockquote(text.splitlines())

def md_unordered_list(text: Any) -> Any:
    """
**Format the text in Markdown as an unordered list item**

* _value_.MdUnorderedList()

If _value_ is a list, each element in it is formated as a list item.

```vgr
**TODO**
```
"""
    if isinstance(text, (list, tuple)):
        if not text: return _BLANK
        return "\n".join([f"- {item}" for item in [poly_str(i) for i in text] if item is not None])
    text = _to_str(text)
    return _BLANK if len(text) == 0 else md_unordered_list(text.splitlines())

def md_ordered_list(text: Any) -> Any:
    """
**Format the text in Markdown as an ordered list item**

* _value_.MdOrderedList()

If _value_ is a list, each element in it is formated as a list item.

```vgr
**TODO**
```
"""
    if isinstance(text, (list, tuple)):
        if not text: return _BLANK
        # Convert to strings, then filter out the nulls
        strs = [poly_str(i) for i in text]
        strs = [item for item in strs if item is not None and len(item) != 0]
        # Now enumerate to get the index
        return "\n".join([f"{index + 1}. {item}" for index, item in enumerate(strs)])
    text = _to_str(text)
    return _BLANK if len(text) == 0 else md_ordered_list(text.splitlines())

def md_code_block(text: Any, lang: str=None) -> Any:
    """
**Format the text in Markdown as a code block**

* _value_.MdCodeBlock()
* _value_.MdCodeBlock(_language_)

If _value_ is a list, each element in it is formatted as part of the block.

```vgr
**TODO**
```
"""
    lang = _to_str(lang)
    if isinstance(text, (list, tuple)):
        if not text: return _BLANK
        return md_code_block("\n".join(item for item in text if item is not None), lang)
    text = _to_str(text)
    return _BLANK if len(text) == 0 else f"{_MD_CODE_BLOCK}{lang}\n{text}\n{_MD_CODE_BLOCK}\n"
