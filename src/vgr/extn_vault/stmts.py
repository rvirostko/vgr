"""
Implementations of Vault Statements
"""

from typing import Any

from lark import Tree

from ..app_exceptions import VgrRuntimeError
from ..data_dict import DataDictionary, DynamicValue
from ..evaluate import do_set, _var_name_path
from ..exec_context import ExecContext
from ..mathpak import (
    bound_ops,
    poly_int,
    poly_list,
)
from ..vault_api.client_mgr import VaultClientManager

from .functions import extract_kv_data, extract_kv_metadata, add_kv_cas

_CAS_ARG = 'cas'
_CONFIG_ARG = 'config'
_DATA_ARG = 'data'
_DESC_ARG = 'description'
_KEY_ARG = 'key'
_META_ARG = 'metadata'
_NS_ARG = 'namespace'
_RESULT_ARG = 'result'
_TYPE_ARG = 'type'
_USING_ARG = 'using'
_VERSION_ARG = 'version'

# These arguments result in a variable name
_ARG_VAR_NAME = (_RESULT_ARG,)

# These arguments result in an integer value
_ARG_INT_EXPR = (_VERSION_ARG, _CAS_ARG)

# These arguments are expressions -OR- they may be unquoted constants
# treated as strings. This is similar to the way "... AS <name>" is
# defined for Select statements.
_ARG_EXPR = (_DESC_ARG, _KEY_ARG, _NS_ARG, _TYPE_ARG, _CONFIG_ARG, _DATA_ARG, _META_ARG, _USING_ARG)

_DEFAULT_CONN_NAME = 'DefaultConnection'
_VAULT_PREFIX = 'vault'
_DEFAULT_RESULT_PATH = (_VAULT_PREFIX, 'result')

_CONNECTIONS = VaultClientManager()

class ExtnState():
    default_namespace = ''
    default_connection = None

_STATE = ExtnState()

def vault_initialize(dd: DataDictionary) -> None:
    dd.add_immutable_prefix(_VAULT_PREFIX)
    dd.set_var(DynamicValue(lambda : _STATE.default_namespace), _VAULT_PREFIX, 'default_ns')
    dd.set_var(DynamicValue(lambda : _STATE.default_connection), _VAULT_PREFIX, 'connection')
    dd.set_var(None, *_DEFAULT_RESULT_PATH)

@bound_ops("Vault-Connect")
def execute_connect(ctx: ExecContext, statement: Tree) -> None:
    """
**Establish a connection to Vault

* Vault Connect [;]
* Vault Connect To _host_ [;]
* Vault Connect To _host_ With _token_ [;]
* Vault Connect To _host_ With _token_ As _connection_name_ [;]
* Vault Connect As _connection_name_ To _host_, Token Is _token_ [;]

Also see `Vault-Disconnect`
"""
    addr = token = conn_name = None
    for child in statement.children:
        if isinstance(child, Tree):
            name: str = child.data
            if name == 'conn_addr':
                addr = _resolve_str_arg(ctx, child.children[0], 'Vault Address')
            elif name == 'conn_token':
                token = _resolve_str_arg(ctx, child.children[0], 'Vault Token')
            elif name == 'conn_name':
                conn_name = _resolve_str_arg(ctx, child.children[0], 'Vault Connection Name')
            else:
                raise VgrRuntimeError(child, NotImplementedError(f'Argument {name!r} not handled')) # SNO
        else:
            raise VgrRuntimeError(child, ValueError(f'Unexpected Vault argument {child!r}')) # SNO
    conn_name = conn_name or _STATE.default_connection
    _CONNECTIONS.connect(conn_name, addr, token)
    _STATE.default_connection = conn_name
    _set_result(ctx, {}, None)

@bound_ops("Vault-Disconnect")
def execute_disconnect(ctx: ExecContext, statement: Tree) -> None:
    """
**Close a connection to Vault**

* Vault Disconnect [;]
* Vault Disconnect _connection_name_ [;]

Also see `Vault-Connect`
"""
    if statement.children:
        name = _resolve_str_arg(ctx, statement.children[0], 'Vault Connection Name')
    else:
        name = _get_conn_name({})
    try:
        _CONNECTIONS.disconnect(name)
    finally:
        if name == _STATE.default_connection: _STATE.default_connection = None
    _set_result(ctx, {}, None)

#-------------------------------------------------------------------------------
# Generic API execution
#-------------------------------------------------------------------------------

