from typing import Any

import pytest

from vgr.builtins import poly_slice

@pytest.mark.parametrize(
    "input_obj, start, stop, step, expected",
    [
        # None and primitives
        (None, None, None, None, None),
        (True, 2, None, None, True),
        (5, 2, None, None, 5),
        (5.1, 2, None, None, 5.1),

        # Strings
        ("", None, None, None, ""),
        ("cake", None, None, None, "cake"),
        ("cake", 2, None, None, "ke"),
        ("cake", 1, 3, None, "ak"),
        ("cake", 1, 4, 2, "ae"),

        # Lists
        ([], 2, None, None, []),
        ([1, 2, 3, 4, 5], 2, None, None, [3, 4, 5]),
        ([1, 2, 3, 4, 5], 1, 4, None, [2, 3, 4]),
        ([1, 2, 3, 4, 5], 0, 5, 2, [1, 3, 5]),
        ([10, 20, 30, 40], -2, None, None, [30, 40]),
        ([10, 20, 30, 40], -3, -1, None, [20, 30]),
        ([10, 20, 30, 40], -1, -5, -1, [40, 30, 20, 10]),

        # Dicts (slice keys)
        ({}, 2, None, None, []),
        ({"a": 1, "b": 2, "c": 3}, None, None, None, ["a", "b", "c"]),
        ({"a": 1, "b": 2, "c": 3}, 1, None, None, ["b", "c"]),
        ({"a": 1, "b": 2, "c": 3}, 0, 2, None, ["a", "b"]),
        ({"a": 1, "b": 2, "c": 3}, 0, 3, 2, ["a", "c"]),
    ]
)
def test_poly_slice(input_obj: Any, start: int, stop: int, step: int, expected: Any):
    result = poly_slice(input_obj, start, stop, step)
    assert result == expected
