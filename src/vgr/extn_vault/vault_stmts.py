"""
Implementations of Vault Statements
"""

from typing import Any

from lark import Tree

from ..app_exceptions import VgrRuntimeError
from ..builtins import (
    bound_ops,
    poly_clamp,
    poly_to_integer,
    poly_to_list,
    poly_to_number,
    poly_type,
)
from ..data_dict import DataDictionary, DynamicValue
from ..evaluate import do_set, _var_name_path
from ..exec_context import ExecContext
from .vault_client_mgr import VaultClientManager

from .vault_functions import extract_kv_data, extract_kv_metadata, add_kv_cas

_CAS_ARG     = 'vopt_cas'
_CONFIG_ARG  = 'vopt_config'
_DATA_ARG    = 'vopt_data'
_DESC_ARG    = 'vopt_description'
_KEY_ARG     = 'vopt_key'
_META_ARG    = 'vopt_metadata'
_NS_ARG      = 'vopt_namespace'
_GIVING_ARG  = 'vopt_giving'
_TYPE_ARG    = 'vopt_type'
_USING_ARG   = 'vopt_using'
_VERSION_ARG = 'vvopt_ersion'

# Values used with "Type Is <type>"
_STATIC_TYPE = "Static"
_DYNAMIC_TYPE = "Dynamic"

# These arguments result in a variable name
_ARG_VAR_NAME = (_GIVING_ARG,)

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

@bound_ops("Vault Connect")
def execute_connect(ctx: ExecContext, statement: Tree) -> None:
    """
**Establish a connection to Vault**

* Vault Connect
* Vault Connect To *host*
* Vault Connect To *host* Token Is *token*
* Vault Connect To *host* Token Is *token* As *connection_name*

*Options*

* Timeout Is *value* [Seconds]
* [BlockSize | Block Size] Is *value* [Bytes]

Also see `Vault Disconnect`
"""
    conn_name = timeout = blocksize = None
    # If not provided, we use our (inherited and mutable) environment
    addr = ctx.get_var('env', 'VAULT_ADDR')
    token = ctx.get_var('env', 'VAULT_TOKEN')
    conn_name = _get_conn_name({})
    for child in statement.children:
        if isinstance(child, Tree):
            name: str = child.data
            if name == 'conn_addr':
                # None means use default
                addr = _resolve_str_arg(ctx, child.children[0], 'Vault Address', True) or addr
            elif name == 'conn_token':
                token = _resolve_str_arg(ctx, child.children[0], 'Vault Token', True) # okay to be None!
            elif name == 'conn_name':
                # None means use default
                conn_name = _resolve_str_arg(ctx, child.children[0], 'Vault Connection Name', True) or conn_name
            elif name == 'conn_timeout':
                v = _resolve_number_arg(ctx, child.children[0], 'Vault Connection Timeout', True)
                timeout = None if v is None else poly_clamp(v, 0.001, 600.0) # 1 msec to 10 minutes
            elif name == 'conn_blocksize':
                v = _resolve_int_arg(ctx, child.children[0], 'Vault Connection Blocksize', True)
                blocksize = None if v is None else poly_clamp(v, 256, 1024 * 512) # 256 bytes to 512k
            else:
                # SNO
                raise VgrRuntimeError(child, NotImplementedError(f'Argument {name!r} not handled')) # pragma no cover
        else:
            # SNO
            raise VgrRuntimeError(child, ValueError(f'Unexpected Vault argument {child!r}')) # pragma no cover
    try:
        client = _CONNECTIONS.connect(conn_name, addr, token)
        if timeout is not None:
            client.timeout = timeout
        if blocksize is not None:
            client.blocksize = blocksize
    except ValueError as e:
        raise VgrRuntimeError(statement, e) from e
    _STATE.default_connection = conn_name
    _set_result(ctx, {}, None)

@bound_ops("Vault Disconnect")
def execute_disconnect(ctx: ExecContext, statement: Tree) -> None:
    """
**Close a connection to Vault**

* Vault Disconnect
* Vault Disconnect *connection_name*

Also see `Vault Connect`
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

@bound_ops("Vault Delete")
def execute_api_delete(ctx: ExecContext, statement: Tree) -> None:
    """
**Send a DELETE to a Vault API**

* Vault Delete *path* [*options*]&hellip;

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _GIVING_ARG, _USING_ARG)
    url: str = _normalize_path(_resolve_str_arg(ctx, statement.children[0], 'Path'))
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.do_delete(url, namespace))