@bound_ops("Vault-ApiDelete")
def execute_api_delete(ctx: ExecContext, statement: Tree) -> None:
    """
**Send a DELETE to a Vault API**

* Vault ApiDelete _path_ [_options_]... [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    url: str = _normalize_path(_resolve_str_arg(ctx, statement.children[0], 'Path'))
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.do_delete(url, namespace))

@bound_ops("Vault-ApiGet")
def execute_api_get(ctx: ExecContext, statement: Tree) -> None:
    """
**Send a GET to a Vault API**

* Vault ApiGet _path_ [_options_]... [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    url: str = _normalize_path(_resolve_str_arg(ctx, statement.children[0], 'Path'))
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.do_get(url, namespace))

@bound_ops("Vault-ApiList")
def execute_api_list(ctx: ExecContext, statement: Tree) -> None:
    """
**Send a LIST to a Vault API**

* Vault ApiList _path_ [_options_]... [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    url: str = _normalize_path(_resolve_str_arg(ctx, statement.children[0], 'Path'))
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.do_list(url, namespace))

@bound_ops("Vault-ApiPatch")
def execute_api_patch(ctx: ExecContext, statement: Tree) -> None:
    """
**Send a PATCH to a Vault API**

* Vault ApiPatch _path_ [_options_]... [;]

_Options_

* Data Is _data_
* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _DATA_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    url: str = _normalize_path(_resolve_str_arg(ctx, statement.children[0], 'Path'))
    data = _get_arg(args, _DATA_ARG, dict, True)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.do_patch(url, data, namespace))

@bound_ops("Vault-ApiPost")
def execute_api_post(ctx: ExecContext, statement: Tree) -> None:
    """
**Send a POST to a Vault API**

* Vault ApiPost _path_ [_options_]... [;]

_Options_

* Data Is _data_
* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _DATA_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    url: str = _normalize_path(_resolve_str_arg(ctx, statement.children[0], 'Path'))
    data = _get_arg(args, _DATA_ARG, dict, True)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.do_post(url, data, namespace))

@bound_ops("Vault-DefaultNamespace")
def execute_default_ns(ctx: ExecContext, statement: Tree) -> None:
    """
**Set the namespace to be used by subsequent requests**

* Vault DefaultNamespace _namespace_ [;]

_Options_

* Giving _variable_
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _RESULT_ARG)
    ns: str = _resolve_str_arg(ctx, statement.children[0], 'Default Namespace', True)
    _STATE.default_namespace = '' if ns is None or ns.isspace() else ns.strip()
    _set_result(ctx, args, None)

@bound_ops("Vault-CreateNamespace")
def execute_create_ns(ctx: ExecContext, statement: Tree) -> None:
    """
**Create a new namesapce**

* Vault CreateNamespace _namespace_ [;]

_Options_

* Metadata Is _meta_
* Namespace Is _parent_
* Using [Connection] _name_
* Giving _variable_
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _META_ARG, _RESULT_ARG, _USING_ARG)
    new_namespace: str = _resolve_str_arg(ctx, statement.children[0], 'New Namespace')
    parent_namespace: str = _get_default_ns(ctx, args)
    metadata = args.get(_META_ARG)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.create_namespace(new_namespace, metadata, parent_namespace))

@bound_ops("Vault-ReadNamespace")
def execute_read_ns(ctx: ExecContext, statement: Tree) -> None:
    """
**Read a namespace**

* Vault ReadNamespace _namespace_ [;]

_Options_

* Namespace Is _parent_
* Using [Connection] _name_
* Giving _variable_
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    ns: str = _resolve_str_arg(ctx, statement.children[0], 'Namespace')
    parent_namespace: str = _get_default_ns(ctx, args)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.read_namespace(ns, parent_namespace))

@bound_ops("Vault-UpdateNamespace")
def execute_update_ns(ctx: ExecContext, statement: Tree) -> None:
    """
**Update a namespace**

* Vault UpdateNamespace _namespace_ Metadata Is _meta_ [;]

_Options_

* Namespace Is _parent_
* Using [Connection] _name_
* Giving _variable_
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _META_ARG, _RESULT_ARG, _USING_ARG)
    ns: str = _resolve_str_arg(ctx, statement.children[0], 'Namespace')
    parent_namespace: str = _get_default_ns(ctx, args)
    metadata = args.get(_META_ARG)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.update_namespace(ns, metadata, parent_namespace))

@bound_ops("Vault-DeleteNamespace")
def execute_delete_ns(ctx: ExecContext, statement: Tree) -> None:
    """
