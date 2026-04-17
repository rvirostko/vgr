"""
Implementations of LDAP Statements
"""

from typing import Any
import os

from lark import Tree
from ldap3 import ANONYMOUS, SIMPLE, NTLM, BASE, LEVEL, SUBTREE, ALL_ATTRIBUTES, NO_ATTRIBUTES, DEREF_ALWAYS, DEREF_NEVER
from ..app_exceptions import VgrRuntimeError
from ..builtins import (
    bound_ops,
    poly_bool,
    poly_int,
    poly_isempty,
    poly_list,
    poly_str,
    poly_strip,
    poly_type,
)
from ..data_dict import DataDictionary, DynamicValue
from ..evaluate import (
    _var_name_path,
    do_set,
    get_writable_var_path,
)
from ..exec_context import ExecContext

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

@bound_ops("Ldap Connect")
def execute_connect(ctx: ExecContext, statement: Tree) -> None:
    """
**Establish an LDAP connection**

* Ldap Connect\\
  &emsp;&emsp;To *url*\\
  &emsp;&emsp;[Auth | Authentication] [Is] *auth_type*\\
  &emsp;&emsp;User [Is] *user*\\
  &emsp;&emsp;Password [Is] *password*\\
  &emsp;&emsp;Read Only [[Is] *read_only*]\\
  &emsp;&emsp;[Return] Empty [Attrs | Attributes] [[Is] *empty_attrs*]\\
  &emsp;&emsp;Time Limit [[Is] *time_limit*]\\
  &emsp;&emsp;Page Size [[Is] *page_size*]\\
  &emsp;&emsp;As *connection_name*

If *url* is omitted then *LDAP_URL*, if defined, is used.
Likewise, environment variables *LDAP_BIND_DN* and *LDAP_PASSWORD* are used
if *user* and *password* are omitted and *auth_type* is `Simple`.

The values for *read_only* and *empty_attrs* are booleans. If the option
is present but no value is provided, the default value is `True`.

The values for *time_limit* and *page_size* are both integers, reflecting
the default maximum operation time in seconds and the default blocking
for retrieved data respectively. Both can be changed on a per operation
basis when applicable.

The value for *auth_type* is a string which must be one of

* `Anonymous` - no authentication required
* `Simple` - user/password authentication. This is the default.
* `Ntlm` - Uses Windows authentication

If *connection_name* is omitted, a default name is used.
This name, or default, becomes the value of _term.connection_.

```vgr
Ldap Connect To "ldaps://main.corp.org"
    User Is corp_dn
    Password Is corp_psw
    As "ldap_corp"
Exhibit ldap.connection → ldap.connection = "ldap_corp"
```
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

@bound_ops("Ldap Disconnect")
def execute_disconnect(ctx: ExecContext, statement: Tree) -> None:
    """
**Disconnect from LDAP**

* Ldap Disconnect
* Ldap Disconnect [From] *connection_name*

The *connection_name* must have been created by a previous `Ldap Connect`.
If no name is provided, the default name is used.

```vgr
Exhibit ldap.connection → ldap.connection = "ldap_corp"
Ldap Disconnect
Exhibit ldap.connection → ldap.connection = None
```
"""
    if statement.children:
        name = _resolve_str_arg(ctx, statement, 'Connection Name')
    else:
        name = _STATE.default_connection or _DEFAULT_CONN_NAME
    try:
        _CONNECTIONS.disconnect(name)
    finally:
        if name == _STATE.default_connection: _STATE.default_connection = None
        do_set(ctx, None, *_DEFAULT_GIVING_PATH)

@bound_ops("Ldap Search")
def execute_search(ctx: ExecContext, statement: Tree) -> None:
    """
**Perform an LDAP search**

* Ldap Search\\
  &emsp;&emsp;Base [Is] *base*\\
  &emsp;&emsp;Scope [Is] *scope*\\
  &emsp;&emsp;Filter [Is] *filter*\\
  &emsp;&emsp;Attributes [Is | Are] *attributes*\\
  &emsp;&emsp;Time Limit [[Is] *time_limit*]\\
  &emsp;&emsp;Page Size [[Is] *page_size*]\\
  &emsp;&emsp;Dereference Aliases [[Is] *deref_aliases*]\\
  &emsp;&emsp;Get Operational [Attributes | Attrs] [[Is] *op_attrs*]\\
  &emsp;&emsp;Giving *variable*\\
  &emsp;&emsp;Using [Connection] *connection_name*

All items are optional except for *base*.

The *attributes* to be retrieved are specified as `All`, `None`, or a list of string names.
If no attributes are defined, all available attributes, as defined by the LDAP server, are returned.

In addition, the `DN` attribute is added to all retrieved values, even if none of the requested
attributes had a value.

The values for *time_limit* and *page_size* are both integers, reflecting
the maximum operation time in seconds and the blocking
for retrieved data respectively. Defaults are inherited from the connection.

The values for *deref_aliases* and *op_attrs* are booleans. If a value
is not provided for the argument, it default to `True`. Setting *deref_aliases*
cause the search to proceed across aliases in the LDAP tree.
The *op_attrs* option must be set to `True` to retrieve operational
attributes such as Active Directory's *whenCreated* or *whenChanged*
attributes.

The value for *scope* is a string which must be one of

* `Base` - the search target is *base*
* `Level` or `One` - the objects that are immediately under *base* are searched. This is the default.
* `All` or `Subtree` - A full subtree search is performed

