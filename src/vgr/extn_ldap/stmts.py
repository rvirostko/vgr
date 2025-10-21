"""
Implementations of LDAP Statements
"""

from typing import Any
import os

from lark import Tree
from ldap3 import ANONYMOUS, SIMPLE, NTLM, BASE, LEVEL, SUBTREE, ALL_ATTRIBUTES, NO_ATTRIBUTES, DEREF_ALWAYS, DEREF_NEVER
from ..app_exceptions import VgrRuntimeError
from ..data_dict import DataDictionary, DynamicValue
from ..evaluate import (
    _var_name_path,
    do_set,
    get_writable_var_path,
)
from ..exec_context import ExecContext
from ..mathpak import (
    bound_ops,
    poly_bool,
    poly_int,
    poly_list,
    poly_str,
    poly_strip,
    type_str,
)

from .ldap_client import LdapClientManager, validate_ldap_url

_CONN_NAME_ARG = 'conn_name'
_BASE_ARG = 'search_base'
_GIVING_ARG = 'giving'
_USING_ARG = 'using'

_LDAP_PREFIX = 'ldap'
_DEFAULT_GIVING_PATH = (_LDAP_PREFIX, 'result')

_DEFAULT_CONN_NAME = 'DefaultConnection'

_CONNECTIONS = LdapClientManager()

class ExtnState():
    default_connection = None

_STATE = ExtnState()

_SCOPE_MAP = {
    'base':    BASE,
    'level':   LEVEL,
    'subtree': SUBTREE,
}

_AUTH_MAP = {
    'anonymous': ANONYMOUS,
    'simple': SIMPLE,
    'ntlm': NTLM,
}

def ldap_initialize(dd: DataDictionary) -> None:
    dd.add_immutable_prefix(_LDAP_PREFIX)
    dd.set_var(DynamicValue(lambda : _STATE.default_connection), _LDAP_PREFIX, 'connection')
    dd.set_var(None, *_DEFAULT_GIVING_PATH)
    for name, value in _SCOPE_MAP.items():
        dd.set_var(value, _LDAP_PREFIX, 'scope', name)
    for name, value in _AUTH_MAP.items():
        dd.set_var(value, _LDAP_PREFIX, 'auth', name)

@bound_ops("Ldap-Connect")
def execute_connect(ctx: ExecContext, statement: Tree) -> None:
    """
**Establish an LDAP connection**

* Ldap Connect<br>
  <em>Host [Is] _host_<br>
  <em>[Auth | Authentication] [Is] _auth_type_<br>
  <em>User [Is] _user_<br>
  <em>Password [Is] _password_<br>
  <em>Read Only [[Is] _read_only_]<br>
  <em>[Return] Empty [Attrs | Attributes] [[Is] _empty_attrs_]<br>
  <em>As _connection_name_<br>

The default for _auth_type_ is _Simple_. The default values for _read_only_
and _empty_attrs_ are _True_. Connection name is optional.

If _host_ is omitted then _LDAP_URL_, if defined, is used.
Likewise, environment variables _LDAP_BIND_DN_ and _LDAP_PASSWORD_ are used
if _user_ and _password_ are omitted and _auth_type_ is _Simple_.
"""
    conn_name = None
    kwargs = {
        'authentication':          SIMPLE,
        'read_only':               False,
        'return_empty_attributes': False,
        _CONN_NAME_ARG:            _DEFAULT_CONN_NAME
    }
    _extract_args(ctx, kwargs, statement.children)
    # Consult the environment for missing values
    kwargs.setdefault('url', os.environ.get('LDAP_URL'))
    if kwargs['authentication'] == SIMPLE:
        kwargs.setdefault('user', os.environ.get('LDAP_BIND_DN'))
        kwargs.setdefault('password', os.environ.get('LDAP_PASSWORD'))
    conn_name = kwargs.pop(_CONN_NAME_ARG)
    _CONNECTIONS.connect(conn_name, **kwargs)
    _STATE.default_connection = conn_name
    do_set(ctx, None, *_DEFAULT_GIVING_PATH)

@bound_ops("Ldap-Disconnect")
def execute_disconnect(ctx: ExecContext, statement: Tree) -> None:
    """
**Disconnect from LDAP**

* Ldap Disconnect
* Ldap Disconnect [From] _connection_name_

"""
    if statement.children:
        name = _resolve_str_arg(ctx, statement.children[0], 'Ldap Connection Name')
    else:
        name = _STATE.default_connection or _DEFAULT_CONN_NAME
    try:
        _CONNECTIONS.disconnect(name)
    finally:
        if name == _STATE.default_connection: _STATE.default_connection = None
        do_set(ctx, None, *_DEFAULT_GIVING_PATH)