@bound_ops("Vault Get")
def execute_api_get(ctx: ExecContext, statement: Tree) -> None:
    """
**Send a GET to a Vault API**

* Vault Get *path* [*options*]&hellip;
* Vault Read *path* [*options*]&hellip;

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _GIVING_ARG, _USING_ARG)
    url: str = _normalize_path(_resolve_str_arg(ctx, statement.children[0], 'Path'))
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.do_get(url, namespace))

@bound_ops("Vault List")
def execute_api_list(ctx: ExecContext, statement: Tree) -> None:
    """
**Send a LIST to a Vault API**

* Vault List *path* [*options*]&hellip;

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _GIVING_ARG, _USING_ARG)
    url: str = _normalize_path(_resolve_str_arg(ctx, statement.children[0], 'Path'))
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.do_list(url, namespace))

@bound_ops("Vault Patch")
def execute_api_patch(ctx: ExecContext, statement: Tree) -> None:
    """
**Send a PATCH to a Vault API**

* Vault Patch *path* [*options*]&hellip;

*Options*

* Data Is *data*
* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _DATA_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    url: str = _normalize_path(_resolve_str_arg(ctx, statement.children[0], 'Path'))
    data = _get_arg(args, _DATA_ARG, dict, True)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.do_patch(url, data, namespace))

@bound_ops("Vault Post")
def execute_api_post(ctx: ExecContext, statement: Tree) -> None:
    """
**Send a POST to a Vault API**

* Vault Post *path* [*options*]&hellip;
* Vault Create *path* [*options*]&hellip;
* Vault Update *path* [*options*]&hellip;

*Options*

* Data Is *data*
* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _DATA_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    url: str = _normalize_path(_resolve_str_arg(ctx, statement.children[0], 'Path'))
    data = _get_arg(args, _DATA_ARG, dict, True)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.do_post(url, data, namespace))

@bound_ops("Vault Default Namespace")
def execute_default_ns(ctx: ExecContext, statement: Tree) -> None:
    """
**Set the namespace to be used by subsequent requests**

* Vault Default Namespace *namespace*

*Deprecated*

*Options*

* Giving *variable*
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _GIVING_ARG)
    ns: str = _resolve_str_arg(ctx, statement.children[0], 'Default Namespace', True)
    _STATE.default_namespace = '' if ns is None or ns.isspace() else ns.strip()
    _set_result(ctx, args, None)

@bound_ops("Vault Create Namespace")
def execute_create_ns(ctx: ExecContext, statement: Tree) -> None:
    """
**Create a new namesapce**

* Vault Create Namespace *namespace*

*Options*

* Metadata Is *metadata*
* Namespace Is *parent*
* Using [Connection] *name*
* Giving *variable*
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _META_ARG, _GIVING_ARG, _USING_ARG)
    new_namespace: str = _resolve_str_arg(ctx, statement.children[0], 'New Namespace')
    parent_namespace: str = _get_default_ns(ctx, args)
    metadata = args.get(_META_ARG)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.create_namespace(new_namespace, metadata, parent_namespace))

@bound_ops("Vault Read Namespace")
def execute_read_ns(ctx: ExecContext, statement: Tree) -> None:
    """
**Read a namespace**

* Vault Read Namespace *namespace*

*Options*

* Namespace Is *parent*
* Using [Connection] *name*
* Giving *variable*
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _GIVING_ARG, _USING_ARG)
    ns: str = _resolve_str_arg(ctx, statement.children[0], 'Namespace')
    parent_namespace: str = _get_default_ns(ctx, args)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.read_namespace(ns, parent_namespace))

@bound_ops("Vault Update Namespace")
def execute_update_ns(ctx: ExecContext, statement: Tree) -> None:
    """
**Update a namespace**

* Vault Update Namespace *namespace* Metadata Is *metadata*

*Options*

* Namespace Is *parent*
* Using [Connection] *name*
* Giving *variable*
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _META_ARG, _GIVING_ARG, _USING_ARG)
    ns: str = _resolve_str_arg(ctx, statement.children[0], 'Namespace')
    parent_namespace: str = _get_default_ns(ctx, args)
    metadata = args.get(_META_ARG)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.update_namespace(ns, metadata, parent_namespace))

