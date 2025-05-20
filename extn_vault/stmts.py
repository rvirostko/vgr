"""
Implementations of Vault Statements
"""

from pathlib import Path
from typing import Any
import sys

from lark import Tree, Token

from evaluate import eval_expr

# HACK: Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# pylint: disable=wrong-import-position
from data_dict import DataDictionary
from redir import print_stderr, shorten
from vault_api.client_mgr import VaultClientManager
# pylint: enable=wrong-import-position

from .dd_consts import DEFAULT_NS_PATH, DEFAULT_RESULT_PATH, DEFAULT_CONN_PATH

_NS_ARG = 'namespace'
_RESULT_ARG = 'result'
_USING_ARG = 'using'
_META_ARG = 'metadata'
_KEY_ARG = 'key'
_CONFIG_ARG = 'config'
_DATA_ARG = 'data'
_TYPE_ARG = 'type'
_DESC_ARG = 'description'
_VERSION_ARG = 'version'
_ARG_VAR_NAME = (_RESULT_ARG,)
_ARG_INT_EXPR = (_VERSION_ARG,)
_ARG_EXPR = (_DESC_ARG, _KEY_ARG, _NS_ARG, _TYPE_ARG, _CONFIG_ARG, _DATA_ARG, _META_ARG, _USING_ARG)

_DEFAULT_CONN_NAME = 'DefaultConnection'

_CONNECTIONS = VaultClientManager()

def _do_set(dd: DataDictionary, value: Any, *path) -> Any:
    new_value = dd.set_var(value, *path)
    if dd.verbose:
        print_stderr('Set', '.'.join(path), 'To', shorten(repr(new_value)))
    return new_value

def _get_default_ns(dd: DataDictionary, args: dict) -> str:
    """If the args doesn't contain the namespace, use the default one"""
    return _get_arg(args, _NS_ARG, str, True) or dd.get_var(*DEFAULT_NS_PATH)

def _set_result(dd: DataDictionary, args: dict, data: Any) -> dict:
    """Sees if the user wants to put the results in a custom location or store in the default location"""
    path = DEFAULT_RESULT_PATH
    if _RESULT_ARG in args:
        path = args[_RESULT_ARG]
        # They can always restate the default
        # and if they do, we dont check immutability/protection
        if path != DEFAULT_RESULT_PATH:
            dd.validate_user_set_path(*dd.validate_user_path(*path))
    return _do_set(dd, data, *path)

def _set_default_conn(dd: DataDictionary, conn: str) -> str:
    # Only change the DD value if we have to,
    # so as to skip a message when verbose is on
    curr = dd.get_var(*DEFAULT_CONN_PATH)
    if curr != conn: _do_set(dd, conn, *DEFAULT_CONN_PATH)
    return conn

def _get_default_conn(dd: DataDictionary, args: dict) -> str:
    """If the args doesn't contain the connection, use the default one"""
    return _get_arg(args, _USING_ARG, str, True) or dd.get_var(*DEFAULT_CONN_PATH) or _DEFAULT_CONN_NAME

# Vault Connect -- values from env, default name
# Vault Connect To "http://127.0.0.1"
# Vault Connect To "http://127.0.0.1" With "<token>"
# Vault Connect To "http://127.0.0.1" With "<token>" As "Source"
# Vault Connect As "Source" To "http://127.0.0.1", Token="<token>"
def execute_connect(dd: DataDictionary, statement: Tree) -> None:
    addr = token = conn_name = None
    for child in statement.children:
        if isinstance(child, Tree):
            name: str = child.data
            if name == 'conn_addr':
                addr = _resolve_str_arg(dd, child.children[0], 'Vault Address')
            elif name == 'conn_token':
                token = _resolve_str_arg(dd, child.children[0], 'Vault Token')
            elif name == 'conn_name':
                conn_name = _resolve_str_arg(dd, child.children[0], 'Vault Connection Name')
            else:
                raise NotImplementedError(f'Argument f{repr(name)} not handled') # SNO
        else:
            raise ValueError(f'Unexpected Vault argument {repr(child)}') # SNO
    conn_name = conn_name or _DEFAULT_CONN_NAME
    _CONNECTIONS.connect(conn_name, addr, token)
    _set_default_conn(dd, conn_name)
    _set_result(dd, {}, None)

