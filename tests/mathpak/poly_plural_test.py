# test_poly_plural.py
import pytest

from vgr.mathpak import poly_plural

@pytest.mark.parametrize(
    "x, plural, singular, expected",
    [
        # Numbers
        (None, "s", "", "s"),          # None → no len, treated as plural
        (1, "s", "", ""),              # 1 → singular
        (2, "s", "", "s"),             # 2 → plural
        (0, "s", "", "s"),             # 0 → plural

        # String lengths
        ("1", "s", "", ""),            # length 1 → singular
        ("2", "s", "", ""),            # length 1 → singular
        ("two", "s", "", "s"),         # length 3 → plural

        # Sequences
        ([], "s", "", "s"),            # len 0 → plural
        (["one"], "s", "", ""),        # len 1 → singular
        (["one", "two"], "s", "", "s"),# len 2 → plural

        # Custom plural/singular values
        (2, "es", "", "es"),
        (1, "es", "", ""),             # still singular
        (1, "mice", "mouse", "mouse"),
        (2, "mice", "mouse", "mice"),
    ]
)
def test_poly_plural(x, plural, singular, expected):
    assert poly_plural(x, plural, singular) == expected

def test_doc_examples():
    # Mirror a few composite examples from the docstring
    assert "value" + poly_plural(None) == "values"
    assert "value" + poly_plural(1) == "value"
    assert "character" + poly_plural("1") == "character"
    assert "character" + poly_plural("two") == "characters"
    assert "item" + poly_plural([]) == "items"
    assert "item" + poly_plural(["one", "two"]) == "items"
    assert "Zero" + poly_plural(2, "es") == "Zeroes"
    assert poly_plural(1, "mice", "mouse") == "mouse"