@bound_ops("Vault Delete Namespace")
def execute_delete_ns(ctx: ExecContext, statement: Tree) -> None:
    """
**Delete a namespace**

* Vault Delete Namespace *namespace*

*Options*

* Namespace Is *parent*
* Using [Connection] *name*
* Giving *variable*
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _GIVING_ARG, _USING_ARG)
    ns: str = _resolve_str_arg(ctx, statement.children[0], 'Namespace')
    parent_namespace: str = _get_default_ns(ctx, args)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.delete_namespace(ns, parent_namespace))

@bound_ops("Vault List Namespaces")
def execute_list_ns(ctx: ExecContext, statement: Tree) -> None:
    """
**List child namespaces**

* Vault List Namespaces
* Vault List Namespaces *parent*
* Vault List Namespaces Namespace Is *parent*

*Options*

* Namespace Is *parent*
* Using [Connection] *name*
* Giving *variable*
"""
    namespace: str = _resolve_str_arg(ctx, statement.children[0], 'Namespace', True) if len(statement.children) > 1 else ""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _GIVING_ARG, _USING_ARG)
    parent_namespace: str = _get_default_ns(ctx, args)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.list_namespace(_combine_ns(parent_namespace, namespace)))

@bound_ops("Vault Lock Namespace")
def execute_lock_ns(ctx: ExecContext, statement: Tree) -> None:
    """
**Lock a namespace**

* Vault Lock Namespace *namespace*

*Options*

* Namespace Is *parent*
* Using [Connection] *name*
* Giving *variable*
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _GIVING_ARG, _USING_ARG)
    namespace: str = _resolve_str_arg(ctx, statement.children[0], 'Namespace')
    parent_namespace: str = _get_default_ns(ctx, args)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.lock_namespace(_combine_ns(parent_namespace, namespace)))

@bound_ops("Vault Unlock Namespace")
def execute_unlock_ns(ctx: ExecContext, statement: Tree) -> None:
    """
**Unlock a namespace**

* Vault Unlock Namespace *namespace* Key Is *key*

*Options*

* Namespace Is *parent*
* Using [Connection] *name*
* Giving *variable*
"""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _GIVING_ARG, _USING_ARG, _KEY_ARG)
    namespace: str = _resolve_str_arg(ctx, statement.children[0], 'Namespace')
    parent_namespace: str = _get_default_ns(ctx, args)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.unlock_namespace(_combine_ns(parent_namespace, namespace), args.get(_KEY_ARG)))

#-------------------------------------------------------------------------------
# Secret Engine mounts
#-------------------------------------------------------------------------------

@bound_ops("Vault Create Mount")
def execute_create_mount(ctx: ExecContext, statement: Tree) -> None:
    """
**Create and configure a secrets engine**

* Vault Create Mount *mount_point* Data Is *data*
* Vault Create Mount *mount_point* Type Is _type_ Config Is _config_ Description Is _desc_

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point = _resolve_str_arg(ctx, statement.children[0], 'Mount Point')
    args = _extract_args(ctx, statement)
    data = {}
    # If Data=... specified, it means it contains all the config info
    # and piecemeal construction is not permitted
    if _DATA_ARG in args:
        _allowed_args(args, _DATA_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
        data = _get_arg(args, _DATA_ARG, dict)
    else:
        # If no data, then at least Type=... must be provided
        # Description and Config are optional
        _allowed_args(args, _DESC_ARG, _TYPE_ARG, _CONFIG_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
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

@bound_ops("Vault Read Mount")
def execute_read_mount(ctx: ExecContext, statement: Tree) -> None:
    """
**Read the configuration of a secrets engine mount**

* Vault Read Mount *mount_point*

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point = _resolve_str_arg(ctx, statement.children[0], 'Mount Point')
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _GIVING_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.read_mount(mount_point, namespace))

@bound_ops("Vault Update Mount")
def execute_update_mount(ctx: ExecContext, statement: Tree) -> None:
    """
**Update the configuration of a secrets engine**

* Vault Update Mount *mount_point* Data Is *data*
* Vault Update Mount *mount_point* Config Is _config_

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point = _resolve_str_arg(ctx, statement.children[0], 'Mount Point')
    args = _extract_args(ctx, statement)
    data = {}
    # Config and Data are synonymous, but you can't have both
    if _DATA_ARG in args:
        _allowed_args(args, _DATA_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
        data = _get_arg(args, _DATA_ARG, dict)
    else:
        _allowed_args(args, _CONFIG_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
        data = _get_arg(args, _CONFIG_ARG, dict)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.update_mount(mount_point, data, namespace))

@bound_ops("Vault Delete Mount")
def execute_delete_mount(ctx: ExecContext, statement: Tree) -> None:
    """