**Delete a namespace**

* Vault DeleteNamespace _namespace_ [;]

_Options_

* Namespace Is _parent_
* Using [Connection] _name_
* Giving _variable_
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    ns: str = _resolve_str_arg(ctx, statement.children[0], 'Namespace')
    parent_namespace: str = _get_default_ns(ctx, args)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.delete_namespace(ns, parent_namespace))

@bound_ops("Vault-ListNamespaces")
def execute_list_ns(ctx: ExecContext, statement: Tree) -> None:
    """
**List child namespaces**

* Vault ListNamespaces [;]
* Vault ListNamespaces _parent_ [;]
* Vault ListNamespaces Namespace Is _parent_ [;]

_Options_

* Namespace Is _parent_
* Using [Connection] _name_
* Giving _variable_
"""
    namespace: str = _resolve_str_arg(ctx, statement.children[0], 'Namespace', True) if len(statement.children) > 1 else ""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    parent_namespace: str = _get_default_ns(ctx, args)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.list_namespace(_combine_ns(parent_namespace, namespace)))

@bound_ops("Vault-LockNamespace")
def execute_lock_ns(ctx: ExecContext, statement: Tree) -> None:
    """
**Lock a namespace**

* Vault LockNamespace _namespace_ [;]

_Options_

* Namespace Is _parent_
* Using [Connection] _name_
* Giving _variable_
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _resolve_str_arg(ctx, statement.children[0], 'Namespace')
    parent_namespace: str = _get_default_ns(ctx, args)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.lock_namespace(_combine_ns(parent_namespace, namespace)))

@bound_ops("Vault-UnlockNamespace")
def execute_unlock_ns(ctx: ExecContext, statement: Tree) -> None:
    """
**Unlock a namespace**

* Vault UnlockNamespace _namespace_ Key Is _key_ [;]

_Options_

* Namespace Is _parent_
* Using [Connection] _name_
* Giving _variable_
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG, _KEY_ARG)
    namespace: str = _resolve_str_arg(ctx, statement.children[0], 'Namespace')
    parent_namespace: str = _get_default_ns(ctx, args)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.unlock_namespace(_combine_ns(parent_namespace, namespace), args.get(_KEY_ARG)))

#-------------------------------------------------------------------------------
# Secret Engine mounts
#-------------------------------------------------------------------------------

@bound_ops("Vault-CreateMount")
def execute_create_mount(ctx: ExecContext, statement: Tree) -> None:
    """
**Create and configure a secrets engine**

* Vault CreateMount _mount_point_ Data Is _data_ [;]
* Vault CreateMount _mount_point_ Type Is _type_ Config Is _config_ Description Is _desc_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point = _resolve_str_arg(ctx, statement.children[0], 'Mount Point')
    args = _extract_args(ctx, statement)
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
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.create_mount(mount_point, data, namespace))

@bound_ops("Vault-ReadMount")
def execute_read_mount(ctx: ExecContext, statement: Tree) -> None:
    """
**Read the configuration of a secrets engine mount**

* Vault ReadMount _mount_point_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point = _resolve_str_arg(ctx, statement.children[0], 'Mount Point')
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.read_mount(mount_point, namespace))

@bound_ops("Vault-UpdateMount")
def execute_update_mount(ctx: ExecContext, statement: Tree) -> None:
    """
**Update the configuration of a secrets engine**

* Vault UpdateMount _mount_point_ Data Is _data_ [;]
* Vault UpdateMount _mount_point_ Config Is _config_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point = _resolve_str_arg(ctx, statement.children[0], 'Mount Point')
    args = _extract_args(ctx, statement)
    data = {}
    # Config and Data are synonymous, but you can't have both
    if _DATA_ARG in args:
        _allowed_args(args, _DATA_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
        data = _get_arg(args, _DATA_ARG, dict)
    else:
        _allowed_args(args, _CONFIG_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
        data = _get_arg(args, _CONFIG_ARG, dict)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.update_mount(mount_point, data, namespace))

@bound_ops("Vault-DeleteMount")
def execute_delete_mount(ctx: ExecContext, statement: Tree) -> None:
    """
**Remove a secrets engine mount**

* Vault DeleteMount _mount_point_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point = _resolve_str_arg(ctx, statement.children[0], 'Mount Point')
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.delete_mount(mount_point, namespace))

