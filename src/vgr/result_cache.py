from collections import OrderedDict

class ResultCacheRegistry(dict):

    def create(self, name: str, size: int) -> "ResultCache":
        cache = ResultCache(name, size)
        self[name] = cache
        return cache

    def clear(self):
        for name in tuple(self.keys()):
            cache = self.pop(name, None)
            if cache is not None: cache.clear()

    def __setitem__(self, name: str, cache):
        old = self.get(name)
        if old is not None: old.clear()
        super().__setitem__(name, cache)

class ResultCache:
    """
    Per-function LRU cache, bounded to `size` entries. Registered under
    `name` in a ResultCacheRegistry.

    Backed by OrderedDict, which preserves insertion order.
    """

    def __init__(self, name: str, size: int):
        assert name is not None
        assert size >= 1
        self.name = name
        self.size = size
        self._data = OrderedDict()

    @staticmethod
    def create_key(*args) -> tuple:
        """Build a hashable cache key tuple from positional arguments."""
        def _key_part(value):
            if type(value).__hash__ is not None: return value
            return type(value).__name__ + "::" + str(id(value))
        return tuple(_key_part(a) for a in args)

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data

    def clear(self):
        self._data.clear()

    def __getitem__(self, key: tuple):
        if key not in self._data:
            raise KeyError(key)
        self._data.move_to_end(key)
        return self._data[key]

    def __setitem__(self, key: tuple, value):
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value
        if len(self._data) > self.size:
            # evict least-recently-used which is at the top
            self._data.popitem(last=False)

    def get(self, key: tuple, default=None):
        if key not in self._data:
            return default
        self._data.move_to_end(key)
        return self._data[key]

    def set(self, key: tuple, value):
        self[key] = value
