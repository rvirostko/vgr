import pytest

from vgr.stmt_exec import ConstantsNormalizer

@pytest.mark.parametrize("input_text, expected", [
    # --- Properly quoted strings ---
    ('"hello"', "hello"),
    ("'world'", "world"),

    # --- Valid escape sequences ---
    ('"line1\\nline2"', "line1\nline2"),
    ('"tab\\tend"', "tab\tend"),
    ('"quote: \\" "', 'quote: " '),

    # --- Invalid escape sequences (should survive as literal) ---
    ('"bad\\qescape"', "bad\\qescape"),
    ('"mix\\nvalid\\ybad"', "mix\nvalid\\ybad"),

    # --- Mixed escapes and fallback logic ---
    (r'"c:\\path\\file"', r"c:\path\file"),        # both \p and \f are fine
    (r'"c:\path\file"', "c:\\path\file"),          # invalid \p "fixed"
    ('"c:\\xfile"', "c:\\xfile"),                  # invalid \x<nn> "fixed"
    (r'"a\\b\qc"', r"a\b\qc"),                     # invalid \q "fixed"

    # --- Unicode-like escapes ---
    ('"ok\\u0041"', "okA"),
    ('"bad\\u00Z9"', "bad\\u00Z9"),                # invalid unicode

])
def test_tolerant_literal_eval(input_text, expected):
    result = ConstantsNormalizer.tolerant_literal_eval(input_text)
    assert result == expected


def test_returns_str_on_total_failure():
    # Non-evaluable nonsense should return the same input
    bad_input = '"""broken\\'
    assert ConstantsNormalizer.tolerant_literal_eval(bad_input) == bad_input


def test_preserves_backslashes_for_invalid_sequences():
    # Ensure \q becomes \\q, not removed or collapsed
    s = '"test\\qmore"'
    assert ConstantsNormalizer.tolerant_literal_eval(s) == "test\\qmore"

@pytest.mark.parametrize(
    "input_str, expected",
    [
        # Already clean quotes
        ('"hello"', '"hello"'),
        ("'world'", "'world'"),

        # Raw string prefix
        ('R"hello"', 'R"hello"'),
        ("r'world'", "r'world'"),

        # Typographic single quotes
        ('\u2018hello\u2019', "'hello'"),
        ('r\u2018world\u2019', "r'world'"),
        ('R\u2018raw\u2019', "R'raw'"),

        # Typographic double quotes
        ('\u201chello\u201d', '"hello"'),
        ('r\u201cworld\u201d', 'r"world"'),
        ('R\u201craw\u201d', 'R"raw"'),

        # Already normal quotes with prefix
        ('r"hello"', 'r"hello"'),

        # Edge: single typographic quotes (incomplete)
        ('\u2018', '\u2018'),
        ('\u201c', '\u201c'),

        # Edge: mismatched quotes (should leave as-is)
        ('\u2018hello\u201d', '\u2018hello\u201d'),
        ('r\u201cworld\u2019', 'r\u201cworld\u2019'),
    ]
)
def test_normalize_outer_quotes(input_str, expected):
    assert ConstantsNormalizer.normalize_outer_quotes(input_str) == expected