**Remove a secrets engine mount**

* Vault Delete Mount *mount_point*

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point = _resolve_str_arg(ctx, statement.children[0], 'Mount Point')
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _GIVING_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.delete_mount(mount_point, namespace))

@bound_ops("Vault List Mounts")
def execute_list_mounts(ctx: ExecContext, statement: Tree) -> None:
    """
**List the mount points in a namespace**

* Vault List Mounts
* Vault List Mounts *namespace*
* Vault List Mounts Namspace Is *namespace*
* Vault List Mounts *namespace* Namspace Is *parent_namespace*

If no namespace name is provided, the default namespace name is used.

*Options*

* Using [Connection] *name*
* Giving *variable*

Also see `Vault DefaultNamespace`
"""
    namespace: str = _resolve_str_arg(ctx, statement.children[0], 'Namespace', True) if len(statement.children) > 1 else ""
    args: dict = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _GIVING_ARG, _USING_ARG)
    parent_namespace: str = _get_default_ns(ctx, args)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.list_mounts(_combine_ns(parent_namespace, namespace)))

#-------------------------------------------------------------------------------
# KV2 secrets and metadata
#-------------------------------------------------------------------------------

@bound_ops("Vault Create KvSecret")
def execute_create_kv_secret(ctx: ExecContext, statement: Tree) -> None:
    """
**Create or update the KV secrets**

* Vault Create KvSecret *mount_and_path* Data Is *data*
* Vault Create KvSecret *mount_and_path* Data Is *data* Metadata Is *metadata*

*Options*

* CAS Is *version*
* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, path = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _DATA_ARG, _META_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG, _CAS_ARG)
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

@bound_ops("Vault Read KvSecret")
def execute_read_kv_secret(ctx: ExecContext, statement: Tree) -> None:
    """
**Read the KV secrets**

* Vault Read KvSecret *mount_and_path*
* Vault Read KvSecret *mount_and_path* Version Is *version*

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, path = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _VERSION_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    version: int = _get_arg(args, _VERSION_ARG, int, True)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.read_kv2_secret(mount_point, path, version, namespace))

@bound_ops("Vault Read KvMetadata")
def execute_read_kv_metadata(ctx: ExecContext, statement: Tree) -> None:
    """
**Read the KV metadata**

* Vault Read KvMetadata *mount_and_path*

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, path = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _GIVING_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.read_kv2_metadata(mount_point, path, namespace))

@bound_ops("Vault Update KvSecret")
def execute_update_kv_secret(ctx: ExecContext, statement: Tree) -> None:
    """
**Update the KV secrets data and/or metadata**

* Vault Update KvSecret *mount_and_path* Data Is *data*
* Vault Update KvSecret *mount_and_path* Data Is *data* Metadata Is *metadata*
* Vault Update KvSecret *mount_and_path* Metadata Is *metadata*

*Options*

* CAS Is *version*
* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, path = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _DATA_ARG, _META_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG, _CAS_ARG)
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

@bound_ops("Vault Patch KvSecret")
def execute_patch_kv_secret(ctx: ExecContext, statement: Tree) -> None:
    """
**Patch the KV secrets data and/or metadata**

* Vault Patch KvSecret *mount_and_path* Data Is *data*
* Vault Patch KvSecret *mount_and_path* Data Is *data* Metadata Is *metadata*
* Vault Patch KvSecret *mount_and_path* Metadata Is *metadata*

*Options*

* CAS Is *version*
* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, path = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _DATA_ARG, _META_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG, _CAS_ARG)
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

@bound_ops("Vault Delete KvSecret")
def execute_delete_kv_secret(ctx: ExecContext, statement: Tree) -> None:
    """
**Delete a KV secret**

* Vault Delete KvSecret *mount_and_path* Version Is *version*
* Vault Delete KvSecret *mount_and_path* Data Is *data*

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, path = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _VERSION_ARG, _DATA_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    data = _get_version_data(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.delete_kv2_secret(mount_point, path, data, namespace))

@bound_ops("Vault Undelete KvSecret")
def execute_undelete_kv_secret(ctx: ExecContext, statement: Tree) -> None:
    """
*Undelete a KV secret**

* Vault Undelete KvSecret *mount_and_path*

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, path = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _VERSION_ARG, _DATA_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    data = _get_version_data(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.undelete_kv2_secret(mount_point, path, data, namespace))

@bound_ops("Vault Destroy KvSecret")
def execute_destroy_kv_secret(ctx: ExecContext, statement: Tree) -> None:
    """