@bound_ops("Vault-ListMounts")
def execute_list_mounts(ctx: ExecContext, statement: Tree) -> None:
    """
**List the mount points in a namespace**

* Vault ListMounts [;]
* Vault ListMounts _namespace_ [;]
* Vault ListMounts Namspace Is _namespace_ [;]
* Vault ListMounts _namespace_ Namspace Is _parent_namespace_ [;]

If no namespace name is provided, the default namespace name is used.

_Options_

* Using [Connection] _name_
* Giving _variable_

Also see `Vault-DefaultNamespace`
"""
    namespace: str = _resolve_str_arg(ctx, statement.children[0], 'Namespace', True) if len(statement.children) > 1 else ""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    parent_namespace: str = _get_default_ns(ctx, args)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.list_mounts(_combine_ns(parent_namespace, namespace)))

#-------------------------------------------------------------------------------
# KV2 secrets and metadata
#-------------------------------------------------------------------------------

@bound_ops("Vault-CreateKvSecret")
def execute_create_kv_secret(ctx: ExecContext, statement: Tree) -> None:
    """
**Create or update the KV secrets**

* Vault CreateKvSecret _mount_and_path_ Data Is _data_ [;]
* Vault CreateKvSecret _mount_and_path_ Data Is _data_ Metadata Is _meta_ [;]

_Options_

* CAS Is _version_
* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, path = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _DATA_ARG, _META_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG, _CAS_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    cas: int = _get_arg(args, _CAS_ARG, int, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    data = add_kv_cas(extract_kv_data(_get_arg(args, _DATA_ARG, dict)) if _DATA_ARG in args else {}, cas)
    result = _set_result(ctx, args, client.create_kv2_secret(mount_point, path, data, namespace))
        # If the data part fails, we'll skip the meta part
        # Caller should be using <result>.status to see if things were okay
    if result['status'] is not None: return
    if _META_ARG in args:
        metadata = extract_kv_metadata(_get_arg(args, _META_ARG, dict))
        _set_result(ctx, args, client.create_kv2_metadata(mount_point, path, metadata, namespace))

@bound_ops("Vault-ReadKvSecret")
def execute_read_kv_secret(ctx: ExecContext, statement: Tree) -> None:
    """
**Read the KV secrets**

* Vault ReadKvSecret _mount_and_path_ [;]
* Vault ReadKvSecret _mount_and_path_ Version Is _version_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, path = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _VERSION_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    version: int = _get_arg(args, _VERSION_ARG, int, True)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.read_kv2_secret(mount_point, path, version, namespace))

@bound_ops("Vault-ReadKvMetadata")
def execute_read_kv_metadata(ctx: ExecContext, statement: Tree) -> None:
    """
**Read the KV metadata**

* Vault ReadKvMetadata _mount_and_path_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, path = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.read_kv2_metadata(mount_point, path, namespace))

@bound_ops("Vault-UpdateKvSecret")
def execute_update_kv_secret(ctx: ExecContext, statement: Tree) -> None:
    """
**Update the KV secrets data and/or metadata**

* Vault UpdateKvSecret _mount_and_path_ Data Is _data_ [;]
* Vault UpdateKvSecret _mount_and_path_ Data Is _data_ Metadata Is _meta_ [;]
* Vault UpdateKvSecret _mount_and_path_ Metadata Is _meta_ [;]

_Options_

* CAS Is _version_
* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, path = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _DATA_ARG, _META_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG, _CAS_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    cas: int = _get_arg(args, _CAS_ARG, int, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, None) # in case neither data or metada is provides
    if _DATA_ARG in args:
        data = add_kv_cas(extract_kv_data(_get_arg(args, _DATA_ARG, dict)), cas)
        result = _set_result(ctx, args, client.update_kv2_secret(mount_point, path, data, namespace))
        # If the data part fails, we'll skip the meta part
        # Caller should be using <result>.status to see if things were okay
        if result['status'] is not None: return
    if _META_ARG in args:
        metadata = extract_kv_metadata(_get_arg(args, _META_ARG, dict))
        _set_result(ctx, args, client.update_kv2_metadata(mount_point, path, metadata, namespace))

