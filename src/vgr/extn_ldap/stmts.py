"""
Implementations of LDAP Statements
"""

from typing import Any
import os

from lark import Tree

from ..app_exceptions import VgrRuntimeError
from ..exec_context import ExecContext
from ..data_dict import DataDictionary

from .dd_consts import DEFAULT_CONN_PATH, DEFAULT_RESULT_PATH
from .ldap_client import LdapClient, LdapClientManager

_DEFAULT_CONN_NAME = 'DefaultConnection'

_CONNECTIONS = LdapClientManager()

def _type_str(o: Any) -> str:
    return repr(type(o).__name__)

def _do_set(dd: DataDictionary, value: Any, *path) -> Any:
    new_value = dd.set_var(value, *path)
    ## FUTURE print verbose via ctx
    return new_value

def _set_result(dd: DataDictionary, args: dict, data: Any) -> dict:
    """Sees if the user wants to put the results in a custom location or store in the default location"""
    path = DEFAULT_RESULT_PATH
# TODO
#    if _RESULT_ARG in args:
#        path = args[_RESULT_ARG]
        # They can always restate the default
        # and if they do, we dont check immutability/protection
#        if path != DEFAULT_RESULT_PATH:
#            dd.validate_user_set_path(*dd.validate_user_path(*path))
    return _do_set(dd, data, *path)

def _set_default_conn(dd: DataDictionary, conn: str) -> str:
    # Only change the DD value if we have to,
    # so as to skip a message when verbose is on
    curr = dd.get_var(*DEFAULT_CONN_PATH)
    if curr != conn: _do_set(dd, conn, *DEFAULT_CONN_PATH)
    return conn

def _get_default_conn(dd: DataDictionary) -> str:
    return dd.get_var(*DEFAULT_CONN_PATH) or _DEFAULT_CONN_NAME

def add_dd_constants(dd: DataDictionary, prefix: str) -> None:
    _do_set(dd, None, *DEFAULT_CONN_PATH)
    _do_set(dd, None, *DEFAULT_RESULT_PATH)
# TODO something
#    for name, value in vars(TermConsts).items():
#        if not name.startswith("__"): dd.set_var(value, prefix, name.lower())
    pass

from ldap3 import ANONYMOUS, SIMPLE, NTLM

def _normalize_auth_type(value: str):
    """
    Normalize a user-supplied authentication type string to ldap3's canonical constants.

    Accepted synonyms (case-insensitive):
        - 'anon', 'anonymous'        -> ANONYMOUS
        - 'simple', 'user', 'bind'   -> SIMPLE
        - 'ntlm', 'windows', 'sspi'  -> NTLM

    Returns:
        The ldap3 constant (ANONYMOUS, SIMPLE, NTLM), or None if not recognized.
    """
    if value:
        v = value.strip().lower()
        if v in ('anon', 'anonymous'): return ANONYMOUS
        if v in ('simple', 'user', 'bind'): return SIMPLE
        if v in ('ntlm', 'windows', 'sspi'): return NTLM
    return SIMPLE

def execute_connect(ctx: ExecContext, statement: Tree) -> None:
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
    kwargs.setdefault('url', os.environ.get('LDAP_URL'))
    if kwargs['authentication'] == SIMPLE:
        kwargs.setdefault('bind_dn', os.environ.get('LDAP_BIND_DN'))
        kwargs.setdefault('password', os.environ.get('LDAP_PASSWORD'))
    conn_name = conn_name or _DEFAULT_CONN_NAME
    _CONNECTIONS.connect(conn_name, **kwargs)
    _set_default_conn(ctx.dd, conn_name)
    _set_result(ctx.dd, {}, None)

def execute_disconnect(ctx: ExecContext, statement: Tree) -> None:
    default_conn = _get_default_conn(ctx.dd)
    if statement.children:
        name = _resolve_str_arg(ctx, statement.children[0], 'Ldap Connection Name')
    else:
        name = default_conn
    try:
        _CONNECTIONS.disconnect(name)
    finally:
        if name == default_conn: _set_default_conn(ctx.dd, None)
        _set_result(ctx.dd, {}, None)

def execute_search(ctx: ExecContext, statement: Tree) -> None:
    pass

def _resolve_str_arg(ctx: ExecContext, expr: Tree, name: str, allow_none: bool=False) -> str:
    rc = ctx.eval_expr_or_const(expr)
    if rc is None and allow_none: return None
    if not isinstance(rc, str): raise TypeError(f'{name} must be a string; found {_type_str(rc)}')
    return rc