**Destroy a KV secret**

* Vault Destory KvSecret *mount_and_path*

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, path = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _VERSION_ARG, _DATA_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    data = _get_version_data(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.destroy_kv2_secret(mount_point, path, data, namespace))

@bound_ops("Vault Delete KvMetadata")
def execute_delete_kv_metadata(ctx: ExecContext, statement: Tree) -> None:
    """
**Delete KV metadata**

* Vault Delete KvMetadata *mount_and_path*

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, path = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _GIVING_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.delete_kv2_metadata(mount_point, path, namespace))

@bound_ops("Vault List KvSecrets")
def execute_list_kv_secrets(ctx: ExecContext, statement: Tree) -> None:
    """
**List KV secrets at a path location**

* Vault List KvSecrets *mount_and_path*

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, path = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Path'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _GIVING_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.list_kv2_secrets(mount_point, path, namespace))

#-------------------------------------------------------------------------------
# LDAP secrets engine : Library
#-------------------------------------------------------------------------------

@bound_ops("Vault Create LdapLibrary")
def execute_create_ldap_library(ctx: ExecContext, statement: Tree) -> None:
    """
**Create a set of LDAP credentials**

* Vault Create LdapLibrary *mount_and_set*\\
  &emsp;&emsp;Config Is _config_

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Set Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _CONFIG_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    config = _get_arg(args, _CONFIG_ARG, dict)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.create_ldap_library(mount_point, name, config, namespace))

@bound_ops("Vault Read LdapLibrary")
def execute_read_ldap_library(ctx: ExecContext, statement: Tree) -> None:
    """
**Get the configuraiton of a set of LDAP credentials**

* Vault Read LdapLibrary *mount_and_set*

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Set Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _GIVING_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.read_ldap_library(mount_point, name, namespace))

@bound_ops("Vault Update LdapLibrary")
def execute_update_ldap_library(ctx: ExecContext, statement: Tree) -> None:
    """
**Update the configuraiton of a set of LDAP credentials**

* Vault Update LdapLibrary *mount_and_set*\\
  &emsp;&emsp;Config Is _config_

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Set Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _CONFIG_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    config = _get_arg(args, _CONFIG_ARG, dict)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.update_ldap_library(mount_point, name, config, namespace))

@bound_ops("Vault Delete LdapLibrary")
def execute_delete_ldap_library(ctx: ExecContext, statement: Tree) -> None:
    """
**Remove a set of LDAP credentials**

* Vault Delete LdapLibrary *mount_and_set*

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Set Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _GIVING_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.delete_ldap_library(mount_point, name, namespace))

@bound_ops("Vault List LdapLibraries")
def execute_list_ldap_libraries(ctx: ExecContext, statement: Tree) -> None:
    """
**List LDAP library set names**

* Vault List LdapLibraries *mount_point*

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point = _resolve_str_arg(ctx, statement.children[0], 'Mount Point')
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _GIVING_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.list_ldap_libraries(mount_point, namespace))

#-------------------------------------------------------------------------------
# LDAP secrets engine : Roles
#-------------------------------------------------------------------------------

@bound_ops("Vault Create LdapRole")
def execute_create_ldap_role(ctx: ExecContext, statement: Tree) -> None:
    """
**Create an LDAP role**

* Vault Create LdapRole *mount_and_role*\\
  &emsp;&emsp;Config Is _config_

*Options*

* Type Is *type* - use "Static" or "Dynamic". Defaults to dynamic roles.
* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _CONFIG_ARG, _TYPE_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    config = _get_arg(args, _CONFIG_ARG, dict, True)
    is_static = _is_static_type(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.create_ldap_role(mount_point, name, config, is_static, namespace))

@bound_ops("Vault Read LdapRole")
def execute_read_ldap_role(ctx: ExecContext, statement: Tree) -> None:
    """
**Get an LDAP role**

* Vault Read LdapRole *mount_and_role*

*Options*

* Type Is *type* - use "Static" or "Dynamic". Defaults to dynamic roles.
* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _TYPE_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    is_static = _is_static_type(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.read_ldap_role(mount_point, name, is_static, namespace))

@bound_ops("Vault Update LdapRole")
def execute_update_ldap_role(ctx: ExecContext, statement: Tree) -> None:
    """
**Update an LDAP role**

* Vault Update LdapRole *mount_and_role*\\
  &emsp;&emsp;Config Is _config_