@bound_ops("Vault-PatchKvSecret")
def execute_patch_kv_secret(ctx: ExecContext, statement: Tree) -> None:
    """
**Patch the KV secrets data and/or metadata**

* Vault PatchKvSecret _mount_and_path_ Data Is _data_ [;]
* Vault PatchKvSecret _mount_and_path_ Data Is _data_ Metadata Is _meta_ [;]
* Vault PatchKvSecret _mount_and_path_ Metadata Is _meta_ [;]

_Options_

* CAS Is _version_
* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, path = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _DATA_ARG, _META_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG, _CAS_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    cas: int = _get_arg(args, _CAS_ARG, int, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, None) # in case neither data or metada is provides
    if _DATA_ARG in args:
        data = add_kv_cas(extract_kv_data(_get_arg(args, _DATA_ARG, dict)), cas)
        result = _set_result(ctx, args, client.patch_kv2_secret(mount_point, path, data, namespace))
        # If the data part fails, we'll skip the meta part
        # Caller should be using <result>.status to see if things were okay
        if result['status'] is not None: return
    if _META_ARG in args:
        metadata = extract_kv_metadata(_get_arg(args, _META_ARG, dict))
        _set_result(ctx, args, client.patch_kv2_metadata(mount_point, path, metadata, namespace))

@bound_ops("Vault-DeleteKvSecret")
def execute_delete_kv_secret(ctx: ExecContext, statement: Tree) -> None:
    """
**Delete a KV secret**

* Vault DeleteKvSecret _mount_and_path_ Version Is _version_ [;]
* Vault DeleteKvSecret _mount_and_path_ Data Is _data_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, path = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _VERSION_ARG, _DATA_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    data = _get_version_data(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.delete_kv2_secret(mount_point, path, data, namespace))

@bound_ops("Vault-UndeleteKvSecret")
def execute_undelete_kv_secret(ctx: ExecContext, statement: Tree) -> None:
    """
*Undelete a KV secret**

* Vault UndeleteKvSecret _mount_and_path_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, path = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _VERSION_ARG, _DATA_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    data = _get_version_data(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.undelete_kv2_secret(mount_point, path, data, namespace))

@bound_ops("Vault-DestroyKvSecret")
def execute_destroy_kv_secret(ctx: ExecContext, statement: Tree) -> None:
    """
**Destroy a KV secret**

* Vault DestoryKvSecret _mount_and_path_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, path = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _VERSION_ARG, _DATA_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    data = _get_version_data(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.destroy_kv2_secret(mount_point, path, data, namespace))

@bound_ops("Vault-DeleteKvMetadata")
def execute_delete_kv_metadata(ctx: ExecContext, statement: Tree) -> None:
    """
**Delete KV metadata**

* Vault DeleteKvMetadata _mount_and_path_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, path = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.delete_kv2_metadata(mount_point, path, namespace))

@bound_ops("Vault-ListKvSecrets")
def execute_list_kv_secrets(ctx: ExecContext, statement: Tree) -> None:
    """
**List KV secrets at a path location**

* Vault ListKvSecrets _mount_and_path_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, path = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.list_kv2_secrets(mount_point, path, namespace))

#-------------------------------------------------------------------------------
# LDAP secrets engine : Library
#-------------------------------------------------------------------------------

@bound_ops("Vault-CreateLdapLibrary")
def execute_create_ldap_library(ctx: ExecContext, statement: Tree) -> None:
    """
**Create a set of LDAP credentials**

* Vault CreateLdapLibrary _mount_and_set_<br>
  <em>Config Is _config_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Set Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _CONFIG_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    config = _get_arg(args, _CONFIG_ARG, dict)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.create_ldap_library(mount_point, name, config, namespace))

@bound_ops("Vault-ReadLdapLibrary")
def execute_read_ldap_library(ctx: ExecContext, statement: Tree) -> None:
    """
**Get the configuraiton of a set of LDAP credentials**

* Vault ReadLdapLibrary _mount_and_set_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Set Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.read_ldap_library(mount_point, name, namespace))

@bound_ops("Vault-UpdateLdapLibrary")
def execute_update_ldap_library(ctx: ExecContext, statement: Tree) -> None:
    """
**Update the configuraiton of a set of LDAP credentials**

* Vault UpdateLdapLibrary _mount_and_set_<br>
  <em>Config Is _config_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Set Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _CONFIG_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    config = _get_arg(args, _CONFIG_ARG, dict)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.update_ldap_library(mount_point, name, config, namespace))

@bound_ops("Vault-DeleteLdapLibrary")
def execute_delete_ldap_library(ctx: ExecContext, statement: Tree) -> None:
    """
**Remove a set of LDAP credentials**

* Vault DeleteLdapLibrary _mount_and_set_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Set Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.delete_ldap_library(mount_point, name, namespace))

