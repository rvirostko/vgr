import pytest

from vgr.builtins.parse import (
    poly_parse_json,
    poly_parse_csv,
    poly_parse_yaml,
    poly_parse_hcl,
    poly_parse_ini,
)

@pytest.mark.parametrize(
    "content, expected",
    [
        ('{"a": 1}',            {"a": 1}),
        ('{"a": 1, "b": 2}',    {"a": 1, "b": 2}),
        ('[1, 2, 3]',           [1, 2, 3]),
        ('"hello"',             "hello"),
        ('42',                  42),
        (42,                    42),
        ('null',                None),
        ('true',                True),
        ('{"nested": {"x": 1}}', {"nested": {"x": 1}}),
        ("",                    {}),
    ]
)
def test_parse_json(content, expected):
    assert poly_parse_json(content) == expected

@pytest.mark.parametrize(
    "content",
    [
        "frog",
    ]
)
def test_parse_json_invalid(content):
    with pytest.raises(Exception):
        poly_parse_json(content)

@pytest.mark.parametrize(
    "content, expected",
    [
        (
            "a,b\n1,2\n3,4",
            [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]
        ),
        (
            "name,age\nAlice,30",
            [{"name": "Alice", "age": "30"}]
        ),
        (
            "x,y\n",
            []                                                  # header only, no data rows
        ),
        (
            'a,b\n"hello, world",2',
            [{"a": "hello, world", "b": "2"}]                  # quoted field with comma
        ),
    ]
)
def test_parse_csv(content, expected):
    assert poly_parse_csv(content) == expected

@pytest.mark.parametrize(
    "content, expected",
    [
        ("a: 1\nb: 2",          {"a": 1, "b": 2}),
        ("- 1\n- 2\n- 3",       [1, 2, 3]),
        ("key: null",           {"key": None}),
        ("{}",                  {}),
        ("a:\n  b: 1",          {"a": {"b": 1}}),
    ]
)
def test_parse_yaml(content, expected):
    assert poly_parse_yaml(content) == expected

@pytest.mark.parametrize(
    "content",
    [
        "key: [unclosed",
    ]
)
def test_parse_yaml_invalid(content):
    with pytest.raises(Exception):
        poly_parse_yaml(content)

@pytest.mark.parametrize(
    "content, expected",
    [
        (
            "[section]\nkey=value",
            {"section": {"key": "value"}}
        ),
        (
            "[s1]\na=1\n[s2]\nb=2",
            {"s1": {"a": "1"}, "s2": {"b": "2"}}
        ),
        (
            "[section]\nkey = value with spaces",
            {"section": {"key": "value with spaces"}}
        ),
        (
            "",
            {}                                                  # no sections
        ),
    ]
)
def test_parse_ini(content, expected):
    assert poly_parse_ini(content) == expected

@pytest.mark.parametrize(
    "content, expected",
    [
        (
            'key = "value"',
            {"key": "value"}
        ),
        (
            'a = 1\nb = 2',
            {"a": 1, "b": 2}
        ),
        (
            'block "label" {\n  key = "val"\n}',
            {"block": [{"label": {"key": "val"}}]}
        ),
    ]
)
def test_parse_hcl(content, expected):
    assert poly_parse_hcl(content) == expected

@pytest.mark.parametrize(
    "content",
    [
        "not = [unclosed",
    ]
)
def test_parse_hcl_invalid(content):
    with pytest.raises(Exception):
        poly_parse_hcl(content)