*Options*

* Type Is *type* - use "Static" or "Dynamic". Defaults to dynamic roles.
* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _CONFIG_ARG, _TYPE_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    config = _get_arg(args, _CONFIG_ARG, dict, True)
    is_static = _is_static_type(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.update_ldap_role(mount_point, name, config, is_static, namespace))

@bound_ops("Vault Delete LdapRole")
def execute_delete_ldap_role(ctx: ExecContext, statement: Tree) -> None:
    """
**Remove an LDAP role**

* Vault Delete LdapRole *mount_and_role*

*Options*

* Type Is *type* - use "Static" or "Dynamic". Defaults to dynamic roles.
* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _TYPE_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    is_static = _is_static_type(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.delete_ldap_role(mount_point, name, is_static, namespace))

@bound_ops("Vault List LdapRoles")
def execute_list_ldap_roles(ctx: ExecContext, statement: Tree) -> None:
    """
**List LDAP roles**

* Vault List LdapRoles *mount_point*

*Options*

* Type Is *type* - use "Static" or "Dynamic". Defaults to dynamic roles.
* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point = _resolve_str_arg(ctx, statement.children[0], 'Mount Point')
    args = _extract_args(ctx, statement)
    _allowed_args(args, _TYPE_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    is_static = _is_static_type(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.list_ldap_roles(mount_point, is_static, namespace))

@bound_ops("Vault Rotate LdapRole Credentials")
def execute_rotate_ldap_role(ctx: ExecContext, statement: Tree) -> None:
    """
**Rotate the password of a static LDAP role**

* Vault Rotate LdapRole Credentials *mount_and_role*

*Options*

* Type Is *type* - if present, mut be "Static". Typically omitted.
* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _TYPE_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    is_static = _is_static_type(args, True)
    if not is_static: raise ValueError('Can only rotate credentials of static roles')
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.rotate_ldap_role(mount_point, name, namespace))

#-------------------------------------------------------------------------------
# Database secrets engine : Connections
#-------------------------------------------------------------------------------

@bound_ops("Vault Create DbConnection")
def execute_create_db_connection(ctx: ExecContext, statement: Tree) -> None:
    """
**Create and configure a Database Connection**

* Vault Create DbConnection *mount_and_name*\\
  &emsp;&emsp;Config Is _config_

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _CONFIG_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    config = _get_arg(args, _CONFIG_ARG, dict)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.create_database_connection(mount_point, name, config, namespace))

@bound_ops("Vault Read DbConnection")
def execute_read_db_connection(ctx: ExecContext, statement: Tree) -> None:
    """
**Read a Database Connection configuration**

* Vault Read DbConnection *mount_and_name*

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _GIVING_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.read_database_connection(mount_point, name, namespace))

@bound_ops("Vault Update DbConnection")
def execute_update_db_connection(ctx: ExecContext, statement: Tree) -> None:
    """
**Update a Database Connection configuration**

* Vault Update DbConnection *mount_and_name*\\
  &emsp;&emsp;Config Is _config_

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _CONFIG_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    config = _get_arg(args, _CONFIG_ARG, dict)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.update_database_connection(mount_point, name, config, namespace))

@bound_ops("Vault Delete DbConnection")
def execute_delete_db_connection(ctx: ExecContext, statement: Tree) -> None:
    """
**Remove a Database Connection**

* Vault Delete DbConnection *mount_and_name*\\
  &emsp;&emsp;Config Is _config_

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _GIVING_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.delete_database_connection(mount_point, name, namespace))

@bound_ops("Vault List DbConnections")
def execute_list_db_connections(ctx: ExecContext, statement: Tree) -> None:
    """
**List Database Connections**

* Vault List DbConnections *mount_point*

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point = _resolve_str_arg(ctx, statement.children[0], 'Mount Point')
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _GIVING_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.list_database_connections(mount_point, namespace))

@bound_ops("Vault Reset DbConnection")
def execute_reset_db_connection(ctx: ExecContext, statement: Tree) -> None:
    """
**Closes a Database Connection and it's plugin and restarts it**

* Vault Reset DbConnection *mount_and_name*

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _GIVING_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.reset_database_connection(mount_point, name, namespace))

@bound_ops("Vault Rotate DbConnection Credentials")
def execute_rotate_db_connection_creds(ctx: ExecContext, statement: Tree) -> None:
    """
**Rotate the user credentials of the Database Connection**

* Vault Rotate DbConnectionCredentials *mount_and_name*