@bound_ops("Vault-ListLdapLibraries")
def execute_list_ldap_libraries(ctx: ExecContext, statement: Tree) -> None:
    """
**List LDAP library set names**

* Vault ListLdapLibraries _mount_point_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point = _resolve_str_arg(ctx, statement.children[0], 'Mount Point')
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.list_ldap_libraries(mount_point, namespace))

#-------------------------------------------------------------------------------
# LDAP secrets engine : Static Roles
#-------------------------------------------------------------------------------

@bound_ops("Vault-CreateLdapRole")
def execute_create_ldap_role(ctx: ExecContext, statement: Tree) -> None:
    """
**Create a static LDAP role**

* Vault CreateLdapRole _mount_and_role_<br>
  <em>Config Is _config_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _CONFIG_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    config = _get_arg(args, _CONFIG_ARG, dict, True)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.create_ldap_role(mount_point, name, config, namespace))

@bound_ops("Vault-ReadLdapRole")
def execute_read_ldap_role(ctx: ExecContext, statement: Tree) -> None:
    """
**Get a static LDAP role**

* Vault ReadLdapRole _mount_and_role_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.read_ldap_role(mount_point, name, namespace))

@bound_ops("Vault-UpdateLdapRole")
def execute_update_ldap_role(ctx: ExecContext, statement: Tree) -> None:
    """
**Update a static LDAP role**

* Vault UpdateLdapRole _mount_and_role_<br>
  <em>Config Is _config_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _CONFIG_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    config = _get_arg(args, _CONFIG_ARG, dict, True)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.update_ldap_role(mount_point, name, config, namespace))

@bound_ops("Vault-DeleteLdapRole")
def execute_delete_ldap_role(ctx: ExecContext, statement: Tree) -> None:
    """
**Remove a static LDAP role**

* Vault DeleteLdapRole _mount_and_role_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.delete_ldap_role(mount_point, name, namespace))

@bound_ops("Vault-ListLdapRoles")
def execute_list_ldap_roles(ctx: ExecContext, statement: Tree) -> None:
    """
**List static LDAP roles**

* Vault ListLdapRoles _mount_point_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point = _resolve_str_arg(ctx, statement.children[0], 'Mount Point')
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.list_ldap_roles(mount_point, namespace))

@bound_ops("Vault-RotateLdapRole")
def execute_rotate_ldap_role(ctx: ExecContext, statement: Tree) -> None:
    """
**Rotate the password of a static LDAP role**

* Vault RotateLdapRole _mount_and_role_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.rotate_ldap_role(mount_point, name, namespace))

#-------------------------------------------------------------------------------
# Database secrets engine : Connections
#-------------------------------------------------------------------------------

@bound_ops("Vault-CreateDbConnection")
def execute_create_db_connection(ctx: ExecContext, statement: Tree) -> None:
    """
**Create and configure a Database Connection**

* Vault CreateDbConnection _mount_and_name_<br>
  <em>Config Is _config_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _CONFIG_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    config = _get_arg(args, _CONFIG_ARG, dict)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.create_database_connection(mount_point, name, config, namespace))

@bound_ops("Vault-ReadDbConnection")
def execute_read_db_connection(ctx: ExecContext, statement: Tree) -> None:
    """
**Read a Database Connection configuration**

* Vault ReadDbConnection _mount_and_name_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.read_database_connection(mount_point, name, namespace))

@bound_ops("Vault-UpdateDbConnection")
def execute_update_db_connection(ctx: ExecContext, statement: Tree) -> None:
    """
**Update a Database Connection configuration**

* Vault UpdateDbConnection _mount_and_name_<br>
  <em>Config Is _config_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _CONFIG_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    config = _get_arg(args, _CONFIG_ARG, dict)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.update_database_connection(mount_point, name, config, namespace))

@bound_ops("Vault-DeleteDbConnection")
def execute_delete_db_connection(ctx: ExecContext, statement: Tree) -> None:
    """
**Remove a Database Connection**

* Vault DeleteDbConnection _mount_and_name_<br>
  <em>Config Is _config_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.delete_database_connection(mount_point, name, namespace))

@bound_ops("Vault-ListDbConnections")
def execute_list_db_connections(ctx: ExecContext, statement: Tree) -> None:
    """
**List Database Connections**

* Vault ListDbConnections _mount_point_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point = _resolve_str_arg(ctx, statement.children[0], 'Mount Point')
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.list_database_connections(mount_point, namespace))

