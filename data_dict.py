#! /usr/bin/env python3

from typing import Any
import math
import os
import re
import string

from mathpak import coerce_value

class DataDictionary():
    """TODO"""
    _ENV_EXCLUDE = tuple(re.compile(pattern, re.IGNORECASE) for pattern in ('^VSCODE', '^_$', '^(OLD)?PWD$'))
    _OS_CONSTS = ( 'defpath',  'devnull', 'extsep', 'linesep', 'name', 'pardir', 'pathsep', 'sep' )
    _ARG_PREFIX = 'arg'
    _ENV_PREFIX = 'env'
    _MATH_PREFIX = 'math'
    _OS_PREFIX = 'os'
    _STRING_PREFIX = 'string'

    _DEBUG_VAR = 'debug'
    _ECHO_VAR = 'echo'
    _VERBOSE_VAR = 'verbose'
    # These can't appear in a path name (to prevent confusion)
    _RESERVED_WORDS = ('true', 'false', 'none', 'null', 'inf', 'nan')

    def __init__(self):
        self._dd = {}
        self._immutable_prefixes = tuple()
        self._protected_prefixes = tuple()
        self.add_immutable_prefix(self._ENV_PREFIX)
        self.set_var(self._dd, self._get_environment(), self._ENV_PREFIX)
        self.add_immutable_prefix(self._STRING_PREFIX)
        self.set_var(self._dd, self._get_string_consts(), self._STRING_PREFIX)
        self.add_immutable_prefix(self._MATH_PREFIX)
        self.set_var(self._dd, self._get_math_consts(), self._MATH_PREFIX)
        self.add_immutable_prefix(self._OS_PREFIX)
        self.set_var(self._dd, self._get_os_consts(), self._OS_PREFIX)
        # Id like these to move...
        self.set_debug(False)
        self.set_echo(False)
        self.set_verbose(False)

    def add_immutable_prefix(self, prefix: str) -> None:
        """Immutable prefixes means you cant change any part of them"""
        self._immutable_prefixes += (prefix, )

    def add_protected_prefix(self, prefix: str) -> None:
        """Protected prefixes means you can change any part of them, but not at the top-level"""
        self._protected_prefixes += (prefix, )

    def keys(self): return self._dd.keys()

    # This block might be moving... At least echo should
    def set_debug(self, v: bool=True) -> None: self.set_var(self._dd, bool(v), self._ARG_PREFIX, self._DEBUG_VAR)
    def set_verbose(self, v: bool=True) -> None: self.set_var(self._dd, bool(v), self._ARG_PREFIX, self._VERBOSE_VAR)
    def set_echo(self, v: bool=True) -> None: self.set_var(self._dd, bool(v), self._ARG_PREFIX, self._ECHO_VAR)
    def is_debug(self) -> bool: return bool(self.get_var(self._dd, self._ARG_PREFIX, self._DEBUG_VAR))
    def is_echo(self) -> bool: return bool(self.get_var(self._dd, self._ARG_PREFIX, self._ECHO_VAR))
    def is_verbose(self) -> bool: return bool(self.get_var(self._dd, self._ARG_PREFIX, self._VERBOSE_VAR))

    def set_var_user(self, value: Any, *path: str) -> None:
        """
        Set an item within the dictionary.
        This is a method to call with user input.
        """
        self.set_var(self._dd, value, *self._validate_user_set_path(*self._validate_user_path(*path)))

    def get_var_user(self, *path: str) -> Any:
        """
        Get an item within the dictionary.
        This is a method to call with user input.
        """
        return self.get_var_user_relative(self._dd, *self._validate_user_path(*path))

    def get_var_user_relative(self, start: dict, *path: str) -> Any:
        """
        Get an item relative to start.
        This is a method to call with user input.
        """
        return self.get_var(start, *self._validate_user_path(*path)) if start is not None else None

    def set_var(self, start: dict, data: Any, *path: str) -> None:
        """
        Called with vetted user args or can be called directly.
        Pass in None for start when traversing a full path.
        """
        current = start or self._dd
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

    def get_var(self, data: Any, *path: str) -> Any:
        """
        Called with vetted user args or can be called directly.
        Pass in None for data when traversing a full path
        """
        data = data or self._dd
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
            raise ValueError(f'Cannot set {".".join(path)} - {prefix} is immutable')
        return path

    def _get_string_consts(self) -> dict: return self._get_consts(string)

    def _get_math_consts(self) -> dict: return self._get_consts(math)

    def _get_os_consts(self) -> dict:
        rc = { key: value for key, value in self._get_consts(os).items() if key in self._OS_CONSTS }
        rc['uid'] = os.getuid()
        rc['gid'] = os.getgid()
        rc['login'] = os.getenv('USER') or os.getlogin()
        return rc

    def _get_environment(self) -> dict:
        rc = {
                name: coerce_value(value) for name, value in os.environ.items()
                    if not any(pattern.search(name) for pattern in self._ENV_EXCLUDE)
             }
        for name, value in rc.items():
            if isinstance(value, str) and re.search(r'(_)?PATH$', name, re.IGNORECASE):
                rc[name] = tuple(value.split(os.pathsep))
        return rc

    def _get_consts(self, source_mod) -> dict:
        return { key: value for key, value in vars(source_mod).items()
                    if isinstance(value, (int, float, str, dict, list, tuple)) and not key.startswith("__")
               }