# Vault Disconnect
# Vault Disconnect "Source"
def execute_disconnect(dd: DataDictionary, statement: Tree) -> None:
    if statement.children:
        name = _resolve_str_arg(dd, statement.children[0], 'Vault Connection Name')
    else:
        name = _get_default_conn(dd, {})
    _CONNECTIONS.disconnect(name)
    _set_result(dd, {}, None)

# Vault DefaultNamespace ""
# Vault DefaultNamespace "D111382"
# Vault DefaultNamespace "D111382/One"
# -- Need to check handling of leading and trailing /s
def execute_default_ns(dd: DataDictionary, statement: Tree) -> None:
    args: dict = _extract_args(dd, statement)
    _allowed_args(args, _RESULT_ARG)
    ns: str = _resolve_str_arg(dd, statement.children[0], 'Default Namespace', True)
    _do_set(dd, '' if ns is None or ns.isspace() else ns.strip(), *DEFAULT_NS_PATH)
    _set_result(dd, args, None)

# Vault CreateNamespace "D111382"
# Vault CreateNamespace "D111382", Namespace=""
# Vault CreateNamespace "One", Namespace="D111382"
# Vault CreateNamespace "SubOne", Namespace="D111382/One"
# Vault CreateNamespace "D111382/One/SubOne" -- Allowed if only the parents exist
def execute_create_ns(dd: DataDictionary, statement: Tree) -> None:
    args: dict = _extract_args(dd, statement)
    _allowed_args(args, _NS_ARG, _META_ARG, _RESULT_ARG, _USING_ARG)
    new_namespace: str = _resolve_str_arg(dd, statement.children[0], 'New Namespace')
    parent_namespace: str = _get_default_ns(dd, args)
    metadata = args.get(_META_ARG)
    using = _set_default_conn(dd, _get_default_conn(dd, args))
    _set_result(dd,
                args,
                _CONNECTIONS.get_connection(using).create_namespace(new_namespace, metadata, parent_namespace)
               )