@bound_ops("Vault-ResetDbConnection")
def execute_reset_db_connection(ctx: ExecContext, statement: Tree) -> None:
    """
**Closes a Database Connection and it's plugin and restarts it**

* Vault ResetDbConnection _mount_and_name_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.reset_database_connection(mount_point, name, namespace))

@bound_ops("Vault-RotateDbConnectionCredentials")
def execute_rotate_db_connection_creds(ctx: ExecContext, statement: Tree) -> None:
    """
**Rotate the user credentials of the Database Connection**

* Vault RotateDbConnectionCredentials _mount_and_name_ [;]

_Options_

* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _RESULT_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.rotate_database_connection_creds(mount_point, name, namespace))

#-------------------------------------------------------------------------------
# Database secrets engine : Roles
#-------------------------------------------------------------------------------

@bound_ops("Vault-CreateDbRole")
def execute_create_db_role(ctx: ExecContext, statement: Tree) -> None:
    """
**Creates a Role for a Database**

* Vault CreateDbRole _mount_and_name_<br>
  <em>Config is _config_ [;]

_Options_

* Type Is _type_ - use "Static" for static roles, otherwise omit
* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, role_name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Role Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _CONFIG_ARG, _TYPE_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    config = _get_arg(args, _CONFIG_ARG, dict)
    is_static = _is_static_type(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.create_database_role(mount_point, role_name, is_static, config, namespace))

@bound_ops("Vault-ReadDbRole")
def execute_read_db_role(ctx: ExecContext, statement: Tree) -> None:
    """
**Read a Database Role**

* Vault ReadDbRole _mount_and_name_ [;]

_Options_

* Type Is _type_ - use "Static" for static roles, otherwise omit
* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, role_name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Role Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _TYPE_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    is_static = _is_static_type(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.read_database_role(mount_point, role_name, is_static, namespace))

@bound_ops("Vault-UpdateDbRole")
def execute_update_db_role(ctx: ExecContext, statement: Tree) -> None:
    """
**Update a Role for a Database**

* Vault UpdateDbRole _mount_and_name_<br>
  <em>Config is _config_ [;]

_Options_

* Type Is _type_ - use "Static" for static roles, otherwise omit
* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, role_name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Role Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _CONFIG_ARG, _TYPE_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    config = _get_arg(args, _CONFIG_ARG, dict)
    is_static = _is_static_type(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.update_database_role(mount_point, role_name, is_static, config, namespace))

@bound_ops("Vault-DeleteDbRole")
def execute_delete_db_role(ctx: ExecContext, statement: Tree) -> None:
    """
**Remove a Database Role**

* Vault DeleteDbRole _mount_and_name_ [;]

_Options_

* Type Is _type_ - use "Static" for static roles, otherwise omit
* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, role_name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Role Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _TYPE_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    is_static = _is_static_type(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.delete_database_role(mount_point, role_name, is_static, namespace))

@bound_ops("Vault-ListDbRoles")
def execute_list_db_roles(ctx: ExecContext, statement: Tree) -> None:
    """
**List Database Roles for a mount point**

* Vault ListDbRoles _mount_point_ [;]

_Options_

* Type Is _type_ - use "Static" for static roles, otherwise omit
* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point = _resolve_str_arg(ctx, statement.children[0], 'Mount Point')
    args = _extract_args(ctx, statement)
    _allowed_args(args, _TYPE_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    is_static = _is_static_type(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.list_database_role(mount_point, is_static, namespace))

@bound_ops("Vault-GenerateDbRoleCredentials")
def execute_generate_db_role_creds(ctx: ExecContext, statement: Tree) -> None:
    """
**Generate a new credentials for a Database Role**

* Vault GenerateDbRoleCredentials _mount_and_name_ [;]

_Options_

* Type Is _type_ - use "Static" for static roles, otherwise omit
* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, role_name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Role Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _TYPE_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    is_static = _is_static_type(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.generate_database_role_credentials(mount_point, role_name, is_static, namespace))

@bound_ops("Vault-RotateDbRoleCredentials")
def execute_vault_rotate_db_role_creds(ctx: ExecContext, statement: Tree) -> None:
    """
**Generate a new credentials for a _Static_ Database Role**

* Vault RotateDbRoleCredentials _mount_and_name_ [;]

_Options_

* Type Is _type_ - must be "Static" if provided
* Namespace Is _namespace_
* Using [Connection] _name_
* Giving _variable_
"""
    mount_point, role_name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Role Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _TYPE_ARG, _NS_ARG, _RESULT_ARG, _USING_ARG)
    # If type isn't specify--unlike other calls--then static is assumed
    # But if it is specified, it has to be static
    is_static = True if _TYPE_ARG not in args else _is_static_type(args)
    if not is_static:
        raise ValueError(f'{mount_point}/{role_name} : Can only rotate credentials of static roles')
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.rotate_database_static_role_credentials(mount_point, role_name, namespace))

