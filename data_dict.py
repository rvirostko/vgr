"""
The DataDictionary holds hierarchical data used by the application.
Most of the space is avaialble for the user's application, but parts--typically constants--
are immutable.
"""

from typing import (
    Any,
    Dict,
    Iterator,
    KeysView,
    Optional,
)
import copy

_SCRATCH_PREFIX = '_'

class DataDictionary():
    """
    A hierachical data store
    """

    # These can't appear in a path name (to prevent confusion)
    _RESERVED_WORDS = ('true', 'false', 'none', 'null')

    def __init__(self):
        # Populate the stack of frames with our "global" frame
        self._frames: list[Frame] = [Frame()]
        self._immutable_prefixes: tuple = tuple()
        self._protected_prefixes: tuple = tuple()
        self.add_protected_prefix(_SCRATCH_PREFIX)

    def add_immutable_prefix(self, prefix: str) -> None:
        """Immutable prefixes means you can't change any part of them"""
        self._assert_valid_prefix(prefix)
        self._immutable_prefixes += (prefix, )

    def add_protected_prefix(self, prefix: str) -> None:
        """Protected prefixes means you can change any part of them, but not at the top-level"""
        self._assert_valid_prefix(prefix)
        self._protected_prefixes += (prefix, )

    def _assert_valid_prefix(self, prefix: str) -> None:
        """Prefixes cannot contain "." or be a reserved word"""
        assert prefix and '.' not in prefix and prefix not in self._RESERVED_WORDS, "Invalid prefix"

    def push_frame(self, locals_list: list) -> None:
        if len(self._frames) >= 8192: raise RecursionError()
        new_frame = CopyOnWriteFrame(self._current_frame, locals_list)
        try:
            self._frames.append(new_frame)
            # Fully populate the local variables
            if locals_list:
                for local in locals_list:
                    self.set_var_user(local[1], *local[0])
        except Exception as e:
            self.pop_frame()
            raise e

    def pop_frame(self) -> None:
        if len(self._frames) <= 1: raise RuntimeError('Frame underflow')
        dropped_frame = self._frames.pop()
        dropped_frame.drop()

    @property
    def _current_frame(self) -> "Frame":
        """The frame at the end of the list is the current frame"""
        return self._frames[-1]

    @property
    def _global_frame(self) -> "Frame":
        """The frame at the head of the list is the global frame"""
        return self._frames[0]

    def keys(self):
        """Return all the top-level keys in the dictionary"""
        return self._current_frame.keys()

    def reset(self) -> None:
        """
        Removes:
        * Everything outside of immutable and protected prefixes
        * Contents of protected prefixes
        """
        self._current_frame.reset(self._protected_prefixes, self._immutable_prefixes)

    def clear_scratch(self) -> None:
        self.get_var(_SCRATCH_PREFIX).clear()

    def set_var_user(self, value: Any, /, *path: str) -> Any:
        """
        Set an item within the dictionary.
        This is a method to call with user input.
        Returns the value passed in.
        """
        return self.set_var(value, *self.validate_user_set_path(*self.validate_user_path(*path)))

    def get_var_user(self, /, *path: str) -> Any:
        """
        Get an item within the dictionary.
        This is a method to call with user input.
        Returns the values stored on the path, or None if the
        path does not lead to a dictionary.
        Note that "None" is not a definitive "not found" statement.
        """
        return self.get_var(*self.validate_user_path(*path))

    def unset_var_user(self, *path: str) -> Any:
        """
        Remove an item from the dictionary.
        This is a method to call with user input.
        Returns the value removed.
        Note that "None" is not a definitive "not found" statement.
        """
        return self.unset_var(*self.validate_user_set_path(*self.validate_user_path(*path)))

    def set_var(self, data: Any, /, *path: str) -> Any:
        """
        Called with vetted user args or can be called directly.
        Returns the value passed in.
        """
        current = self._current_frame
        # optimizing for this case prevents the possible
        # deepcopy of something we are about to overwrite
        # when working in a local frame
        if len(path) > 1:
            for step in path[:-1]:
                # If the next step doesn't exist, create it as dictionary
                next_step = current.setdefault(step, {})
                # If it isn't a dictionary, it has to become one
                if not isinstance(next_step, (Frame, dict)):
                    next_step = {}
                    current[step] = next_step
                current = next_step
        # Last step in the path gets the data
        current[path[-1]] = data
        return data

    def unset_var(self, *path: str) -> Any:
        """
        Called with vetted user args or can be called directly.
        Returns the value removed.
        Note that "None" is not a definitive "not found" statement.
        """
        current = self._current_frame
        for step in path[:-1]:
            # If the next step doesn't exist, or is
            # not a dictionary, we can't go anywhere
            # to unset something
            next_step = current.get(step, None)
            if not isinstance(next_step, (Frame, dict)): return None
            current = next_step
        # Last step in the path gets removed
        return current.pop(path[-1], None)

    def get_var(self, *path: str) -> Any:
        """
        Called with vetted user args or can be called directly.
        Returns the values stored on the path, or None if the
        path does not lead to a dictionary.
        Note that "None" is not a definitive "not found" statement.
        """
        data = self._current_frame
        for key in path:
            if not isinstance(data, (Frame, dict)) or key not in data: return None
            data = self.value_for(data[key])
        return data

    def var_exists(self, *path: str) -> tuple[bool, Any]:
        """
        Returns a tuple that says if the value exists and,
        if it does, what that value is.
        """
        if not path: return (False, None)
        data = self._current_frame
        for key in path:
            if not isinstance(data, (Frame, dict)) or key not in data: return (False, None)
            data = data[key]
        return (True, self.value_for(data))

    def validate_user_path(self, *path: str) -> tuple:
        """Checks the path for validity"""
        if not path: raise ValueError('Empty/Missing path')
        # Check for anything that is None, isn't a string, or strings that are "empty"
        if any(step is None or not isinstance(step, str) or all(sc.isspace() for sc in step) for step in path):
            raise ValueError(f"Invalid name: {'.'.join(map(str, path))!r}")
        if any(step.lower() in self._RESERVED_WORDS for step in path):
            raise ValueError(f'{".".join(path)!r} contains reserved words')
        return path

    def validate_user_set_path(self, *path: str) -> tuple:
        """Check the path for validity in setting, preventing alterations of protected and immutable areas"""
        prefix: str = path[0]
        # protected means you can't change at the top level, but
        # you can change its properties
        if len(path) == 1 and prefix in self._protected_prefixes:
            raise ValueError(f'Cannot alter protected prefix {prefix!r}')
        # immutable means just that
        if prefix in self._immutable_prefixes:
            raise ValueError(f'Cannot alter {".".join(path)!r} - {prefix!r} is immutable')
        return path

    def value_for(self, data: Any) -> Any:
        """
        Allows us to dereferce executable items stored in the dictionary.
        This is (typically) handled by default, but not if you traverse the
        contents of the directory directly.
        """
        return data() if callable(data) and not isinstance(data, type) else data

