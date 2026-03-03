import pytest

from vgr.builtins import poly_repr

@pytest.mark.parametrize("input_obj, expected", [
    ('hello', r'"hello"'),
    ('"hello"', '\'"hello"\''),
    ('o\'hello', '\"o\'hello\"'),
    ("o\"hello", '\'o"hello\''),

])
def test_poly_repr(input_obj, expected):
    result = poly_repr(input_obj)
    assert result == expected
