"""
The DataDictionary holds hierarchical data used by the application.
Most of the space is avaialble for the user's application, but parts--typically constants--
are immutable.
"""

from typing import Any
import math
import os
import re
import string

from mathpak import coerce_value

class DataDictionary():
    """
    The following portions are immutable:

    * env - the imported environment
    * math - math constants
    * string - string constant
    * os - operating system specific constants

    arg is mutable, but protected, meaning it cannot be unset or overwritten at
    the top-level. Individual components within it can be changed, though.
    """
    _ENV_EXCLUDE = tuple(re.compile(pattern, re.IGNORECASE) for pattern in ('^VSCODE', '^_$', '^(OLD)?PWD$'))
    _OS_CONSTS = ( 'defpath',  'devnull', 'extsep', 'linesep', 'name', 'pardir', 'pathsep', 'sep' )

    _ARG_PREFIX = 'arg'
    _DEBUG_PATH = (_ARG_PREFIX, 'debug')
    _VERBOSE_PATH = (_ARG_PREFIX, 'verbose')
    _ECHO_PATH = (_ARG_PREFIX, 'echo')

    # These can't appear in a path name (to prevent confusion)
    _RESERVED_WORDS = ('true', 'false', 'none', 'null', 'inf', 'nan')

    def __init__(self):
        self._dd = {}
        self._debug = False
        self._echo = False
        self._verbose = False
        self._immutable_prefixes = tuple()
        self._protected_prefixes = tuple()
        for mod in (math, string):
            name = mod.__name__
            self.set_var(self._get_consts(mod), name)
            self.add_immutable_prefix(name)
        for func, name in ((self._get_os_consts, 'os'), (self._get_environment, 'env')):
            self.set_var(func(), name)
            self.add_immutable_prefix(name)

    def add_immutable_prefix(self, prefix: str) -> None:
        """Immutable prefixes means you cant change any part of them"""
        self._immutable_prefixes += (prefix, )

    def add_protected_prefix(self, prefix: str) -> None:
        """Protected prefixes means you can change any part of them, but not at the top-level"""
        self._protected_prefixes += (prefix, )

    def keys(self): return self._dd.keys()

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
        return self.set_var(value, *self._validate_user_set_path(*self._validate_user_path(*path)))

    def get_var_user(self, /, *path: str) -> Any:
        """
        Get an item within the dictionary.
        This is a method to call with user input.
        Returns the values stored on the path, or None if the
        path does not lead to a dictionary.
        Note that "None" is not a definitive "not found" statement.
        """
        return self.get_var(*self._validate_user_path(*path))

    def unset_var_user(self, *path: str) -> Any:
        """
        Remove an item from the dictionary.
        This is a method to call with user input.
        Returns the value removed.
        Note that "None" is not a definitive "not found" statement.
        """
        return self.unset_var(*self._validate_user_set_path(*self._validate_user_path(*path)))

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
            data = data[key]
        return data

    def _validate_user_path(self, *path: str) -> tuple:
        if not path: raise ValueError('Empty/Missing path')
        # Check for anything that is None, isn't a string, or strings that are "empty"
        if any(step is None or not isinstance(step, str) or all(sc.isspace() for sc in step) for step in path) :
            raise ValueError(f"Invalid path: {'.'.join(map(str, path))}")
        if any(step.lower() in self._RESERVED_WORDS for step in path):
            raise ValueError(f'Invalid path: {".".join(path)} contains reserved values')
        return path

    def _validate_user_set_path(self, *path: str) -> tuple:
        prefix: str = path[0]
        # protected means you can't change at the top level, but
        # you can change its properties
        if len(path) == 1 and prefix in self._protected_prefixes:
            raise ValueError(f'Cannot alter protected prefix {prefix}')
        # immutable means just that
        if prefix in self._immutable_prefixes:
            raise ValueError(f'Cannot alter {".".join(path)} - {prefix} is immutable')
        return path

    @classmethod
    def _get_os_consts(cls) -> dict:
        rc = { key: value for key, value in cls._get_consts(os).items() if key in cls._OS_CONSTS }
        rc['uid'] = os.getuid()
        rc['gid'] = os.getgid()
        rc['login'] = os.getenv('USER') or os.getlogin()
        return rc

    @classmethod
    def _get_environment(cls) -> dict:
        rc = {
                name: coerce_value(value) for name, value in os.environ.items()
                    if not any(pattern.search(name) for pattern in cls._ENV_EXCLUDE)
             }
        for name, value in rc.items():
            if isinstance(value, str) and re.search(r'(_)?PATH$', name, re.IGNORECASE):
                rc[name] = tuple(value.split(os.pathsep))
        return rc

    @classmethod
    def _get_consts(cls, source_mod) -> dict:
        return { key: value for key, value in vars(source_mod).items()
                    if isinstance(value, (int, float, str, dict, list, tuple)) and not key.startswith("__")
               }