#-------------------------------------------------------------------------------

def _normalize_path(path: str) -> str:
    """Make sure path points to /v1/<something>"""
    if path.startswith("/v1/"): return path
    if path.startswith("/"): return "/v1" + path
    return "/v1/" + path

def _get_default_ns(_ctx: ExecContext, args: dict) -> str:
    """If the args doesn't contain the namespace, use the default one"""
    return _get_arg(args, _NS_ARG, str, True) or _STATE.default_namespace

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

def _combine_ns(parent: str, child: str) -> str:
    """Combine parent and child namespace paths into a single path."""
    parent = (parent or '').strip('/').replace('//', '/')
    child = (child or '').strip('/').replace('//', '/')
    if not parent and not child: return ''
    if not parent: return child
    if not child: return parent
    return f'{parent}/{child}'

def _split_mount_path(s: str) -> tuple:
    s = '/'.join(filter(None, s.split('/')))
    parts = s.split('/', 1)
    if len(parts) != 2:
        raise ValueError(f'Missing information following Mount Point: {s}')
    return parts

def _type_str(o: Any) -> str:
    return repr(type(o).__name__)

def _is_static_type(args: dict):
    """Look at _TYPE_ARG and see if user requested "static" """
    value: str = _get_arg(args, _TYPE_ARG, str, True)
    if not value: return False
    return ''.join(filter(str.isalpha, value)).lower().startswith('stat')

def _get_version_data(args: dict) -> dict:
    # Use _DATA to allow direct use of "versions"
    if _DATA_ARG in args: return _get_arg(args, _DATA_ARG, dict)
    # Use _VERSION_ARG for target version
    rc = {"versions": [] }
    if _VERSION_ARG in args:
        # Convert it to a list of integers
        rc["versions"] = poly_list(poly_int(args[_VERSION_ARG]))
    return rc

def _extract_args(ctx: ExecContext, statement: Tree) -> dict:
    args = {}
    # Last child will be the "vault_args"
    # and its children will all be prefixed with "vopt_"
    for child in statement.children[-1].children:
        if isinstance(child, Tree) and child.data.startswith('vopt_'):
            arg_name = child.data[5:]
            arg_node = child.children[0]
            if arg_name in _ARG_VAR_NAME:
                args[arg_name] = _var_name_path(arg_node)
            elif arg_name in _ARG_INT_EXPR:
                v = ctx.eval_expr_or_const(arg_node)
                # TODO !! looks like potential common code
                if v:
                    if not isinstance(v, (int, float)): raise TypeError(f'{arg_name.title()} must be a int; found {_type_str(v)}')
                    args[arg_name] = int(v)
            elif arg_name in _ARG_EXPR:
                args[arg_name] = ctx.eval_expr_or_const(arg_node)
            else:
                raise VgrRuntimeError(child, NotImplementedError(f'Vault argument {arg_name!r} not implemented')) # SNO
        else:
            raise VgrRuntimeError(child, ValueError(f'Unexpected Vault argument {child.data!r}:{_type_str(child)}')) # SNO
    return args

def _resolve_str_arg(ctx: ExecContext, expr: Tree, name: str, allow_none: bool=False) -> str:
    rc = ctx.eval_expr_or_const(expr)
    if rc is None and allow_none: return None
    if not isinstance(rc, str): raise TypeError(f'{name} must be a string; found {_type_str(rc)}')
    return rc

def _allowed_args(args: dict, *allowed_keys) -> None:
    """Raise an error if any key in args is not in allowed_keys."""
    for key in args:
        if key not in allowed_keys:
            raise ValueError(f'Unexpected argument: {key.title()}')

def _get_arg(args: dict, name: str, expected_type: type, optional: bool = False) -> Any:
    """Retrieve a typed value from args or raise if missing or wrong type."""
    if name not in args:
        if optional: return None
        raise ValueError(f'Missing required argument: {name.title()}')
    value = args[name]
    if isinstance(value, expected_type): return value
    raise TypeError(f'Argument {name.title()} must be of type {_type_str(expected_type)}, found {_type_str(value)}')