class Frame:
    def __init__(self, locals_list: list=None) -> None:
        self._data: Dict[str, Any] = {}
        # Every frame gets its own scratch are
        self._data[_SCRATCH_PREFIX] = {}
        # In this way we make sure the frame
        # has these items rooted in it regardless
        # of the design. The caller is responsible
        # for the full population of value using the
        # correct methods.
        if locals_list:
            for prefix in [local[0][0] for local in locals_list]:
                self._data[prefix] = None

    def drop(self) -> None:
        self._data.clear()
        self._data = None

    def reset(self, protected_prefixes: tuple, immutable_prefixes: tuple) -> None:
        for key in list(self._data):  # list() to avoid dict size change during iteration
            if key in protected_prefixes:
                self._data[key] = {}
            else:
                if key not in immutable_prefixes:
                    del self._data[key]

    def __iter__(self): return iter(self._data)
    def __getitem__(self, key: str) -> Any: return self._data[key]
    def __setitem__(self, key: str, value: Any) -> None: self._data[key] = value
    def __delitem__(self, key: str) -> None: del self._data[key]
    def __contains__(self, key: str) -> bool: return key in self._data
    def __repr__(self) -> str: return f'{self.__class__.__name__}({self._data!r})'
    def __str__(self) -> str: return str(self._data)

    def keys(self) -> KeysView[str]: return self._data.keys()

    def setdefault(self, key: str, default: Optional[Any] = None) -> Any:
        return self._data.setdefault(key, default)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self._data.get(key, default)

    def pop(self, key: str, default: Optional[Any] = None) -> Any:
        return self._data.pop(key, default)

class CopyOnWriteFrame(Frame):
    def __init__(self, base_frame: Frame, locals_list: list) -> None:
        super().__init__(locals_list)
        self._base_frame: Frame = base_frame

    def drop(self) -> None:
        try:
            super().drop()
        finally:
            self._base_frame = None

    def reset(self, protected_prefixes: tuple, immutable_prefixes: tuple) -> None:
        super().reset(protected_prefixes, immutable_prefixes)
        self._base_frame.reset(protected_prefixes, immutable_prefixes)

    def __iter__(self) -> Iterator:
        seen = set()
        for key in self._data:
            yield key
            seen.add(key)
        for key in self._base_frame:
            if key not in seen:
                yield key

    def __getitem__(self, key: str) -> Any:
        return self._data[key] if key in self._data else self._base_frame[key]

    def __delitem__(self, key: str) -> None:
        if key in self._data:
            del self._data[key]
        else:
            del self._base_frame[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data or key in self._base_frame

    def setdefault(self, key: str, default: Optional[Any] = None) -> Any:
        """
        This is called when we are looking for the root of a path for modification.
        If we have the value, we return it (it is a "local").
        If the base has the value (it is a "global") we _clone_ it and store
        the clone before returning it. Otherwise we return the default value.
        Note that cloning is only performed on lists and dictionaries (mutable objects)
        and that a "deep copy" is always performed.
        """
        if key in self._data: return self._data[key]
        # This is our "copy-on-write" behavior
        # We only need to make a deep copy for mutable objects
        if key in self._base_frame: default = self._base_frame[key]
        if isinstance(default, (list, dict)): default = copy.deepcopy(default)
        self._data[key] = default
        return default
