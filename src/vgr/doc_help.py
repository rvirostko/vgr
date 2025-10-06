"""
The help system
"""

from typing import Callable
import re

from lark import Lark
from pygments.lexer import RegexLexer
from pygments.style import Style
from pygments.styles import STYLE_MAP
from pygments.token import (
    Comment,
    Error,
    Escape,
    Generic,
    Keyword,
    Literal,
    Name,
    Number,
    Operator,
    Other,
    Punctuation,
    String,
    Text,
    Token,
    Whitespace,
)
from rapidfuzz import fuzz
from rich.console import Console, Theme
from rich.markdown import Markdown
from rich.syntax import Syntax

_CODE_BG = "#f8f8f8"
_ON_BG = "on " + _CODE_BG

_BASE_THEME = Theme({}, inherit=True)

_THEME = Theme({
    "markdown.text": "",  # Default terminal style
    # NB: Headings are all centered and look horrible: don't use
    #     until Markdown is fixed
    #     Also, __ul__ renders as bold
    # Foreground colors: standard names, 256-color, and hex
	# Background colors: on color
	# Text styles: bold, italic, underline, reverse, blink, dim, strike
    #"markdown.h1": "bold underline",
    #"markdown.h2": "bold",
    #"markdown.h3": "bold",
    #"markdown.h4": "bold",
    #"markdown.h5": "bold",
    #"markdown.h6": "bold",
    #"markdown.list": "",
    #"markdown.item": "",
    "markdown.block_quote": "",
    #"markdown.bold": "bold",
    #"markdown.italic": "italic",
    "markdown.code": str(_BASE_THEME.styles["markdown.item.bullet"]),
    "markdown.hr": "bold",
    "markdown.link": "underline",
    "markdown.image": "underline",
}, inherit=True)

