import pytest

from unittest.mock import patch

from vgr.result_cache import ResultCacheRegistry, ResultCache

CACHE_SIZE = 8

@pytest.fixture
def registry():
    return ResultCacheRegistry()

def test_create_adds_new_entry(registry):
    cache = registry.create("alpha", CACHE_SIZE)
    assert "alpha" in registry
    assert registry["alpha"] is cache
    assert isinstance(cache, ResultCache)
    assert cache.name == "alpha"
    assert cache.size == CACHE_SIZE

def test_create_multiple_distinct_names(registry):
    alpha = registry.create("alpha", CACHE_SIZE)
    beta = registry.create("beta", CACHE_SIZE)
    assert set(registry.keys()) == {"alpha", "beta"}
    assert registry["alpha"] is alpha
    assert registry["beta"] is beta

def test_create_with_existing_name_overwrites(registry):
    first = registry.create("gamma", CACHE_SIZE)
    second = registry.create("gamma", CACHE_SIZE)
    assert registry["gamma"] is second
    assert registry["gamma"] is not first
    assert len(registry) == 1

def test_overwrite_clears_the_old_cache_instance(registry):
    first = registry.create("delta", CACHE_SIZE)
    with patch.object(first, "clear") as mock_clear:
        registry.create("delta", CACHE_SIZE)
        mock_clear.assert_called_once()

def test_direct_setitem_overwrite_clears_old_cache(registry):
    first = registry.create("epsilon", CACHE_SIZE)
    replacement = ResultCache("epsilon", CACHE_SIZE)
    with patch.object(first, "clear") as mock_clear:
        registry["epsilon"] = replacement
        mock_clear.assert_called_once()
    assert registry["epsilon"] is replacement

def test_setitem_on_new_name_does_not_call_clear(registry):
    new_cache = ResultCache("zeta", CACHE_SIZE)
    with patch.object(new_cache, "clear") as mock_clear:
        registry["zeta"] = new_cache
        mock_clear.assert_not_called()

def test_clear_removes_all_entries(registry):
    registry.create("eta", CACHE_SIZE)
    registry.create("theta", CACHE_SIZE)
    registry.create("iota", CACHE_SIZE)
    registry.clear()
    assert len(registry) == 0
    assert list(registry.keys()) == []

def test_clear_calls_clear_on_every_registered_cache(registry):
    caches = [registry.create(name, CACHE_SIZE) for name in ("kappa", "lambda", "mu")]
    with patch.object(ResultCache, "clear", autospec=True) as mock_clear:
        registry.clear()
    called_on = [c.args[0] for c in mock_clear.call_args_list]
    assert set(called_on) == set(caches)

def test_clear_on_empty_registry_is_a_no_op(registry):
    registry.clear()  # should not raise
    assert len(registry) == 0

class _Unhashable:
    """Simple stand-in for a non-hashable object (dict/list/set are also
    fine, but a dedicated class keeps class-name assertions readable)."""
    __hash__ = None


@pytest.mark.parametrize(
    "args",
    [
        (),
        (1,),
        ("a", "b"),
        (1, 2, 3),
        (None,),
        (True, False),
        ("mixed", 1, None, True),
    ],
)
def test_create_key_returns_tuple_of_same_length_for_hashable_args(args):
    key = ResultCache.create_key(*args)
    assert isinstance(key, tuple)
    assert len(key) == len(args)

@pytest.mark.parametrize(
    "args, expected",
    [
        ((), ()),
        ((1,), (1,)),
        (("x", "y"), ("x", "y")),
        ((1, "x", None), (1, "x", None)),
        ((True, False), (True, False)),
    ],
)
def test_create_key_passes_hashable_values_through_unchanged(args, expected):
    assert ResultCache.create_key(*args) == expected

def test_create_key_replaces_single_unhashable_arg():
    obj = _Unhashable()
    key = ResultCache.create_key(obj)
    assert key == (f"_Unhashable::{id(obj)}",)

def test_create_key_replaces_unhashable_args_among_hashable_ones():
    obj = _Unhashable()
    key = ResultCache.create_key("first", obj, 3)
    assert key == ("first", f"_Unhashable::{id(obj)}", 3)

@pytest.mark.parametrize(
    "unhashable",
    [
        [1, 2, 3],
        {"a": 1},
        {1, 2, 3},
        _Unhashable(),
    ],
)
def test_create_key_stringifies_various_unhashable_types(unhashable):
    key = ResultCache.create_key(unhashable)
    expected = type(unhashable).__name__ + "::" + str(id(unhashable))
    assert key == (expected,)

def test_create_key_two_different_unhashable_objects_produce_different_keys():
    obj_a = _Unhashable()
    obj_b = _Unhashable()
    key_a = ResultCache.create_key(obj_a)
    key_b = ResultCache.create_key(obj_b)
    assert key_a != key_b

def test_create_key_result_is_usable_as_a_dict_key():
    d = {}
    key = ResultCache.create_key("user", 42, None)
    d[key] = "cached result"
    assert d[key] == "cached result"
    assert d[ResultCache.create_key("user", 42, None)] == "cached result"
    assert len(d) == 1  # equal keys collapse to one entry, as expected of a dict
