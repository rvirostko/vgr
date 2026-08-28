import json
import os
import re
from importlib import resources as impresources

from lark import Lark

from . import images
from . import __version__

# Written to package.json
_PACKAGE = {
    "name": "vgr-syntax",
    "displayName": "VGR Syntax Highlighting",
    "description": "Syntax highlighting for the VGR DSL",
    "version": "",
    "icon": "images/icon.png",
    "publisher": "rvirostko@icloud.com",
    "author": "Ross Virostko <rvirostko@icloud.com>",
    "engines": {
        "vscode": "^1.50.0"
    },
    "contributes": {
        "languages": [
            {
                "id": "vgr",
                "aliases": ["VGR", "vgr"],
                "extensions": [".vgr", ".vstatements"],
                "configuration": "./language-configuration.json"
            }
        ],
        "grammars": [
            {
                "language": "vgr",
                "scopeName": "source.vgr",
                "path": "./syntaxes/vgr.tmLanguage.json"
            }
        ]
    }
}

# Written to language-configuration.json
_LANG_CONFIG = {
    "comments": {
        "lineComment": "#",
        "lineComment": "//",
        "blockComment": ["/*", "*/"]
    },
    "brackets": [
        ["[", "]"],
        ["(", ")"]
    ],
    "autoClosingPairs": [
        { "open": "[", "close": "]" },
        { "open": "(", "close": ")" },
        { "open": "\"", "close": "\"" },
        { "open": "'", "close": "'" },
    ],
    "surroundingPairs": [
        { "open": "[", "close": "]" },
        { "open": "(", "close": ")" },
        { "open": "\"", "close": "\"" },
        { "open": "'", "close": "'" },
        { "open": "‘", "close": "’" },
        { "open": "“", "close": "”" }
    ]
}

def _vscode_syntax_highlighting(keyword_pattern: str, constants_pattern: str, function_pattern: str):
    """
    Generate a VS Code TextMate grammar JSON for a DSL.
    - keywords: list of reserved words
    - functions: list of built-in function names
    """
    grammar = {
        "scopeName": "source.vgr",
        "name":      "VGR",
        "fileTypes": [".vgr"],
        "patterns": [
            # Keywords
            {
                "name": "keyword.control.vgr",
                "match": keyword_pattern,
            },
            # Built-in Functions
            {
                "name": "function.name.vgr",
                "match": function_pattern,
            },
            # Constants
            {
                "name": "constant.name.vgr",
                "match": constants_pattern,
            },
            # Single-line comments "#"
            {
                "name": "comment.line.number-sign.vgr",
                "begin": r"#",
                "beginCaptures": {"0": {"name": "punctuation.definition.comment.vgr"}},
                "end": r"$"
            },
            # Single-line comments "//"
            {
                "name": "comment.line.double-slash.vgr",
                "begin": r"//",
                "beginCaptures": {"0": {"name": "punctuation.definition.comment.vgr"}},
                "end": r"$"
            },
            # Multi-line comments "/* */"
            {
                "name": "comment.block.vgr",
                "begin": r"/\*",
                "beginCaptures": {"0": {"name": "punctuation.definition.comment.begin.vgr"}},
                "end": r"\*/",
                "endCaptures": {"0": {"name": "punctuation.definition.comment.end.vgr"}}
            },
            # Regular expressions
            {
                "name": "string.regexp.vgr",
                "begin": r"r/",
                "end": r"/[adimsx]*",
                "patterns": [{"name": "constant.character.escape.vgr", "match": r'\\.'}]
            },
            # Strings (single, double, triple, raw)
            {
                "name": "string.quoted.vgr",
                "patterns": [
                    # _ESC_TRIPLE_STRING:   /(""".*?(?<!\\)(\\\\)*?"""|'''.*?(?<!\\)(\\\\)*?''')/s
                    { "name": "string.quoted.triple.vgr", "begin": r'("""|\'\'\')', "end": r'\1',
                      "patterns": [{"name": "constant.character.escape.vgr", "match": r'\\.'}] },
                    # _ESC_STRING:          /("(?!"").*?(?<!\\)(\\\\)*?"|'(?!'').*?(?<!\\)(\\\\)*?')/
                    { "name": "string.quoted.vgr", "begin": r'("|\')', "end": r'\1',
                      "patterns": [{"name": "constant.character.escape.vgr", "match": r'\\.'}] },
                    #_RAW_TRIPLE_STRING:   /[Rr](""".*?"""|'''.*?''')/s
                    { "name": "string.quoted.raw.triple.vgr", "begin": r'[Rr]("""|\'\'\')', "end": r'\1' },
                    #_RAW_STRING:          /[Rr]("(?!"").*?"|'(?!'').*?')/
                    { "name": "string.quoted.raw.vgr", "begin": r'[Rr]("|\')', "end": r'\1' },
                    # _ESC_T_DQUOTE_STRING: /\u201C.*?(?<!\\)(\\\\)*?\u201D/
                    { "name": "string.quoted.typo.double.vgr", "begin": '\u201C', "end": '\u201D',
                       "patterns": [{"name": "constant.character.escape.vgr", "match": r'\\.'}] },
                    # _ESC_T_SQUOTE_STRING: /\u2018.*?(?<!\\)(\\\\)*?\u2019/
                    { "name": "string.quoted.typo.single.vgr", "begin": '\u2018', "end": '\u2019',
                       "patterns": [{"name": "constant.character.escape.vgr", "match": r'\\.'}] },
                    #_RAW_T_DQUOTE_STRING: /[Rr]\u201C.*?\u201D/
                    { "name": "string.quoted.typo.double.raw.vgr", "begin": '[Rr]\u201C', "end": '\u201D' },
                    #_RAW_T_SQUOTE_STRING: /[Rr]\u2018.*?\u2019/
                    { "name": "string.quoted.typo.single.raw.vgr", "begin": '[Rr]\u2018', "end": '\u2019' }
                ]
            }
        ],
        "repository": {},
    }
    return json.dumps(grammar, indent=4)