@bound_ops("Ldap-Search")
def execute_search(ctx: ExecContext, statement: Tree) -> None:
    """
**Perform an LDAP search**

* Ldap Search<br>
  <em>Base [Is] _base_<br>
  <em>Scope [Is] _scope_<br>
  <em>Query [Is] _query_<br>
  <em>Attributes [Is | Are] _attributes_<br>
  <em>Giving _variable_<br>
  <em>Using [Connection] _connection_name_<br>

All items are optional except for _base_.

"""
    kwargs = _extract_args(ctx,
                           {
                                _GIVING_ARG: _DEFAULT_GIVING_PATH,
                                _USING_ARG: _STATE.default_connection or _DEFAULT_CONN_NAME,
                           },
                           statement.children)
    conn_name = kwargs.pop(_USING_ARG)
    result_path = kwargs.pop(_GIVING_ARG)
    if _BASE_ARG not in kwargs:
        raise VgrRuntimeError(statement, ValueError('Required argument \'Base\' missing'))
    ctx.set_var(None, *result_path)
    do_set(ctx, _CONNECTIONS.get_connection(conn_name).search(**kwargs), *result_path)

def _resolve_int_arg(ctx: ExecContext, opt: Tree, name: str) -> str:
    expr = opt.children[0]
    rc = ctx.eval_expr_or_const(expr)
    if rc is None: return None
    if isinstance(rc, (int, float)): return int(rc)
    if isinstance(rc, str):
        try:
            return poly_int(rc)
        except ValueError as e:
            raise VgrRuntimeError(expr, e) from e
    raise VgrRuntimeError(expr, TypeError(f'{name} must be a number; found {type_str(rc)}'))

def _resolve_str_arg(ctx: ExecContext, opt: Tree, name: str, allow_none: bool=False) -> str:
    expr = opt.children[0]
    rc = ctx.eval_expr_or_const(expr)
    if rc is None and allow_none: return None
    if not isinstance(rc, str): raise VgrRuntimeError(expr, TypeError(f'{name} must be a string; found {type_str(rc)}'))
    return rc

def _resolve_opt_str_arg(ctx: ExecContext, opt: Tree, name: str) -> str:
    """Allows for a None result"""
    return _resolve_str_arg(ctx, opt, name, True)

def _resolve_bool_arg(ctx: ExecContext, opt: Tree, name: str) -> bool:
    expr = opt.children[0]
    rc = ctx.eval_expr_or_const(expr)
    if rc is None: return False
    if isinstance(rc, (dict, list, tuple)): raise VgrRuntimeError(expr, TypeError(f'{name} must be a boolean; found {type_str(rc)}'))
    return poly_bool(rc)

def _resolve_opt_bool_arg(ctx: ExecContext, opt: Tree, name: str) -> bool:
    """Presence of option means True, but has an optional child expression which must be a bool"""
    return _resolve_bool_arg(ctx, opt, name) if opt.children else True

def _resolve_deref_arg(ctx: ExecContext, opt: Tree, name: str) -> str:
    return DEREF_ALWAYS if _resolve_opt_bool_arg(ctx, opt, name) else DEREF_NEVER

def _resolve_url_arg(ctx: ExecContext, opt: Tree, name: str) -> str:
    return validate_ldap_url(_resolve_str_arg(ctx, opt, name), name)

def _resolve_scope_arg(ctx: ExecContext, opt: Tree, name: str) -> str:
    """
    Normalize a user-supplied scope string to ldap3's canonical constants.

    Accepted synonyms (case-insensitive):
        - 'base'                  -> BASE
        - 'level', 'one'          -> LEVEL
        - 'subtree', 'sub', 'all' -> SUBTREE

    Returns:
        The ldap3 constant (BASE, LEVEL, SUBTREE)
    """
    expr = opt.children[0]
    value = _resolve_str_arg(ctx, expr, name, True)
    if value is None: return BASE
    v = value.strip().lower()
    if v in ('base', ''): return BASE
    if v in ('level', 'one'): return LEVEL
    if v in ('subtree', 'sub', 'all'): return SUBTREE
    raise VgrRuntimeError(expr, ValueError(f'{name} {value!r} is invalid'))