_VGR_CODE_BLOCK_PATTERN = re.compile(r"```vgr\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

# Pull out weights etc for better tuning
_FULL_SCORE_WEIGHT = 1.5
_WEAK_SCORE_RATIO = 0.7

_KEYWORD_PATTERN = re.compile("[A-Z][A-Za-z]+")

def keyword_pattern(parser: Lark) -> str:
    """
    Returns a regex pattern that will match a keyword.
    Only includes terminals defined as literal strings, not regexes.
    """
    keywords = []
    for t in parser.terminals:
        # Lark >=1.0 uses t.pattern.value for literals
        value = getattr(t.pattern, "value", None)
        if value is not None and re.fullmatch(_KEYWORD_PATTERN, value):
            if not value.isupper() or value in ["CSV", "JSON"]: keywords.append(value)
    # Pattern assures that it is a stand-alone word
    return r"(?i)\b(" + "|".join(sorted(keywords, key=len, reverse=True)) + r")\b"

def search_entries(entries: dict, query: str="", limit: int = 10) -> list[tuple[str, Callable]]:
    """
    Search using some fuzzy logic. entries should be in the form of:

        key: Canonical name, value: (implementing function, name normalized, documentation normalized)

    """
    if not entries: return []
    q = query.strip().replace('_', '').casefold().removesuffix("()").removesuffix("(")
    tokens = q.split()
    scores = {}
    for name, (_, name_norm, doc_norm) in entries.items():
        # 1. Match against full query
        query_score = max(fuzz.QRatio(q, name_norm), fuzz.QRatio(q, doc_norm))
        # 2. Match individual tokens
        token_score = sum(max(fuzz.partial_ratio(tok, name_norm), fuzz.partial_ratio(tok, doc_norm)) for tok in tokens)
        # 3. Composite score: prioritize full match, reward partial token matches
        scores[name] = query_score * _FULL_SCORE_WEIGHT + token_score
    # Only include matches above threshold, sorted by score descending
    threshold = max(scores.values()) * _WEAK_SCORE_RATIO
    filtered_matches = [
        (name, score) for name, score in scores.items() if score >= threshold
    ]
    # Sort by descending score
    filtered_matches.sort(key=lambda x: -x[1])
    # If the query is an "exact" match, return only that entry
    top_name = filtered_matches[0][0] if filtered_matches else None
    if top_name and top_name.casefold().replace('_', '').replace(' ', '') == q:
        return [(top_name, entries[top_name][0])]
    # Otherwise, convert the filtered matches into an array and return
    # references that are unique by function
    return unique_by_func([(name, entries[name][0]) for name, _score in filtered_matches], limit)

def unique_by_func(entries: list, limit: int=None) -> list:
    funcs = set()
    rc = []
    for name, func in entries:
        if func not in funcs:
            rc.append((name, func))
            funcs.add(func)
            if limit and len(rc) >= limit: break
    return rc

_NBSP = "\u00A0"
_REPLACER = re.compile(r"[.]{3}|[ \t]*<br>[ \t]*\n|<sp>|<en>|<em>", re.IGNORECASE)
_EN = _NBSP * 2
_EM = _NBSP * 4
_ELLIPSIS = "…"

def _text_replace(match):
    tag = match.group(0).lower()
    if tag == "...": return _ELLIPSIS
    if tag == "<sp>": return _NBSP
    if tag == "<en>": return _EN
    if tag == "<em>": return _EM
    return '  \n'

def print_md(s: str) -> None:
    if s: _print(Console(theme=_THEME), s)

def print_doc(func: Callable) -> None:
    doc = (func.__doc__ or "").strip()
    console = Console(theme=_THEME)
    console.print("")
    if doc:
        _print(console, doc)
    else:
        console.print(Markdown('_Sorry, no documentation available_'))
    console.print("")

def _print(console: Console, s: str) -> None:
    s = _REPLACER.sub(_text_replace, s)
    last_pos = 0
    for match in _VGR_CODE_BLOCK_PATTERN.finditer(s):
        start, end = match.span()
        if start > last_pos: console.print(Markdown(s[last_pos:start]))
        _print_code_block(console, match.group(1))
        last_pos = end
    # Add remaining text
    if last_pos < len(s): console.print(Markdown(s[last_pos:]))

def _print_code_block(console: Console, code_block: str) -> None:
    console.print("")  # outside blank line above
    console.print(Syntax(
        code=code_block.strip('\n'),
        lexer=VgrLexer(),
        theme=VGRCodeStyle,
        line_numbers=False,
        padding=(1,2),
        background_color=_CODE_BG,
        tab_size=4,
        dedent=True
    ))
    console.print("")  # outside blank line below

# Initially based on "default" style
class VGRCodeStyle(Style):
    background_color = _CODE_BG

    styles = {
        Text: "",
        Token: "",
        Escape: "",
        Literal: "",
        Other: "",
        Punctuation: "",
        Operator: "",

        Whitespace:                "#bbbbbb",
        Comment:                   "italic " + "#0a5301",
        Comment.Preproc:           "",

        Keyword:                   "bold " + "#6b0041",
        Keyword.Pseudo:            "nobold",
        Keyword.Type:              "nobold",

        Operator:                  "",
        Operator.Word:             "bold",

        Name.Builtin:              "",
        Name.Function:             "",
        Name.Class:                "bold",
        Name.Namespace:            "bold",
        Name.Exception:            "bold",
        Name.Variable:             "",
        Name.Constant:             "",
        Name.Label:                "",
        Name.Entity:               "bold",
        Name.Attribute:            "",
        Name.Tag:                  "",
        Name.Decorator:            "bold italic " + "#ff8051",

        String:                    "#2D0BF2",
        String.Doc:                "italic",
        String.Interpol:           "bold",
        String.Escape:             "bold " + "#000000",
        String.Regex:              "#2D0BF2",
        String.Symbol:             "#2D0BF2",
        String.Other:              "#2D0BF2",
        Number:                    "",

        Generic.Heading:           "bold",
        Generic.Subheading:        "bold",
        Generic.Deleted:           "",
        Generic.Inserted:          "",
        Generic.Error:             "",
        Generic.Emph:              "italic",
        Generic.Strong:            "bold",
        Generic.EmphStrong:        "bold italic",
        Generic.Prompt:            "bold",
        Generic.Output:            "",
        Generic.Traceback:         "",

        Error:                     "border:#FF0000"
    }

STYLE_MAP["vgr"] = f"{VGRCodeStyle.__module__}.{VGRCodeStyle.__qualname__}"

class VgrLexer(RegexLexer):
    name = "vgr"
    aliases = ["vgr"]
    tokens = {
        # This is NOT a full highlighter: we'll only support our uppercase keywords
        # and limited syntax elements
        "root": [
            # Comments
            (r"--.*?$", Comment.Single),   # em-dash style
            (r"//.*?$", Comment.Single),   # double-slash
            (r"#.*?$", Comment.Single),    # hash style
            (r"/\*.*?\*/", Comment.Multiline),

            (r" → ", Name.Decorator), # This is used with functional output examples

            (r'\\(x[0-9A-Fa-f]{2}|u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8}|N\{[^}]+\}|.)', String.Escape),

            # Single-quoted or double-quoted strings
            (r'[Rr]?("(?!"").*?(?<!\\)(\\\\)*?"|\'(?!\'\').*?(?<!\\)(\\\\)*?\')', String),
            # Triple-quoted strings (long strings, can be multi-line)
            (r'[Rr]?("""(.*?)(?<!\\)(\\\\)*?"""|\'\'\'(.*?)(?<!\\)(\\\\)*?\'\'\')', String),

            (r"(?i)(?:(?<=^)|(?<=\s)|(?<=[^\w.-]))(Append|Prepend|Remove|Replace|Insert|At|Corresponding|Corr|If|Else|End-If|Exhibit|Add|Subtract|Giving|Multiply|Divide|Into|From|Compute|Equal|End-Compute|Display|Up|Down|Repeat|Perform|End-Perform|From|By|Until|Varying|For|Next|ForEach|Contains|Is|In|Not|Greater|Less|Than|Any|All|For|Next|Move|Evaluate|Sort|On|Key|File|Asc|Des|Unique|Printf|End|Otherwise|Assert|True|False|None|Choose|Print|Using|When|Matches|Set|To)(?:(?=$)|(?=\s)|(?=[^\w(]))", Keyword),
        ]
    }
