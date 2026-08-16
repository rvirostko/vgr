import pytest

from vgr.builtins.list import poly_combine_lists

@pytest.mark.parametrize(
    "inputs, expected",
    [
        ( (None,), [[None]] ),
        ( ([], []), [] ),
        ( ([], [1, 2]), [[None, 1], [None, 2]] ),
        ( ([1, 2], [3, 4]), [[1, 3], [2, 4]] ),
        ( ([1], [10, 20, 30]), [[1, 10], [None, 20], [None, 30]] ),
        ( ([1, 2], ["a", "b"], [True, False]), [[1, "a", True], [2, "b", False]] ),
        ( (5, 10), [[5, 10]] ),
        ( (1, [2, 3]), [[1, 2], [None, 3]] ),
        ( ([None], [1, 2]), [[None, 1], [None, 2]] ),
        ( ([1, 2, 3],), [[1], [2], [3]] ),
    ]
)
def test_poly_combine_lists(inputs, expected):
    result = poly_combine_lists(*inputs)
    assert result == expected
