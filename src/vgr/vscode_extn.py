import json
import os
import re
from importlib import resources as impresources

from lark import Lark

from . import images
from . import js
from . import __version__
from .functions import (
    get_builtin_function_names,
    get_function_doc,
    get_function
)
from .operators import (
    get_operator_entries,
)
from .stmt_exec import get_statement_op

# Written to package.json
_PACKAGE = {
    "name":        "vgr-syntax",
    "displayName": "VGR Language Highlighting and Autocomplete",
    "description": "Syntax highlighting and completion for the VGR scripting language",
    "version":     "", # set dynamically
    "icon":        "images/icon.png",
    "publisher":   "rvirostko@icloud.com",
    "author":      "Ross Virostko <rvirostko@icloud.com>",
    "engines":     { "vscode": "^1.60.0" },
    "main":        "./extension.js",
    "activationEvents": ["onLanguage:vgr"],
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
        ],
        "views": {
            "explorer": [{ "id": "vgrReference", "name": "VGR Reference" }]
        },
        "configurationDefaults": {
            "[vgr]": { "editor.wordBasedSuggestions": "currentDocument" }
        },
        "commands": [
            { "command": "vgr.runFile",   "category": "VGR", "title": "Run Script", "icon": "$(play)" },
            { "command": "vgr.startRepl", "category": "VGR", "title": "Open REPL",  "icon": "$(terminal)" }
        ],
        "menus": {
            "editor/title/run": [
                {
                    "command": "vgr.runFile",
                    "when": "editorLangId == vgr",
                    "group": "navigation@0"
                }
            ]
        }
    }
}

