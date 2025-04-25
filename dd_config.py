
"""
Utility routines for working with the global Data Dictionary
"""

from copy import deepcopy
from typing import Any
import getpass
import math
import os
import re
import string

from lark import Tree

from data_dict import DataDictionary
from mathpak import coerce_value
from redir import shorten, print_stderr

_VGR_PREFIX = 'vgr'
_STATEMENT_PATH = (_VGR_PREFIX, 'statement')
SHELL_PROMPT_PATH = (_VGR_PREFIX, 'prompt')
SHELL_HISTORY_PATH = (_VGR_PREFIX, 'history')
SHELL_HISTORY_SIZE_PATH = (_VGR_PREFIX, 'history_size')

_SCRATCH_PREFIX = '_'
ROWID_PATH = (_SCRATCH_PREFIX, 'rowid')

_ARG_PREFIX = 'arg'
OFS_PATH = (_ARG_PREFIX, 'ofs')
ORS_PATH = (_ARG_PREFIX, 'ors')
# If no "For" is given with a Select, this is the type used as default
DEFAULT_FOR_TYPE_PATH = (_ARG_PREFIX, 'default_for_type')

_ENV_EXCLUDE = tuple(re.compile(pattern, re.IGNORECASE) for pattern in ('^VSCODE', '^_$', '^(OLD)?PWD$'))
_OS_CONSTS = ( 'defpath',  'devnull', 'extsep', 'linesep', 'name', 'pardir', 'pathsep', 'sep' )

_RE_PREFIX = 're'
_RE_FLAGS = ('ASCII', 'IGNORECASE', 'LOCALE', 'MULTILINE', 'DOTALL', 'UNICODE', 'VERBOSE')

def dd_init() -> DataDictionary:
    dd = DataDictionary()
    dd.add_protected_prefix(_ARG_PREFIX)
    dd.add_immutable_prefix(_VGR_PREFIX)
    dd.set_var({}, _SCRATCH_PREFIX)
    dd.add_protected_prefix(_SCRATCH_PREFIX)
    for flag in _RE_FLAGS:
        dd.set_var(getattr(re, flag), _RE_PREFIX, flag)
    dd.add_immutable_prefix(_RE_PREFIX)
    for mod in (math, string):
        name = mod.__name__
        dd.set_var(_get_consts(mod), name)
        dd.add_immutable_prefix(name)
    for func, name in ((_get_os_consts, 'os'), (_get_environment, 'env')):
        dd.set_var(func(), name)
        dd.add_immutable_prefix(name)
    # Pick up the defaults AWK would use
    # Since we don't allow the env space to be changed,
    # we have to keep our own copies for the user to change with
    # either Set or with command line arguments
    dd.set_var(os.getenv('OFS', ' '), *OFS_PATH)
    dd.set_var(os.getenv('ORS', '\n'), *ORS_PATH)
    return dd

def dd_parse_user_args(dd: DataDictionary, user_args: list) -> None:
    # NB: User args can override debug/echo/verbose...
    for arg in user_args:
        if '=' in arg:
            name, value = re.split(r'\s*=', arg, 1)
            path = tuple(step for step in re.split(r'\s*[.]\s*', name.strip()))
            if path:
                # Strip off the quotes
                match = re.fullmatch(r'\s*"([^"]*)"\s*', value)
                path = (_ARG_PREFIX,) + path
                dd.set_var(match.group(1) if match else coerce_value(value), *path)

def dd_set_statement(dd: DataDictionary, statement_text: str) -> str:
    dd.set_var(statement_text, *_STATEMENT_PATH)

def dd_clear_scratch(dd: DataDictionary) -> None:
    dd.get_var(_SCRATCH_PREFIX).clear()

def dd_path(var_ref: Tree) -> tuple[str]:
    return tuple(name.value for name in var_ref.children)

def do_assignment(dd: DataDictionary, expr: Tree, value: Any, path: tuple[str]) -> None:
    """
    Use when you are doing an assignment (set) where you cannot be sure
    that the result is a reference to another mutable variable such as a list or dict.
    When it is, we need to make a copy before setting the value in the DD.
    """
    if isinstance(expr, Tree) and expr.data == 'var_ref' and isinstance(value, (list, dict)):
        value = deepcopy(value)
    do_set(dd, value, *path)

def do_set(dd: DataDictionary, value: Any, *path) -> None:
    """
    After calculations are done, use this to set a value.
    Generates verbose output.
    """
    new_value = dd.set_var_user(value, *path)
    if dd.verbose:
        print_stderr(dd, 'Set', '.'.join(path), 'To', shorten(repr(new_value)))

def do_unset(dd: DataDictionary, *path) -> None:
    """
    Use this to unset a value.
    Generates verbose output.
    """
    old_value = dd.unset_var_user(*path)
    if dd.verbose:
        print_stderr(dd, 'Removed', shorten(repr(old_value)), 'From', '.'.join(path))

def _get_os_consts() -> dict:
    rc = { key: value for key, value in _get_consts(os).items() if key in _OS_CONSTS }
    rc['login'] = getpass.getuser() or 'unknown'
    return rc

def _get_environment() -> dict:
    rc = {
            name: coerce_value(value) for name, value in os.environ.items()
                if not any(pattern.search(name) for pattern in _ENV_EXCLUDE)
            }
    for name, value in rc.items():
        if isinstance(value, str) and re.search(r'(_)?PATH$', name, re.IGNORECASE):
            rc[name] = tuple(value.split(os.pathsep))
    return rc

def _get_consts(source_mod) -> dict:
    return { key: value for key, value in vars(source_mod).items()
                if isinstance(value, (int, float, str, dict, list, tuple)) and not key.startswith("__")
            }