_CONSTS = [
    "\u2205",
    "\u221E",
    "Backslash",
    "Colon",
    "Comma",
    "Escape",
    "False",
    "Inf",
    "Nan",
    "Newline",
    "None",
    "Null",
    "Period",
    "Quote",
    "Space",
    "Tab",
    "True",
    "Zero",
]

def _constants_pattern(_parser: Lark) -> str:
    # NB: part of VSC extension
    """Returns a regex pattern that will match a constant"""
    return "(?i)" + r"\b(:?" + "|".join(sorted(_CONSTS, key=len, reverse=True)) + r")\b"

_KEYWORD_PATTERN = re.compile("[A-Z][A-Za-z-]+")
# These keep things like "foo.for" from highlighting the "for" part
_KEYWORD_START_BOUNDRY = r"(?<![.\w_])"
_KEYWORD_END_BOUNDRY = r"(?![.\w-])"

def _keyword_pattern(parser: Lark) -> str:
    """
    Returns a regex pattern that will match a keyword.
    Only includes terminals defined as literal strings, not regexes.
    """
    # NB: part of VSC extension
    keywords = []
    for t in parser.terminals:
        # Lark >= 1.0 uses t.pattern.value for literals
        value = getattr(t.pattern, "value", None)
        if value is not None and re.fullmatch(_KEYWORD_PATTERN, value):
            if value not in _CONSTS:
                keywords.append(value)
    # Pattern assures that it is a stand-alone word
    return "(?i)" + _KEYWORD_START_BOUNDRY + "(:?" + "|".join(sorted(keywords, key=len, reverse=True)) + ")" + _KEYWORD_END_BOUNDRY

def create_vscode_extension(debug: bool, parser: Lark, function_pattern: str) -> None:
    """
    Creates a directory with the required structure and files
    to be a Visual Studion Code extension.
    """
    keyword_pattern = _keyword_pattern(parser)
    constants_pattern = _constants_pattern(parser)
    if debug:
        print(f'(r"{keyword_pattern}", Keyword),')
        print(f'(r"{constants_pattern}", Name.Constant),')
        print(f'(r"{function_pattern}", Name.Function),')
    out_dir = "vgr-syntax"
    # Ensure base folder structure
    os.makedirs(out_dir, exist_ok=True)
    _PACKAGE["version"] = __version__
    with open(os.path.join(out_dir, "package.json"), "w", encoding="utf-8", errors='backslashreplace') as f:
        json.dump(_PACKAGE, f, indent=4)
    with open(os.path.join(out_dir, "language-configuration.json"), "w", encoding="utf-8", errors='backslashreplace') as f:
        json.dump(_LANG_CONFIG, f, indent=4)
    syntaxes_dir = os.path.join(out_dir, "syntaxes")
    os.makedirs(syntaxes_dir, exist_ok=True)
    grammar_json = _vscode_syntax_highlighting(keyword_pattern, constants_pattern, function_pattern)
    with open(os.path.join(syntaxes_dir, "vgr.tmLanguage.json"), "w", encoding="utf-8", errors='backslashreplace') as f:
        f.write(grammar_json)
    out_dir_images = out_dir + "/images"
    os.makedirs(out_dir_images, exist_ok=True)
    # Source - https://stackoverflow.com/a/20885799
    # Posted by ankostis, modified by community.
    # Retrieved 2026-05-20, License - CC BY-SA 4.0
    inp_file = impresources.files(images) / 'vgr-icon-128x128.png'
    with inp_file.open("rb") as f:
        image_data = f.read()
        with open(os.path.join(out_dir_images, "icon.png"), "wb") as f:
            f.write(image_data)