*Options*

* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _NS_ARG, _GIVING_ARG, _USING_ARG)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.rotate_database_connection_creds(mount_point, name, namespace))

#-------------------------------------------------------------------------------
# Database secrets engine : Roles
#-------------------------------------------------------------------------------

@bound_ops("Vault Create DbRole")
def execute_create_db_role(ctx: ExecContext, statement: Tree) -> None:
    """
**Creates a Role for a Database**

* Vault Create DbRole *mount_and_name*\\
  &emsp;&emsp;Config is _config_

*Options*

* Type Is *type* - use "Static" for static roles, otherwise omit
* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, role_name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Role Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _CONFIG_ARG, _TYPE_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    config = _get_arg(args, _CONFIG_ARG, dict)
    is_static = _is_static_type(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.create_database_role(mount_point, role_name, is_static, config, namespace))

@bound_ops("Vault Read DbRole")
def execute_read_db_role(ctx: ExecContext, statement: Tree) -> None:
    """
**Read a Database Role**

* Vault Read DbRole *mount_and_name*

*Options*

* Type Is *type* - use "Static" for static roles, otherwise omit
* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, role_name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Role Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _TYPE_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    is_static = _is_static_type(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.read_database_role(mount_point, role_name, is_static, namespace))

@bound_ops("Vault Update DbRole")
def execute_update_db_role(ctx: ExecContext, statement: Tree) -> None:
    """
**Update a Role for a Database**

* Vault Update DbRole *mount_and_name*\\
  &emsp;&emsp;Config is _config_

*Options*

* Type Is *type* - use "Static" for static roles, otherwise omit
* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, role_name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Role Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _CONFIG_ARG, _TYPE_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    config = _get_arg(args, _CONFIG_ARG, dict)
    is_static = _is_static_type(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.update_database_role(mount_point, role_name, is_static, config, namespace))

@bound_ops("Vault Delete DbRole")
def execute_delete_db_role(ctx: ExecContext, statement: Tree) -> None:
    """
**Remove a Database Role**

* Vault Delete DbRole *mount_and_name*

*Options*

* Type Is *type* - use "Static" for static roles, otherwise omit
* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, role_name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Role Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _TYPE_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    is_static = _is_static_type(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.delete_database_role(mount_point, role_name, is_static, namespace))

@bound_ops("Vault List DbRoles")
def execute_list_db_roles(ctx: ExecContext, statement: Tree) -> None:
    """
**List Database Roles for a mount point**

* Vault List DbRoles *mount_point*

*Options*

* Type Is *type* - use "Static" for static roles, otherwise omit
* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point = _resolve_str_arg(ctx, statement.children[0], 'Mount Point')
    args = _extract_args(ctx, statement)
    _allowed_args(args, _TYPE_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    is_static = _is_static_type(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.list_database_role(mount_point, is_static, namespace))

@bound_ops("Vault Generate DbRole Credentials")
def execute_generate_db_role_creds(ctx: ExecContext, statement: Tree) -> None:
    """
**Generate a new credentials for a Database Role**

* Vault Generate DbRole Credentials *mount_and_name*

*Options*

* Type Is *type* - use "Static" for static roles, otherwise omit
* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, role_name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Role Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _TYPE_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    is_static = _is_static_type(args)
    namespace: str = _get_arg(args, _NS_ARG, str, True)
    client =_CONNECTIONS.get_connection(_get_conn_name(args))
    _set_result(ctx, args, client.generate_database_role_credentials(mount_point, role_name, is_static, namespace))

@bound_ops("Vault Rotate DbRole Credentials")
def execute_rotate_db_role_creds(ctx: ExecContext, statement: Tree) -> None:
    """
**Generate a new credentials for a _Static_ Database Role**

* Vault Rotate DbRole Credentials *mount_and_name*

*Options*

* Type Is *type* - must be "Static" if provided
* Namespace Is *namespace*
* Using [Connection] *name*
* Giving *variable*
"""
    mount_point, role_name = _split_mount_path(_resolve_str_arg(ctx, statement.children[0], 'Mount Point/Role Name'))
    args = _extract_args(ctx, statement)
    _allowed_args(args, _TYPE_ARG, _NS_ARG, _GIVING_ARG, _USING_ARG)
    # If type isn't specify--unlike other calls--then static is assumed
    # But if it is specified, it has to be static
    is_static = True if _TYPE_ARG not in args else _is_static_type(args)
    if not is_static: raise ValueError('Can only rotate credentials of static roles')
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
    if _GIVING_ARG in args:
        path = args[_GIVING_ARG]
        # They can always restate the default
        # and if they do, we dont check immutability/protection
        # TODO This late check prevents us from doing good error reporting
        if path != _DEFAULT_RESULT_PATH:
            ctx.dd.validate_user_set_path(*path)
    do_set(ctx, data, *path)
    return data

