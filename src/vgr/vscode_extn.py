
import json
import os

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
        { "open": "'", "close": "'" }
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

from . import __version__

def create_vscode_extension(keyword_pattern: str, constants_pattern: str, function_pattern: str) -> None:
    """
    Creates a directory with the required structure and files
    to be a Visual Studion Code extension.
    """
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
    # This gets complicated...
    # See the extension loading code etc: a better solutions is needed
#    shutil.copy("images/vgr-icon-128x128.png", out_dir_images + "/icon.png")
