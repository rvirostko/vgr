
import json
import re
import os

from lark import Lark

# package.json
_PACKAGE = {
    "name": "vgr-syntax",
    "displayName": "VGR Syntax Highlighting",
    "description": "Syntax highlighting for the VGR DSL",
    "version": "0.0.1",
    "publisher": "localdev",
    "engines": {
        "vscode": "^1.50.0"
    },
    "contributes": {
        "languages": [
            {
                "id": "vgr",
                "aliases": ["VGR", "vgr"],
                "extensions": [".vgr"],
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

# language-configuration.json
_LANG_CONFIG = {
    "comments": {
        "lineComment": "#",
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
        { "open": "'", "close": "'" }
    ]
}

def _extract_keywords(parser: Lark):
    """
    Return a list of all literal keywords defined in the parser's terminals.
    Only includes terminals defined as literal strings, not regexes.
    """
    keywords = []
    for t in parser.terminals:
        # Lark >=1.0 uses t.pattern.value for literals
        value = getattr(t.pattern, "value", None)
        if value is not None and re.fullmatch(r"[A-Za-z0-9_]+", value):
            keywords.append(value)
    return keywords

def _vscode_syntax_highlighting(keywords, functions):
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
                "match": r"(?i)\b(" + "|".join(map(re.escape, keywords)) + r")\b"
            },
            # Functions (only highlight listed functions)
            {
                "name": "entity.name.function.vgr",
                "match": r"(?i)\b(" + "|".join(map(re.escape, functions)) + r")(?=\s*\()"
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
            # Single-line comments "--"
            {
                "name": "comment.line.double-dash.vgr",
                "begin": r"--",
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
            # Strings (single, double, triple, raw)
            {
                "name": "string.quoted.vgr",
                "patterns": [
                    # Triple quotes
                    {
                        "name": "string.quoted.triple.double.vgr",
                        "begin": r'"""',
                        "end": r'"""',
                        "patterns": [{"name": "constant.character.escape.vgr", "match": r'\\.'}]
                    },
                    # Raw strings
                    {
                        "name": "string.quoted.raw.double.vgr",
                        "begin": r'r"',
                        "end": r'"'
                    },
                    {
                        "name": "string.quoted.raw.single.vgr",
                        "begin": r"r'",
                        "end": r"'"
                    },
                    # Standard strings
                    {
                        "name": "string.quoted.double.vgr",
                        "begin": r'"',
                        "end": r'"',
                        "patterns": [{"name": "constant.character.escape.vgr", "match": r'\\.'}]
                    },
                    {
                        "name": "string.quoted.single.vgr",
                        "begin": r"'",
                        "end": r"'",
                        "patterns": [{"name": "constant.character.escape.vgr", "match": r'\\.'}]
                    }
                ]
            }
        ],
        "repository": {},
    }
    return json.dumps(grammar, indent=4)

def create_vscode_extension(parser: Lark, functions):
    out_dir = "vgr-syntax"
    # Ensure base folder structure
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "package.json"), "w", encoding="utf-8") as f:
        json.dump(_PACKAGE, f, indent=4)
    with open(os.path.join(out_dir, "language-configuration.json"), "w", encoding="utf-8") as f:
        json.dump(_LANG_CONFIG, f, indent=4)
    syntaxes_dir = os.path.join(out_dir, "syntaxes")
    os.makedirs(syntaxes_dir, exist_ok=True)
    grammar_json = _vscode_syntax_highlighting(_extract_keywords(parser), functions)
    with open(os.path.join(syntaxes_dir, "vgr.tmLanguage.json"), "w", encoding="utf-8") as f:
        f.write(grammar_json)