def _get_conn_name(args: dict) -> str:
    """
    If the args doesn't contain the connection, use either the current default connection or the fixed default.
    Has the side effect of setting the default connection in _STATE.
    """
    _STATE.default_connection = _get_arg(args, _USING_ARG, str, True) or _STATE.default_connection or _DEFAULT_CONN_NAME
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

def _is_static_type(args: dict, default: bool=False) -> bool:
    """Look at _TYPE_ARG and see if user requested "static" """
    value: str = _get_arg(args, _TYPE_ARG, str, True)
    if not value: return default
    value = value.title()
    if value == _STATIC_TYPE: return True
    if value == _DYNAMIC_TYPE: return False
    raise ValueError(f'Type must be either {_STATIC_TYPE} or {_DYNAMIC_TYPE}; found {value!r}')

def _get_version_data(args: dict) -> dict:
    # Use _DATA to allow direct use of "versions"
    if _DATA_ARG in args: return _get_arg(args, _DATA_ARG, dict)
    # Use _VERSION_ARG for target version
    rc = {"versions": [] }
    if _VERSION_ARG in args:
        # Convert it to a list of integers
        rc["versions"] = poly_to_list(poly_to_integer(args[_VERSION_ARG]))
    return rc

def _extract_args(ctx: ExecContext, statement: Tree) -> dict:
    args = {}
    # Last child will be the "vault_args"
    # and its children will all be prefixed with "vopt_"
    for child in statement.children[-1].children:
        if isinstance(child, Tree):
            arg_name = child.data
            arg_node = child.children[0]
            if arg_name in _ARG_VAR_NAME:
                args[arg_name] = _var_name_path(arg_node)
            elif arg_name in _ARG_INT_EXPR:
                args[arg_name] = _resolve_int_arg(ctx, arg_node, arg_name.title(), True)
            elif arg_name in _ARG_EXPR:
                args[arg_name] = ctx.eval_expr_or_const(arg_node)
            else:
                # SNO
                raise VgrRuntimeError(child, NotImplementedError(f'Vault argument {arg_name!r} not implemented')) # pragma no cover
        else:
            # SNO
            raise VgrRuntimeError(child, ValueError(f'Unexpected Vault argument {child.data!r}:{poly_type(child)!r}')) # pragma no cover
    return args

def _display_name(name: str) -> str: return name.removeprefix("vopt_").title()

def _resolve_str_arg(ctx: ExecContext, expr: Tree, name: str, allow_none: bool=False) -> str:
    rc = ctx.eval_expr_or_const(expr)
    if rc is None and allow_none: return None
    if not isinstance(rc, str): raise TypeError(f'{_display_name(name)} must be a string; found {poly_type(rc)!r}')
    return rc

def _resolve_int_arg(ctx: ExecContext, expr: Tree, name: str, allow_none: bool=False) -> int:
    return int(_resolve_number_arg(ctx, expr, name, allow_none))

def _resolve_number_arg(ctx: ExecContext, expr: Tree, name: str, allow_none: bool=False) -> Any:
    rc = ctx.eval_expr_or_const(expr)
    if isinstance(rc, (str, int, float)): return poly_to_number(rc)
    if rc is None and allow_none: return None
    raise TypeError(f'{_display_name(name)} must be a number or string; found {poly_type(rc)!r}')

def _allowed_args(args: dict, *allowed_keys) -> None:
    """Raise an error if any key in args is not in allowed_keys."""
    for key in args:
        if key not in allowed_keys:
            raise ValueError(f'Unexpected argument: {_display_name(key)}')

def _get_arg(args: dict, name: str, expected_type: type, optional: bool = False) -> Any:
    """Retrieve a typed value from args or raise if missing or wrong type."""
    if name not in args:
        if optional: return None
        raise ValueError(f'Missing required argument: {_display_name(name)}')
    value = args[name]
    if isinstance(value, expected_type): return value
    if value is None and optional: return None
    raise TypeError(f'Argument {_display_name(name)} must be of type {poly_type(expected_type)!r}, found {poly_type(value)!r}')
