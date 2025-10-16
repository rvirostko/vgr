"""
Implementations of LDAP Statements
"""

from typing import Any
import os

from lark import Tree
from ldap3 import ANONYMOUS, SIMPLE, NTLM, BASE, LEVEL, SUBTREE

from ..app_exceptions import VgrRuntimeError
from ..data_dict import DataDictionary, DynamicValue
from ..evaluate import do_set, _var_name_path
from ..exec_context import ExecContext
from ..mathpak import bound_ops, type_str

from .ldap_client import LdapClient, LdapClientManager

_BASE_ARG = 'base'
_SCOPE_ARG = 'scope'
_QUERY_ARG = 'query'
_RESULT_ARG = 'result'
_USING_ARG = 'using'

# These arguments result in a variable name
_ARG_VAR_NAME = (_RESULT_ARG,)

# These arguments are expressions -OR- they may be unquoted constants
# treated as strings. This is similar to the way "... AS <name>" is
# defined for Select statements.
_ARG_EXPR = (_BASE_ARG, _SCOPE_ARG, _QUERY_ARG, _USING_ARG)

_DEFAULT_CONN_NAME = 'DefaultConnection'

_CONNECTIONS = LdapClientManager()

class ExtnState():
    default_connection = None

_STATE = ExtnState()

_LDAP_PREFIX = 'ldap'
_DEFAULT_RESULT_PATH = (_LDAP_PREFIX, 'result')

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
    dd.set_var(None, *_DEFAULT_RESULT_PATH)
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
Environment variables _LDAP_BIND_DN_ and _LDAP_PASSWORD_ are used
if _user_ and _password_ are omitted and _auth_type_ is _Simple_.
"""
    conn_name = None
    kwargs = {
        'authentication': SIMPLE,
        'read_only': False,
        'return_empty_attributes': False,
    }
    for child in statement.children:
        if isinstance(child, Tree):
            name = child.data
            if name == 'ldap_conn_addr':
                kwargs['url'] = _resolve_str_arg(ctx, child.children[0], 'Host')
            elif name == 'ldap_user':
                kwargs['user'] = _resolve_str_arg(ctx, child.children[0], 'User')
            elif name == 'ldap_password':
                kwargs['password'] = _resolve_str_arg(ctx, child.children[0], 'Password', True)
            elif name == 'ldap_auth':
                kwargs['authentication'] = _normalize_auth_type(_resolve_str_arg(ctx, child.children[0], 'Authentication'))
            elif name == 'ldap_read_only':
                kwargs['read_only'] = _resolve_str_arg(ctx, child.children[0], 'Read-Only') if child.children else True
            elif name == 'ldap_empty_attrs':
                kwargs['return_empty_attributes'] = _resolve_str_arg(ctx, child.children[0], 'Return Empty Attributes') if child.children else True
            elif child.data == 'ldap_conn_name':
                conn_name = _resolve_str_arg(ctx, child.children[0], 'Ldap Connection Name')
            else:
                raise VgrRuntimeError(child, NotImplementedError(f'Argument {name!r} not handled')) # SNO
        else:
            raise VgrRuntimeError(child, ValueError(f'Unexpected Ldap argument {child!r}')) # SNO
    # Consult the environment for missing values
    kwargs.setdefault('url', os.environ.get('LDAP_URL'))
    if kwargs['authentication'] == SIMPLE:
        kwargs.setdefault('bind_dn', os.environ.get('LDAP_BIND_DN'))
        kwargs.setdefault('password', os.environ.get('LDAP_PASSWORD'))
    conn_name = conn_name or _DEFAULT_CONN_NAME
    _CONNECTIONS.connect(conn_name, **kwargs)
    _STATE.default_connection = conn_name
    _set_result(ctx.dd, {}, None)

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
        name = _get_conn_name({})
    try:
        _CONNECTIONS.disconnect(name)
    finally:
        if name == _STATE.default_connection: _STATE.default_connection = None

@bound_ops("Ldap-Search")
def execute_search(ctx: ExecContext, statement: Tree) -> None:
    """
**Perform an LDAP search**

* Ldap Search<br>
  <em>Base "Is"i? _base_<br>
  <em>Scope "Is"i? _scope_<br>
  <em>Query "Is"i? _query_<br>
  <em>Giving _variable_<br>
  <em>Using [Connection] _connection_name_<br>

All items are optional except for _query_.

"""
    # TODO

def _resolve_str_arg(ctx: ExecContext, expr: Tree, name: str, allow_none: bool=False) -> str:
    rc = ctx.eval_expr_or_const(expr)
    if rc is None and allow_none: return None
    if not isinstance(rc, str): raise TypeError(f'{name} must be a string; found {_type_str(rc)}')
    return rc

def _set_result(ctx: ExecContext, args: dict, data: Any) -> dict:
    """Sees if the user wants to put the results in a custom location or store in the default location"""
    path = _DEFAULT_RESULT_PATH
    if _RESULT_ARG in args:
        path = args[_RESULT_ARG]
        # They can always restate the default
        # and if they do, we dont check immutability/protection
        # TODO This late check prevents us from doing good error reporting
        if path != _DEFAULT_RESULT_PATH:
            ctx.dd.validate_user_set_path(*path)
    do_set(ctx, data, *path)
    return data

def _get_conn_name(args: dict) -> str:
    """If the args doesn't contain the connection, use the default one"""
    _STATE.default_connection =_get_arg(args, _USING_ARG, str, True) or _STATE.default_connection or _DEFAULT_CONN_NAME
    return _STATE.default_connection

def _get_arg(args: dict, name: str, expected_type: type, optional: bool = False) -> Any:
    """Retrieve a typed value from args or raise if missing or wrong type."""
    if name not in args:
        if optional: return None
        raise ValueError(f'Missing required argument: {name.title()}')
    value = args[name]
    if isinstance(value, expected_type): return value
    raise TypeError(f'Argument {name.title()} must be of type {type_str(expected_type)}, found {_type_str(value)}')

def _normalize_scope(value: str) -> str:
    """
    Normalize a user-supplied scope string to ldap3's canonical constants.

    Accepted synonyms (case-insensitive):
        - 'base'                  -> BASE
        - 'level', 'one'          -> LEVEL
        - 'subtree', 'sub', 'all' -> SUBTREE

    Returns:
        The ldap3 constant (BASE, LEVEL, SUBTREE)
    """
    if value:
        v = value.strip().lower()
        if v in ('base',): return BASE
        if v in ('level', 'one'): return LEVEL
        if v in ('subtree', 'sub', 'all'): return SUBTREE
    return BASE

def _normalize_auth_type(value: str) -> str:
    """
    Normalize a user-supplied authentication type string to ldap3's canonical constants.

    Accepted synonyms (case-insensitive):
        - 'anon', 'anonymous'        -> ANONYMOUS
        - 'simple', 'user', 'bind'   -> SIMPLE
        - 'ntlm', 'windows', 'sspi'  -> NTLM

    Returns:
        The ldap3 constant (ANONYMOUS, SIMPLE, NTLM)
    """
    if value:
        v = value.strip().lower()
        if v in ('anon', 'anonymous'): return ANONYMOUS
        if v in ('simple', 'user', 'bind'): return SIMPLE
        if v in ('ntlm', 'windows', 'sspi'): return NTLM
    return SIMPLE