If the `Giving` argument is used, it must reference a user writeable variable.
On completion, this variable will have the following items set

* *variable*.success - a boolean indicating if the search succeeded or not. Not finding any
  item _is not_ considered an error.
* *variable*.result_code - an LDAP specific error code, with zero meaning no errors
* *variable*.error - a human readable description of an error, if any
* *variable*.entries - a list of the retrieved values.
  Note that when *size_limit* is set to one, the wrapping list is omitted.

If the `Giving` argument is omited, results are stored in *ldap.result*

```vgr
// See https://www.forumsys.com/2022/05/10/online-ldap-test-server/
Set formsys.url To "ldap://ldap.forumsys.com"
Set formsys.user To "cn=read-only-admin,dc=example,dc=com"
Set formsys.psw To "password"
Set formsys.base To "dc=example,dc=com"

Ldap Connect To formsys.url
    User Is formsys.user
    Password Is formsys.psw

Set filter To "objectClass".LdapAttrEquals("groupOfUniqueNames")
Ldap Search
    Base Is formsys.base
    Filter Is filter
    Attributes Are ["ou", "uniqueMember"]
    Scope Is ALL
    Giving groups
Assert groups.success : "Failed to get groups: {} (rc={})", groups.error, groups.result_code
Sort groups.entries By ou
Select ou.TitleCase() As "Group",
    uniqueMember.Length() As "Members",
    dn As "DN"
    From groups.entries
    For Batch Template
```

Also see-

* `LdapAttrGE()` - Generate a filter for greater-than or equal-to comparison of an attribute
* `LdapAttrLE()` - Generate a filter for less-than or equal-to comparison of an attribute
* `LdapEscape()` - Escape special characters in an LDAP filter value
* `LdapFilterOr()` - Combine two or more LDAP filter expressions with a logical OR
* `ToLdapFilter()` - Converts a dictionary to a query-by-example filter
* `LdapFilterAnd()` - Combine two or more LDAP filter expressions with a logical AND
* `LdapFilterNot()` - Negate an LDAP filter expression
* `LdapAttrEquals()` - Generate a filter for equality of an attribute with one or more values
* `LdapAttrExists()` - Generate a filter for an attribute having any value

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
    raise VgrRuntimeError(expr, TypeError(f'{name} must be a number; found {poly_type(rc)!r}'))

def _resolve_str_arg(ctx: ExecContext, opt: Tree, name: str, allow_none: bool=False) -> str:
    expr = opt.children[0]
    rc = ctx.eval_expr_or_const(expr)
    if rc is None and not allow_none: raise VgrRuntimeError(expr, ValueError(f'{name} cannot be None'))
    if isinstance(rc, str):
        # NB: if you use "expr" instead of "opt" it can't seem to find the index!
        if poly_isempty(rc) and not allow_none: raise VgrRuntimeError(opt, ValueError(f'{name} cannot be blank'))
        return rc
    raise VgrRuntimeError(expr, TypeError(f'{name} must be a string; found {poly_type(rc)!r}'))

def _resolve_opt_str_arg(ctx: ExecContext, opt: Tree, name: str) -> str:
    """Allows for a None result"""
    return _resolve_str_arg(ctx, opt, name, True)

def _resolve_bool_arg(ctx: ExecContext, opt: Tree, name: str) -> bool:
    expr = opt.children[0]
    rc = ctx.eval_expr_or_const(expr)
    if rc is None: return False
    if isinstance(rc, (dict, list)): raise VgrRuntimeError(expr, TypeError(f'{name} must be a boolean; found {poly_type(rc)!r}'))
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
    value = _resolve_str_arg(ctx, opt, name, True)
    if value is None: return BASE
    v = value.strip().lower()
    if v in ('base', ''): return BASE
    if v in ('level', 'one'): return LEVEL
    if v in ('subtree', 'sub', 'all'): return SUBTREE
    raise VgrRuntimeError(opt, ValueError(f'{name} {value!r} is invalid'))

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
    value = _resolve_str_arg(ctx, opt, name, True)
    if value is None: return SIMPLE
    v = value.strip().lower()
    if v in ('simple', 'user', 'bind', ''): return SIMPLE
    if v in ('anon', 'anonymous'): return ANONYMOUS
    if v in ('ntlm', 'windows', 'sspi'): return NTLM
    raise VgrRuntimeError(opt, ValueError(f'{name} {value!r} is invalid'))

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
                raise VgrRuntimeError(expr, TypeError(f'{name} can contain only strings; found {poly_type(rc)!r}'))
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
    _CONN_NAME_ARG:             ('Connection Name',            _resolve_str_arg),
    _GIVING_ARG:                ('Giving',                     _resolve_giving_arg),
    _USING_ARG:                 ('Using',                      _resolve_opt_str_arg),
    'attributes':               ('Attributes',                 _resolve_attrs_arg),
    'authentication':           ('Authentication',             _resolve_auth_arg),
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
            raise VgrRuntimeError(opt, ValueError(f'Unexpected Ldap argument {opt.data!r}:{poly_type(opt)!r}')) # SNO
        arg_name = opt.data[5:]
        if arg_name not in _OPT_HANDLER:
            raise VgrRuntimeError(opt, NotImplementedError(f'Ldap argument {arg_name!r} not implemented')) # SNO
        name, handler = _OPT_HANDLER[arg_name]
        args[arg_name] = handler(ctx, opt, name)
    return args
