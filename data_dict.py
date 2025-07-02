"""
The DataDictionary holds hierarchical data used by the application.
Most of the space is avaialble for the user's application, but parts--typically constants--
are immutable.
"""

from typing import Any

class DataDictionary():
    """
    A hierachical data store
    """
    _ARG_PREFIX = 'arg'
    _DEBUG_PATH = (_ARG_PREFIX, 'debug')
    _VERBOSE_PATH = (_ARG_PREFIX, 'verbose')
    _ECHO_PATH = (_ARG_PREFIX, 'echo')

    # These can't appear in a path name (to prevent confusion)
    _RESERVED_WORDS = ('true', 'false', 'none', 'null')

    def __init__(self):
        self._dd = {}
        self._immutable_prefixes = tuple()
        self._protected_prefixes = tuple()
        self.add_protected_prefix(self._ARG_PREFIX)

    def add_immutable_prefix(self, prefix: str) -> None:
        """Immutable prefixes means you cant change any part of them"""
        self._assert_valid_prefix(prefix)
        self._immutable_prefixes += (prefix, )

    def remove_immutable_prefix(self, prefix: str) -> None:
        """Removes immutability on part of the dictionary"""
        self._assert_valid_prefix(prefix)
        self._immutable_prefixes = tuple(x for x in self._immutable_prefixes if x != prefix)

    def add_protected_prefix(self, prefix: str) -> None:
        """Protected prefixes means you can change any part of them, but not at the top-level"""
        self._assert_valid_prefix(prefix)
        self._protected_prefixes += (prefix, )

    def remove_protected_prefix(self, prefix: str) -> None:
        """Removes protection on part of the dictionary"""
        self._assert_valid_prefix(prefix)
        self._protected_prefixes = tuple(x for x in self._protected_prefixes if x != prefix)

    def _assert_valid_prefix(self, prefix: str) -> None:
        assert prefix and '.' not in prefix and prefix not in self._RESERVED_WORDS, "Invalid prefix"

    def keys(self): return self._dd.keys()

    def reset(self) -> None:
        for key in list(self._dd):  # list() to avoid dict size change during iteration
            if key in self._protected_prefixes:
                self._dd[key] = {}
            else:
                if key not in self._immutable_prefixes:
                    del self._dd[key]
        self.debug = False
        self.verbose = False
        self.echo = False

    @property
    def debug(self) -> bool:
        return bool(self.get_var(*self._DEBUG_PATH))

    @debug.setter
    def debug(self, v: bool) -> None:
        self.set_var(bool(v), *self._DEBUG_PATH)

    @property
    def verbose(self) -> bool:
        return bool(self.get_var(*self._VERBOSE_PATH))

    @verbose.setter
    def verbose(self, v: bool) -> None:
        self.set_var(bool(v), *self._VERBOSE_PATH)

    @property
    def echo(self) -> bool:
        return bool(self.get_var(*self._ECHO_PATH))

    @echo.setter
    def echo(self, v: bool) -> None:
        self.set_var(bool(v), *self._ECHO_PATH)

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
        current = self._dd
        for step in path[:-1]:
            # If the next step doesn't exist, create it as dictionary
            next_step = current.setdefault(step, {})
            # If it isn't a dictionary, it has to become one
            if not isinstance(next_step, dict):
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
        current = self._dd
        for step in path[:-1]:
            # If the next step doesn't exist, or is
            # not a dictionary, we can't go anywhere
            # to unset something
            next_step = current.get(step, None)
            if not isinstance(next_step, dict): return None
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
        data = self._dd
        for key in path:
            if not isinstance(data, dict) or key not in data: return None
            data = self.value_for(data[key])
        return data

    def exists(self, *path: str) -> tuple[bool, Any]:
        """
        Returns a tuple that says if the value exists and,
        if it does, what that value is.
        """
        if not path: return (False, None)
        data = self._dd
        for key in path:
            if not isinstance(data, dict) or key not in data: return (False, None)
            data = data[key]
        return (True, self.value_for(data))

    def validate_user_path(self, *path: str) -> tuple:
        if not path: raise ValueError('Empty/Missing path')
        # Check for anything that is None, isn't a string, or strings that are "empty"
        if any(step is None or not isinstance(step, str) or all(sc.isspace() for sc in step) for step in path) :
            raise ValueError(f"Invalid path: {'.'.join(map(str, path))}")
        if any(step.lower() in self._RESERVED_WORDS for step in path):
            raise ValueError(f'Invalid path: {".".join(path)} contains reserved values')
        return path

    def validate_user_set_path(self, *path: str) -> tuple:
        prefix: str = path[0]
        # protected means you can't change at the top level, but
        # you can change its properties
        if len(path) == 1 and prefix in self._protected_prefixes:
            raise ValueError(f'Cannot alter protected prefix {prefix}')
        # immutable means just that
        if prefix in self._immutable_prefixes:
            raise ValueError(f'Cannot alter {".".join(path)} - {prefix} is immutable')
        return path

    def value_for(self, data: Any) -> Any:
        """
        Allows us to dereferce executable items stored in the dictionary.
        This is (typically) handled by default, but not if you traverse the
        contents of the directory directly.
        """
        return data() if callable(data) and not isinstance(data, type) else data
