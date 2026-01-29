import pytest

from vgr.mathpak import poly_type, compile_pattern

@pytest.mark.parametrize(
    "x, expected",
    [
        (None,                 "none"),
        ("hello",              "string"),
        (1,                    "int"),
        (1.0,                  "float"),
        (["hello"],            "list"),
        ({"hello":"world"},    "dictionary"),
        (compile_pattern("a"), "pattern")
        # TODO - missing "function"
    ]
)
def test_poly_type(x, expected):
    assert poly_type(x) == expected