def _resolve_auth_arg(ctx: ExecContext, opt: Tree, name: str) -> str:
    """
    Normalize a user-supplied authentication type string to ldap3's canonical constants.

    Accepted synonyms (case-insensitive):
        - 'anon', 'anonymous'        -> ANONYMOUS
        - 'simple', 'user', 'bind'   -> SIMPLE
        - 'ntlm', 'windows', 'sspi'  -> NTLM

    Returns:
        The ldap3 constant (ANONYMOUS, SIMPLE, NTLM)
    """
    expr = opt.children[0]
    value = _resolve_str_arg(ctx, expr, name, True)
    if value is None: return SIMPLE
    v = value.strip().lower()
    if v in ('simple', 'user', 'bind', ''): return SIMPLE
    if v in ('anon', 'anonymous'): return ANONYMOUS
    if v in ('ntlm', 'windows', 'sspi'): return NTLM
    raise VgrRuntimeError(expr, ValueError(f'{name} {value!r} is invalid'))

def _resolve_attrs_arg(ctx: ExecContext, opt: Tree, name: str) -> Any:
    expr = opt.children[0]
    rc = ctx.eval_expr_or_const(expr)
    if rc is None: return NO_ATTRIBUTES
    if isinstance(rc, str) and rc.lower().strip() in ('all', '*'): return ALL_ATTRIBUTES
    if isinstance(rc, dict):
        rc = list(rc.keys())
    else:
        rc = poly_list(rc)
    attrs = []
    # Report on non-strings (like nested lists or dicts)
    for attr in poly_strip(poly_str(rc)):
        # Filter out Nones and blank strings
        if attr:
            if isinstance(attr, str):
                attrs.append(attr)
            else:
                raise VgrRuntimeError(expr, TypeError(f'{name} can contain only strings; found {type_str(rc)}'))
    return attrs if attrs else NO_ATTRIBUTES

def _resolve_giving_arg(ctx: ExecContext, opt: Tree, _name: str) -> tuple:
    var = opt.children[0]
    try:
        return get_writable_var_path(ctx, var)
    except VgrRuntimeError as e:
        path = _var_name_path(var)
        if path == _DEFAULT_GIVING_PATH: return path
        raise e

_OPT_HANDLER = {
    _BASE_ARG:                  ('Base',                       _resolve_str_arg),
    _CONN_NAME_ARG:             ('Connection Name',            _resolve_opt_str_arg),
    _GIVING_ARG:                ('Giving',                     _resolve_giving_arg),
    _USING_ARG:                 ('Using',                      _resolve_opt_str_arg),
    'attributes':               ('Attributes',                 _resolve_attrs_arg),
    'auth':                     ('authentication',             _resolve_auth_arg),
    'dereference_aliases':      ('Derference Aliases',         _resolve_deref_arg),
    'get_operation_attributes': ('Get Operational Attributes', _resolve_opt_bool_arg),
    'paged_size':               ('Page Size',                  _resolve_int_arg),
    'password':                 ('Password',                   _resolve_opt_str_arg),
    'read_only':                ('Read-Only',                  _resolve_opt_bool_arg),
    'return_empty_attributes':  ('Return Empty Attributes',    _resolve_opt_bool_arg),
    'search_filter':            ('Filter',                     _resolve_opt_str_arg),
    'search_scope':             ('Scope',                      _resolve_scope_arg),
    'size_limit':               ('Size Limit',                 _resolve_int_arg),
    'time_limit':               ('Time Limit',                 _resolve_int_arg),
    'url':                      ('URL',                        _resolve_url_arg),
    'user':                     ('User',                       _resolve_str_arg),
}

def _extract_args(ctx: ExecContext, args: dict, opts: list) -> dict:
    for opt in opts:
        if not isinstance(opt, Tree) or not opt.data.startswith('lopt_'):
            raise VgrRuntimeError(opt, ValueError(f'Unexpected Ldap argument {opt.data!r}:{type_str(opt)}')) # SNO
        arg_name = opt.data[5:]
        if arg_name not in _OPT_HANDLER:
            raise VgrRuntimeError(opt, NotImplementedError(f'Ldap argument {arg_name!r} not implemented')) # SNO
        name, handler = _OPT_HANDLER[arg_name]
        args[arg_name] = handler(ctx, opt, name)
    return args
