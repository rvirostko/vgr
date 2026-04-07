from typing import Any

import pytest

from vgr.builtins import strip_nulls

@pytest.mark.parametrize("input_obj, expected", [
    # None and scalars (pass-through)
    (None, None),
    (42, 42),
    ("hello", "hello"),
    (False, False),
    (3.14, 3.14),

    # Flat list
    ([1, None, 2, None, 3], [1, 2, 3]),

    # Flat dict
    ({"a": 1, "b": None, "c": 2}, {"a": 1, "c": 2}),

    # Nested dict
    (
        {"a": None, "b": {"c": None, "d": 4}},
        {"b": {"d": 4}}
    ),

    # Nested list
    (
        [1, None, [2, None, 3], None],
        [1, [2, 3]]
    ),

    # Mixed nested structures
    (
        {
            "x": [None, {"y": None, "z": 5}, None],
            "w": None
        },
        {
            "x": [{"z": 5}]
        }
    ),

    # Empty structures remain empty
    ({}, {}),
    ([], []),

    # Dict with list containing only None
    (
        {"a": [None, None], "b": 1},
        {"a": [], "b": 1}
    ),

    # List with dicts containing None
    (
        [{"a": None}, {"b": 2}, None],
        [{}, {"b": 2}]
    ),
])
def test_strip_nulls(input_obj: Any, expected: Any):
    assert strip_nulls(input_obj) == expected
