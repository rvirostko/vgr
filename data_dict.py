#! /usr/bin/env python3

import string
import math
import os
import re
from mathpak import poly_bool, poly_number
from typing import Any

class DataDictionary():
    _ENV_EXCLUDE = tuple(re.compile(pattern, re.IGNORECASE) for pattern in ('^VSCODE', '^_$', '^(OLD)?PWD$'))
    _OS_CONSTS = ( 'defpath',  'devnull', 'extsep', 'linesep', 'name', 'pardir', 'pathsep', 'sep' )
    _ARG_PREFIX = 'arg'
    _ENV_PREFIX = 'env'
    _MATH_PREFIX = 'math'
    _OS_PREFIX = 'os'
    _STRING_PREFIX = 'string'
    _VGR_PREFIX = '_vgr'
    _INTERNAL_PREFIXES = ( _ARG_PREFIX, _ENV_PREFIX, _MATH_PREFIX, _OS_PREFIX, _STRING_PREFIX, _VGR_PREFIX )

    _DEBUG_VAR = 'debug'
    _ECHO_VAR = 'echo'
    _VERBOSE_VAR = 'verbose'
    _OFS_VAR = 'ofs'  # Like AWK's Output Field Separator
    _ORS_VAR = 'ors' # Like AWK's Output Record Separator

    _DD = {}

    def __init__(self):
        self._set_var(self._DD, self._get_environment(), self._ENV_PREFIX)
        self._set_var(self._DD, self._get_string_consts(), self._STRING_PREFIX)
        self._set_var(self._DD, self._get_math_consts(), self._MATH_PREFIX)
        self._set_var(self._DD, self._get_os_consts(), self._OS_PREFIX)
        self._DD[self._VGR_PREFIX] = {}
        self.set_debug(False)
        self.set_echo(False)
        self.set_verbose(False)
        # Pick up the defaults AWK would use
        # Since we don't allow the env space to be changed,
        # we have to keep our own copies for the user to change with
        # either Set or with command line arguments
        self._set_var(self._DD, self._defaut_ofs(), self._ARG_PREFIX, self._OFS_VAR)
        self._set_var(self._DD, self._defaut_ors(), self._ARG_PREFIX, self._ORS_VAR)

    def get_internal_prefixes(self) -> tuple: return self._INTERNAL_PREFIXES

    def keys(self): return self._DD.keys()

    def set_debug(self, v: bool=True) -> None: self._set_var(self._DD, bool(v), self._ARG_PREFIX, self._DEBUG_VAR)
    def set_verbose(self, v: bool=True) -> None: self._set_var(self._DD, bool(v), self._ARG_PREFIX, self._VERBOSE_VAR)
    def set_echo(self, v: bool=True) -> None: self._set_var(self._DD, bool(v), self._ARG_PREFIX, self._ECHO_VAR)
    def set_grammar(self, grammar: str) -> None: self._set_var(self._DD, grammar, self._VGR_PREFIX, 'grammar')
    def set_statement(self, statement: str) -> None: self._set_var(self._DD, statement, self._VGR_PREFIX, 'statement')

    def is_debug(self) -> bool: return bool(self._get_var(self._DD, self._ARG_PREFIX, self._DEBUG_VAR))
    def is_echo(self) -> bool: return bool(self._get_var(self._DD, self._ARG_PREFIX, self._ECHO_VAR))
    def is_verbose(self) -> bool: return bool(self._get_var(self._DD, self._ARG_PREFIX, self._VERBOSE_VAR))
    def get_ofs(self) -> str: return str(self._get_var(self._DD, self._ARG_PREFIX, self._OFS_VAR) or self._defaut_ofs())
    def get_ors(self) -> str: return str(self._get_var(self._DD, self._ARG_PREFIX, self._ORS_VAR) or self._defaut_ors())

    def set_var(self, value: Any, *path: str) -> None:
        """Set an item within the dictionary"""
        self._set_var(self._DD, value, *self._validate_user_set_path(*self._validate_user_path(*path)))

    def get_var(self, *path: str) -> Any:
        """Get an item within the dictionary"""
        return self.get_var_relative(self._DD, *self._validate_user_path(*path))

    def get_var_relative(self, start: dict, *path: str) -> Any:
        """Get an item relative to start"""
        return self._get_var(start, *self._validate_user_path(*path))

    def parse_user_args(self, user_args: list[str]) -> None:
        """
        Parse a list of 'name=value' strings into .
        If an argument doesn't contain '=', it's ignored.
        These are meant to be simple values, not collections.
        """
        for arg in user_args:
            if '=' in arg:
                name, value = re.split(r'\s*=\s*', arg, 1)
                path = tuple(step for step in re.split(r'\s*[.]\s*', name.strip()))
                if path:
                    match = re.fullmatch(r'\s*"([^"]*)"\s*', value)
                    path = (self._ARG_PREFIX,) + path
                    self.set_var(match.group(1) if match else self._coerce_value(value), *path)

    def _validate_user_path(self, *path: str) -> tuple:
        if not path: raise ValueError('Empty/Missing path')
        # Check for anything that is None, isn't a string, or strings that are "empty"
        if any(step is None or not isinstance(step, str) or all(sc.isspace() for sc in step) for step in path) :
            raise ValueError(f"Invalid path: {'.'.join(map(str, path))}")
        return path

    def _validate_user_set_path(self, *path: str) -> tuple:
        prefix: str = path[0]
        if prefix in self._INTERNAL_PREFIXES:
            # Can't slam "arg" but can modify its contents
            if prefix != self._ARG_PREFIX or len(path) < 2:
                raise ValueError(f'Cannot set {".".join(path)} - {prefix} is immutable')
        return path

    def _get_string_consts(self) -> dict: return self._get_consts(string)

    def _get_math_consts(self) -> dict: return self._get_consts(math)

    def _get_os_consts(self) -> dict:
        rc = { key: value for key, value in self._get_consts(os).items() if key in self._OS_CONSTS }
        rc['cwd'] = os.getcwd()
        rc['uid'] = os.getuid()
        rc['gid'] = os.getgid()
        rc['login'] = os.getenv('USER') or os.getlogin()
        return rc

    def _get_environment(self) -> dict:
        rc = { name: self._coerce_value(value) for name, value in os.environ.items() if not any(pattern.search(name) for pattern in self._ENV_EXCLUDE) }
        for name, value in rc.items():
            if isinstance(value, str) and re.search(r'(_)?PATH$', name, re.IGNORECASE): rc[name] = tuple(value.split(os.pathsep))
        rc['PWD'] = os.getcwd()
        return rc

    def _set_var(self, start: dict, data: Any, *path: str) -> None:
        if start == None or not path: return
        current = start
        for step in path[:-1]:
            # If the next step doesn't exist, create it as dictionary
            next = current.setdefault(step, {})
            # If it isn't a dictionary, it has to become one
            if not isinstance(next, dict):
                next = {}
                current[step] = next
            current = next
        # Last step in the path gets the data
        current[path[-1]] = data

    def _get_var(self, data: Any, *path: str) -> Any:
        if data is not None:
            for key in path:
                if not isinstance(data, dict) or key not in data: return None
                data = data[key]
        return data

    def _get_consts(self, source_mod) -> dict:
        return { key: value for key, value in vars(source_mod).items() if isinstance(value, (int, float, str, dict, list, tuple)) and not key.startswith("__") }

    def _coerce_value(self, value: Any):
        """
        Coerce the string value to None, int, float, or bool.
        Falls back to the original string.
        """
        if value == None or isinstance(value, (bool, int, float, dict, list, tuple)): return value
        if value.strip().lower() in ('true', 'false'): return poly_bool(value)
        try: return poly_number(value)
        except TypeError: return None if value.lower() == 'none' else value

    def _defaut_ofs(self) -> str: return os.getenv('OFS', ' ')

    def _defaut_ors(self) -> str: return os.getenv('ORS', '\n')
