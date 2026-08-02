from collections import OrderedDict

from typing import Any
from threading import RLock

class ResultCache:
    """A cached set of results"""

    def __init__(self, key: str, size: int):
        """key: identifier for the cache, size: max number of entries possible"""
        assert key is not None
        assert size >= 1
        self._key = key
        self._size = size
        self._data = OrderedDict()
        self._lock = RLock()
        self._requests = 0
        self._hits = 0

    @staticmethod
    def create_key(*args) -> tuple:
        """Build a hashable key for cache entries"""
        def _key_for(value):
            if type(value).__hash__ is not None: return value
            return type(value).__name__ + "::" + str(id(value))
        return tuple(_key_for(a) for a in args)

    def __str__(self) -> str:
        return f"{self.key} - {self.size}, {len(self)}, {self.hit_percentage:.1f}%"

    def __len__(self) -> int:
        return len(self._data)

    def keys(self) -> list:
        return list(self._data.keys())

    def clear(self) -> None:
        """Clears data and statistics"""
        self._data.clear()
        self._requests = 0
        self._hits = 0

    @property
    def key(self) -> str: return self._key

    @property
    def size(self) -> int: return self._size

    @property
    def requests(self) -> int: return self._requests

    @property
    def hits(self) -> int: return self._hits

    @property
    def hit_percentage(self) -> float:
        return 0 if self.requests == 0 else 100 if self.hits == self.requests else (self.hits / self.requests) * 100

    @property
    def info(self) -> dict:
        return {
            "key":            self.key,
            "size":           self.size,
            "requests":       self.requests,
            "hits":           self.hits,
            "hit_percentage": self.hit_percentage
        }

    def fetch(self, key: tuple) -> tuple:
        """Get an existing value from the cache

Returns tuple: [0]-bool, found or not, [1]-the requested key, [2]-cached value"""
        with self._lock:
            self._requests += 1
            if key in self._data:
                self._hits += 1
                self._data.move_to_end(key)
                return (True, key, self._data[key])
            return (False, key, None)

    def store(self, key: tuple, value: Any) -> None:
        """Adds a ***NEW*** entry to the cache"""
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
            else:
                # evict least-recently-used which is at the top
                if len(self._data) >= self._size:
                    self._data.popitem(last=False)
                self._data[key] = value

class ResultCacheRegistry():
    """Manages a set of caches"""

    def __init__(self):
        self._caches = dict()

    def create(self, key: str, size: int) -> ResultCache:
        """key: identifier for the cache, size: max number of entries possible"""
        # If one existed, we clear it out
        self._dispose(key)
        # If not a valid size, then we don't create an instance
        return None if size is None or size < 1 else self._add(key, ResultCache(key, size))

    def clear(self):
        """Disposes of all caches"""
        for key in self.keys(): self._dispose(key)

    def _dispose(self, key: str) -> None:
        cache = self._caches.pop(key, None)
        if cache is not None: cache.clear()

    def _add(self, key: str, cache: ResultCache) -> ResultCache:
        self._caches[key] = cache
        return cache

    def __getitem__(self, key: str) -> ResultCache:
        return self._caches[key]

    def __contains__(self, key: str) -> bool:
        return key in self._caches

    def __len__(self) -> int:
        return len(self._caches)

    def keys(self) -> list:
        return list(self._caches.keys())