# See list for tests
def execute_read_ns(dd: DataDictionary, statement: Tree) -> None:
    args: dict = _extract_args(dd, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    ns: str = _resolve_str_arg(dd, statement.children[0], 'Namespace')
    parent_namespace: str = _get_default_ns(dd, args)
    using = _set_default_conn(dd, _get_default_conn(dd, args))
    _set_result(dd,
                args,
                _CONNECTIONS.get_connection(using).read_namespace(ns, parent_namespace)
               )

# See list for tests
def execute_update_ns(dd: DataDictionary, statement: Tree) -> None:
    args: dict = _extract_args(dd, statement)
    _allowed_args(args, _NS_ARG, _META_ARG, _RESULT_ARG, _USING_ARG)
    ns: str = _resolve_str_arg(dd, statement.children[0], 'Namespace')
    parent_namespace: str = _get_default_ns(dd, args)
    metadata = args.get(_META_ARG)
    using = _set_default_conn(dd, _get_default_conn(dd, args))
    _set_result(dd,
                args,
                _CONNECTIONS.get_connection(using).update_namespace(ns, metadata, parent_namespace)
               )

# See list for tests
def execute_delete_ns(dd: DataDictionary, statement: Tree) -> None:
    args: dict = _extract_args(dd, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    ns: str = _resolve_str_arg(dd, statement.children[0], 'Namespace')
    parent_namespace: str = _get_default_ns(dd, args)
    using = _set_default_conn(dd, _get_default_conn(dd, args))
    _set_result(dd,
                args,
                _CONNECTIONS.get_connection(using).delete_namespace(ns, parent_namespace)
               )

# NB: for testing, need to be able to list the root as well
#     a top-level NS, and a child NS
#     Vault ListNamespaces
#     Vault ListNamespaces ""
#     Vault ListNamespaces "D111382"
#     Vault ListNamespaces Namespace="D111382"
#     Vault ListNamespaces "D111382", Namspace=""
#     Vault ListNamespaces "One", Namspace="D111382"
#     Vault ListNamespaces "SubOne", Namspace="D111382/One"
#     Vault ListNamespaces "D111382/One/SubOne" -- allowed?
def execute_list_ns(dd: DataDictionary, statement: Tree) -> None:
    namespace: str = _resolve_str_arg(dd, statement.children[0], 'Namespace', True) if len(statement.children) > 1 else ""
    args: dict = _extract_args(dd, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    parent_namespace: str = _get_default_ns(dd, args)
    using = _set_default_conn(dd, _get_default_conn(dd, args))
    _set_result(
        dd,
        args,
        _CONNECTIONS.get_connection(using).list_namespace(_combine_ns(parent_namespace, namespace))
    )

def execute_lock_ns(dd: DataDictionary, statement: Tree) -> None:
    args: dict = _extract_args(dd, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _resolve_str_arg(dd, statement.children[0], 'Namespace')
    parent_namespace: str = _get_default_ns(dd, args)
    using = _set_default_conn(dd, _get_default_conn(dd, args))
    _set_result(
        dd,
        args,
        _CONNECTIONS.get_connection(using).lock_namespace(_combine_ns(parent_namespace, namespace))
    )

def execute_unlock_ns(dd: DataDictionary, statement: Tree) -> None:
    args: dict = _extract_args(dd, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG, _KEY_ARG)
    namespace: str = _resolve_str_arg(dd, statement.children[0], 'Namespace')
    parent_namespace: str = _get_default_ns(dd, args)
    using = _set_default_conn(dd, _get_default_conn(dd, args))
    _set_result(
        dd,
        args,
        _CONNECTIONS.get_connection(using).unlock_namespace(_combine_ns(parent_namespace, namespace), args.get(_KEY_ARG))
    )

def execute_create_mount(dd: DataDictionary, statement: Tree) -> None:
    mount_point = _resolve_str_arg(dd, statement.children[0], 'Mount Point')
    args = _extract_args(dd, statement)
    data = {}
    # If Data=... specified, it means it contains all the config info
    # and piecemeal construction is not permitted
    if _DATA_ARG in args:
        _allowed_args(args, _DATA_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
        data = _get_arg(args, _DATA_ARG, dict)
    else:
        # If no data, then at least Type=... must be provided
        # Description and Config are optional
        _allowed_args(args, _DESC_ARG, _TYPE_ARG, _CONFIG_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
        mtype: str = _get_arg(args, _TYPE_ARG, str).lower()
        if mtype.startswith('kv'):
            data['options'] = { 'version': 1 if mtype == 'kv1' else 2 }
            data['type'] = 'kv'
        else:
            data['type'] = mtype
        desc = _get_arg(args, _DESC_ARG, str, True)
        if desc: data['description'] = desc
        config = _get_arg(args, _CONFIG_ARG, dict, True)
        if config: data['config'] = config
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    using = _set_default_conn(dd, _get_default_conn(dd, args))
    _set_result(dd,
                args,
                _CONNECTIONS.get_connection(using).create_mount(mount_point, data, namespace))

def execute_read_mount(dd: DataDictionary, statement: Tree) -> None:
    mount_point = _resolve_str_arg(dd, statement.children[0], 'Mount Point')
    args = _extract_args(dd, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    using = _set_default_conn(dd, _get_default_conn(dd, args))
    _set_result(dd,
                args,
                _CONNECTIONS.get_connection(using).read_mount(mount_point, namespace))

def execute_update_mount(dd: DataDictionary, statement: Tree) -> None:
    mount_point = _resolve_str_arg(dd, statement.children[0], 'Mount Point')
    args = _extract_args(dd, statement)
    data = {}
    # Config and Data are synonymous, but you can't have both
    if _DATA_ARG in args:
        _allowed_args(args, _DATA_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
        data = _get_arg(args, _DATA_ARG, dict)
    else:
        _allowed_args(args, _CONFIG_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
        data = _get_arg(args, _CONFIG_ARG, dict)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    using = _set_default_conn(dd, _get_default_conn(dd, args))
    _set_result(dd,
                args,
                _CONNECTIONS.get_connection(using).update_mount(mount_point, data, namespace))

def execute_delete_mount(dd: DataDictionary, statement: Tree) -> None:
    mount_point = _resolve_str_arg(dd, statement.children[0], 'Mount Point')
    args = _extract_args(dd, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    using = _set_default_conn(dd, _get_default_conn(dd, args))
    _set_result(dd,
                args,
                _CONNECTIONS.get_connection(using).delete_mount(mount_point, namespace))

def execute_list_mounts(dd: DataDictionary, statement: Tree) -> None:
    args = _extract_args(dd, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _resolve_str_arg(dd, statement.children[0], 'Namespace', True) if len(statement.children) > 1 else ""
    using = _set_default_conn(dd, _get_default_conn(dd, args))
    _set_result(dd,
                args,
                _CONNECTIONS.get_connection(using).list_mounts(namespace))

def execute_create_kv_secret(dd: DataDictionary, statement: Tree) -> None:
    """For create, Data is required but Metadata is optional"""
    mount_point, path = _split_mount_path(_resolve_str_arg(dd, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(dd, statement)
    _allowed_args(args, _DATA_ARG, _META_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    using = _set_default_conn(dd, _get_default_conn(dd, args))
    data = _get_arg(args, _DATA_ARG, dict) if _DATA_ARG in args else {}
    _set_result(dd,
                args,
                _CONNECTIONS.get_connection(using).create_kv2_secret(mount_point, path, data, namespace))
    # TODO return on error
    if _META_ARG in args:
        metadata = _get_arg(args, _META_ARG, dict)
        _set_result(dd,
                    args,
                    _CONNECTIONS.get_connection(using).create_kv_metadata(mount_point, path, metadata, namespace))

def execute_read_kv_secret(dd: DataDictionary, statement: Tree) -> None:
    mount_point, path = _split_mount_path(_resolve_str_arg(dd, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(dd, statement)
    _allowed_args(args, _VERSION_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    version: int = _get_arg(args, _VERSION_ARG, int, True)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    using = _set_default_conn(dd, _get_default_conn(dd, args))
    _set_result(dd,
                args,
                _CONNECTIONS.get_connection(using).read_kv2_secret(mount_point, path, version, namespace))

def execute_read_kv_metadata(dd: DataDictionary, statement: Tree) -> None:
    mount_point, path = _split_mount_path(_resolve_str_arg(dd, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(dd, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    using = _set_default_conn(dd, _get_default_conn(dd, args))
    _set_result(dd,
                args,
                _CONNECTIONS.get_connection(using).read_kv2_metadata(mount_point, path, namespace))

def execute_update_kv_secret(dd: DataDictionary, statement: Tree) -> None:
    """Data and Metadata are optional"""
    mount_point, path = _split_mount_path(_resolve_str_arg(dd, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(dd, statement)
    _allowed_args(args, _DATA_ARG, _META_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    using = _set_default_conn(dd, _get_default_conn(dd, args))
    _set_result(dd, args, None) # in case neither data or metada is provides
    if _DATA_ARG in args:
        data = _get_arg(args, _DATA_ARG, dict)
        _set_result(dd,
                    args,
                    _CONNECTIONS.get_connection(using).update_kv2_secret(mount_point, path, data, namespace))
        # TODO return on error
    if _META_ARG in args:
        metadata = _get_arg(args, _META_ARG, dict)
        _set_result(dd,
                    args,
                    _CONNECTIONS.get_connection(using).update_kv2_metadata(mount_point, path, metadata, namespace))

def execute_patch_kv_secret(dd: DataDictionary, statement: Tree) -> None:
    """Data and Metadata are optional"""
    mount_point, path = _split_mount_path(_resolve_str_arg(dd, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(dd, statement)
    _allowed_args(args, _DATA_ARG, _META_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    using = _set_default_conn(dd, _get_default_conn(dd, args))
    _set_result(dd, args, None) # in case neither data or metada is provides
    if _DATA_ARG in args:
        data = _get_arg(args, _DATA_ARG, dict)
        _set_result(dd,
                    args,
                    _CONNECTIONS.get_connection(using).patch_kv2_secret(mount_point, path, data, namespace))
        # TODO return on error
    if _META_ARG in args:
        metadata = _get_arg(args, _META_ARG, dict)
        _set_result(dd,
                    args,
                    _CONNECTIONS.get_connection(using).patch_kv2_metadata(mount_point, path, metadata, namespace))

def execute_delete_kv_secret(dd: DataDictionary, statement: Tree) -> None:
    value = eval_expr(dd, statement.children[0])
    print(value)

def execute_list_kv_secrets(dd: DataDictionary, statement: Tree) -> None:
    value = eval_expr(dd, statement.children[0])
    print(value)

def execute_create_ldap_lib(dd: DataDictionary, statement: Tree) -> None:
    value = eval_expr(dd, statement.children[0])
    print(value)

def execute_read_ldap_lib(dd: DataDictionary, statement: Tree) -> None:
    value = eval_expr(dd, statement.children[0])
    print(value)

def execute_update_ldap_lib(dd: DataDictionary, statement: Tree) -> None:
    value = eval_expr(dd, statement.children[0])
    print(value)

def execute_delete_ldap_lib(dd: DataDictionary, statement: Tree) -> None:
    value = eval_expr(dd, statement.children[0])
    print(value)

def execute_list_ldap_libs(dd: DataDictionary, statement: Tree) -> None:
    value = eval_expr(dd, statement.children[0])
    print(value)

def execute_create_ldap_secret(dd: DataDictionary, statement: Tree) -> None:
    value = eval_expr(dd, statement.children[0])
    print(value)

def execute_read_ldap_secret(dd: DataDictionary, statement: Tree) -> None:
    value = eval_expr(dd, statement.children[0])
    print(value)

def execute_update_ldap_secret(dd: DataDictionary, statement: Tree) -> None:
    value = eval_expr(dd, statement.children[0])
    print(value)

def execute_delete_ldap_secret(dd: DataDictionary, statement: Tree) -> None:
    value = eval_expr(dd, statement.children[0])
    print(value)

def execute_list_ldap_secrets(dd: DataDictionary, statement: Tree) -> None:
    value = eval_expr(dd, statement.children[0])
    print(value)

def execute_rotate_ldap_secret(dd: DataDictionary, statement: Tree) -> None:
    value = eval_expr(dd, statement.children[0])
    print(value)

# TODO may need to clean up duped slashes etc
def _combine_ns(parent: str, child: str) -> str:
    """Combine parent and child namespace paths into a single path."""
    parent = (parent or '').strip('/')
    child = (child or '').strip('/')
    if not parent and not child: return ''
    if not parent: return child
    if not child: return parent
    return f'{parent}/{child}'

def _split_mount_path(s: str) -> tuple:
    s = '/'.join(filter(None, s.split('/')))
    parts = s.split('/', 1)
    if len(parts) != 2:
        raise ValueError(f'Missing Path in {s}')
    return parts

def _extract_args(dd: DataDictionary, statement: Tree) -> dict:
    args = {}
    for child in statement.children[-1].children:
        if isinstance(child, Tree) and child.data.startswith('vopt_'):
            arg_name = child.data[5:]
            arg_node = child.children[0]
            if arg_name in _ARG_VAR_NAME:
                args[arg_name] = tuple(name.value for name in arg_node.children)
            elif arg_name in _ARG_INT_EXPR:
                v = _resolve_arg_value(dd, arg_node)
                if v:
                    if not isinstance(v, (int, float)): raise TypeError(f'{arg_name.title()} must be a int; found {repr(type(v).__name__)}')
                    args[arg_name] = int(v)
            elif arg_name in _ARG_EXPR:
                args[arg_name] = _resolve_arg_value(dd, arg_node)
            else:
                raise NotImplementedError(f'Vault argument {repr(arg_name)} not implemented') # SNO
        else:
            raise ValueError(f'Unexpected Vault argument {repr(child.data)}:{type(child)}') # SNO
    return args

def _resolve_str_arg(dd: DataDictionary, expr: Tree, name: str, allow_none: bool=False) -> str:
    rc = _resolve_arg_value(dd, expr)
    if rc is None and allow_none: return None
    if not isinstance(rc, str): raise TypeError(f'{name} must be a string; found {repr(type(rc).__name__)}')
    return rc

def _resolve_arg_value(dd: DataDictionary, node):
    """
    This lets values be unquoted as arguments.
    For example it allows
        Vault CreateMount secrets Type is KV2
    to be interchangabe with
        Vault CreateMount "secrets" Type is "KV2"
    _if_ secrets and KV2 are not defined in the data dictionary
    """
    if isinstance(node, Tree) and node.data == "var_ref":
        if len(node.children) == 1 and isinstance(node.children[0], Token) and node.children[0].type == "NAME":
            name = node.children[0].value
            exists, value = dd.exists(name)
            return value if exists else name
    return eval_expr(dd, node)

def _allowed_args(args: dict, *allowed_keys) -> None:
    """Raise an error if any key in args is not in allowed_keys."""
    for key in args:
        if key not in allowed_keys:
            raise ValueError(f'Unexpected argument: {key.title()}')

def _get_arg(args: dict, name: str, expected_type: type, optional: bool = False) -> Any:
    """Retrieve a typed value from args or raise if missing or wrong type."""
    if name not in args:
        if optional: return None
        raise ValueError(f'Missing required argument: {name.tile()}')
    value = args[name]
    if isinstance(value, expected_type): return value
    raise TypeError(f'Argument {name.title()} must be of type {repr(expected_type.__name__)}, found {repr(type(value).__name__)}')