# Written to language-configuration.json
_LANG_CONFIG = {
    "comments": {
        "lineComment":  "#",
        "lineComment":  "//",
        "blockComment": ["/*", "*/"]
    },
    "brackets": [
        ["{", "}"],
        ["[", "]"],
        ["［", "］"], # fullwidth variant
        ["(", ")"]
    ],
    "autoClosingPairs": [
        { "open": "[", "close": "]" },
        { "open": "［", "close": "］" },# fullwidth variant
        { "open": "(", "close": ")" },
        { "open": '"', "close": '"' },
        { "open": "'", "close": "'" },
    ],
    "surroundingPairs": [
        { "open": "{", "close": "}" },
        { "open": "[", "close": "]" },
        { "open": "［", "close": "］" },# fullwidth variant
        { "open": "(", "close": ")" },
        { "open": '"', "close": '"' },
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

    Written to vgr.tmLanguage.json
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

_KEYWORD_PATTERN = re.compile("(?i)[@A-Z][A-Z-]+")
# These keep things like "foo.for" from highlighting the "for" part
_KEYWORD_START_BOUNDARY = r"(?<![.\w_])"
_KEYWORD_END_BOUNDARY = r"(?![.\(\[［\w-])"

def _keyword_pattern(parser: Lark) -> str:
    """
    Returns a regex pattern that will match a keyword.
    Only includes terminals defined as literal strings, not regexes.
    """
    keywords = _keyword_list(parser)
    # Pattern assures that it is a stand-alone word
    return "(?i)" + _KEYWORD_START_BOUNDARY + "(:?" + "|".join(sorted(keywords, key=len, reverse=True)) + ")" + _KEYWORD_END_BOUNDARY

def _keyword_list(parser: Lark) -> list[str]:
    keywords = []
    for t in parser.terminals:
        # Lark >= 1.0 uses t.pattern.value for literals
        value = getattr(t.pattern, "value", None)
        if value is not None and re.fullmatch(_KEYWORD_PATTERN, value):
            if value not in _CONSTS:
                keywords.append(value)
    return sorted(keywords)

def _keywords(parser: Lark) -> list[dict]:
    keywords = []
    for name in _keyword_list(parser):
        statement = get_statement_op(name)
        if statement is None:
            if name.find('-') != -1:
                statement = get_statement_op(n := name.replace('-', ' '))
                if statement is not None: name = n
        entry = {
            "name":          name,
            #"insertText":    None, defaults to name
            #"detail":        None, not sure how to use this...
        }
        if doc := get_function_doc(statement):
            entry["documentation"] = doc
        keywords.append(entry)
    return keywords

def _functions_pattern() -> str:
    """
    Return a regex string that will match built-in
    function names.
    """
    functions = sorted(get_builtin_function_names(), key=len, reverse=True)
    return r"(?i)\b(?:" + "|".join(functions) + r")(?=\s*\()"

def _functions() -> list[dict]:
    functions = []
    for name in sorted(get_builtin_function_names()):
        func = get_function(name)[1]
        entry = {
            "name":          name,
            #"insertText":    None, defaults to name, need a way to specify on the function
            #"detail":        None, # This should be in the form of a function signiture
        }
        if doc := get_function_doc(func):
            entry["documentation"] = doc
        functions.append(entry)
    return functions

def _operators() -> list[dict]:
    operators = []
    entries = get_operator_entries()
    for name in sorted(entries.keys()):
        entry = {
            "name":          name,
            #"insertText":    None, defaults to name, need a way to specify on the function
            #"detail":        None, # NA here
        }
        func = entries.get(name)[0]
        if doc := get_function_doc(func):
            entry["documentation"] = doc
        operators.append(entry)
    return operators

def _bin_copy(file_in: str, out_file: str) -> None:
    # Source - https://stackoverflow.com/a/20885799
    # Posted by ankostis, modified by community.
    # Retrieved 2026-05-20, License - CC BY-SA 4.0
    with file_in.open("rb") as f:
        data = f.read()
        with open(out_file, "wb") as f:
            f.write(data)

def create_vscode_extension(debug: bool, parser: Lark) -> None:
    """
    Creates a directory with the required structure and files
    to be a Visual Studio Code extension.
    """
    keywords_pattern = _keyword_pattern(parser)
    constants_pattern = _constants_pattern(parser)
    functions_pattern = _functions_pattern()
    if debug:
        print(f'(r"{keywords_pattern}", Keyword),')
        print(f'(r"{constants_pattern}", Name.Constant),')
        print(f'(r"{functions_pattern}", Name.Function),')
    out_dir = "vgr-syntax"
    # Ensure base folder structure
    os.makedirs(out_dir, exist_ok=True)
    _PACKAGE["version"] = __version__
    with open(os.path.join(out_dir, "package.json"), "w", encoding="utf-8", errors='backslashreplace') as f:
        json.dump(_PACKAGE, f, indent=2)
    with open(os.path.join(out_dir, "language-configuration.json"), "w", encoding="utf-8", errors='backslashreplace') as f:
        json.dump(_LANG_CONFIG, f, indent=2)
    _bin_copy(impresources.files(js) / 'extension.js', os.path.join(out_dir, "extension.js"))
    with open(os.path.join(out_dir, "keywords.json"), "w", encoding="utf-8", errors='backslashreplace') as f:
        json.dump(_keywords(parser), f, indent=2)
    with open(os.path.join(out_dir, "functions.json"), "w", encoding="utf-8", errors='backslashreplace') as f:
        json.dump(_functions(), f, indent=2)
    with open(os.path.join(out_dir, "operators.json"), "w", encoding="utf-8", errors='backslashreplace') as f:
        json.dump(_operators(), f, indent=2)
    syntaxes_dir = os.path.join(out_dir, "syntaxes")
    os.makedirs(syntaxes_dir, exist_ok=True)
    grammar_json = _vscode_syntax_highlighting(keywords_pattern, constants_pattern, functions_pattern)
    with open(os.path.join(syntaxes_dir, "vgr.tmLanguage.json"), "w", encoding="utf-8", errors='backslashreplace') as f:
        f.write(grammar_json)
    out_dir_images = out_dir + "/images"
    os.makedirs(out_dir_images, exist_ok=True)
    _bin_copy(impresources.files(images) / 'vgr-icon-128x128.png', os.path.join(out_dir_images, "icon.png"))
