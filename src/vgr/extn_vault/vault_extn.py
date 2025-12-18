"""
Vault extension to the grammar
"""

from typing import Dict, Callable

from ..extn import VgrExtension
from ..data_dict import DataDictionary
from ..mathpak import bound_ops

from .functions import (
    duration_to_ms,
    extract_kv_data,
    extract_kv_metadata,
    ms_to_duration
)

from .stmts import (
    execute_api_delete,
    execute_api_get,
    execute_api_list,
    execute_api_patch,
    execute_api_post,
    execute_connect,
    execute_create_db_connection,
    execute_create_kv_secret,
    execute_create_ldap_library,
    execute_create_ldap_role,
    execute_create_mount,
    execute_create_ns,
    execute_default_ns,
    execute_delete_db_connection,
    execute_delete_db_role,
    execute_delete_kv_metadata,
    execute_delete_kv_secret,
    execute_delete_ldap_library,
    execute_delete_ldap_role,
    execute_delete_mount,
    execute_delete_ns,
    execute_destroy_kv_secret,
    execute_disconnect,
    execute_generate_db_role_creds,
    execute_list_db_connections,
    execute_list_kv_secrets,
    execute_list_ldap_libraries,
    execute_list_ldap_roles,
    execute_list_mounts,
    execute_list_ns,
    execute_lock_ns,
    execute_patch_kv_secret,
    execute_read_db_connection,
    execute_read_kv_metadata,
    execute_read_kv_secret,
    execute_read_ldap_library,
    execute_read_ldap_role,
    execute_read_mount,
    execute_read_ns,
    execute_reset_db_connection,
    execute_rotate_db_connection_creds,
    execute_rotate_ldap_role,
    execute_undelete_kv_secret,
    execute_unlock_ns,
    execute_update_db_connection,
    execute_update_kv_secret,
    execute_update_ldap_library,
    execute_update_ldap_role,
    execute_update_mount,
    execute_update_ns,
    vault_initialize,
)

@bound_ops("Vault")
def _vault_help(_ctx, _statement) -> None:
    """
**Vault Commands**

_Connections_
* Vault Connect<br>
  <em>To [Host] _host_<br>
  <em>[With Token | [Token Is] _token_<br>
  <em>As _connection_name_ - Opens a connection to a Vault instance
* Vault Disconnect [[From] _connection_name_] - Closes a connection

_Generic API Calls_

* Vault APIGet _path_ - Send a GET to a Vault API
* Vault APIList _path_ - Send a LIST to a Vault API
* Vault APIDelete _path_ - Send a DELETE to a Vault API
* Vault APIPost _path_ - Send a PATCH to a Vault API
* Vault APIPatch _path_ - Send a POST to a Vault API

_Namespace Management_

* Vault CreateNamespace _namespace_ - Create a new namesapce
* Vault ReadNamespace _namespace_ - Read a namespace
* Vault UpdateNamespace _namespace_ - Update a namespace
* Vault DeleteNamespace _namespace_ - Delete a namespace
* Vault ListNamespaces [_namespace_] - List child namespaces
* Vault LockNamespace _namespace_ - Lock a namespace
* Vault UnlockNamespace _namespace_ - Unlock a namespace
* Vault DefaultNamespace _namespace_ - Set the namespace to be used by subsequent requests

_Secret Engine Mount Points_

* Vault CreateMount _mount_point_ - Create and configure a secrets engine
* Vault ReadMount _mount_point_ - Read the configuration of a secrets engine mount
* Vault UpdateMount _mount_point_ - Update the configuration of a secrets engine
* Vault DeleteMount _mount_point_ - Remove a secrets engine mount
* Vault ListMounts [_namespace_] - List the mount points in a namespace

_KV2 Secrets_

* Vault CreateKvSecret _mount_and_path_ - Create or update the KV secrets
* Vault ReadKvSecret _mount_and_path_ - Read the KV secrets
* Vault ReadKvMetadata _mount_and_path_ - Read the KV metadata
* Vault DeleteKvMetadata _mount_and_path_ - Delete KV metadata
* Vault UpdateKvSecret _mount_and_path_ - Update the KV secrets data and/or metadata
* Vault DeleteKvSecret _mount_and_path_ - Delete a KV secret
* Vault UndeleteKvSecret _mount_and_path_ - Undelete a KV secret
* Vault DestroyKvSecret _mount_and_path_ - Destroy a KV secret
* Vault ListKvSecrets _mount_and_path_ - List KV secrets at a path location
* Vault PatchKvSecret _mount_and_path_ - Patch the KV secrets data and/or metadata

_LDAP Libraries Sets_

* Vault CreateLdapLibrary _mount_and_set_ - Create a set of LDAP credentials
* Vault ReadLdapLibrary _mount_and_set_ - Get the configuraiton of a set of LDAP credentials
* Vault UpdateLdapLibrary _mount_and_set_ - Update the configuraiton of a set of LDAP credentials
* Vault DeleteLdapLibrary _mount_and_set_ - Remove a set of LDAP credentials
* Vault ListLdapLibraries _mount_point_ - List LDAP library set names

_LDAP Static Roles_

* Vault CreateLdapRole _mount_and_role_ - Create a static LDAP role
* Vault ReadLdapRole _mount_and_role_ - Get a static LDAP role
* Vault UpdateLdapRole _mount_and_role_ - Update a static LDAP role
* Vault DeleteLdapRole _mount_and_role_ - Remove a static LDAP role
* Vault ListLdapRoles _mount_point_ - List static LDAP roles
* Vault RotateLdapRole _mount_and_role_ - Rotate the password of a static LDAP role

_Database Connections_

* Vault CreateDbConnection _mount_and_name_ - Create and configure a Database Connection
* Vault ReadDbConnection _mount_and_name_ - Read a Database Connection configuration
* Vault UpdateDbConnection _mount_and_name_ - Update a Database Connection configuration
* Vault DeleteDbConnection _mount_and_name_ - Remove a Database Connection
* Vault ListDbConnections _mount_point_ - List Database Connections
* Vault ResetDbConnection _mount_and_name_ - Closes a Database Connection and it's plugin and restarts it
* Vault RotateDbConnectionCredentials _mount_and_name_ - Rotate the user credentials of the Database Connection

_Database Roles_

* Vault CreateDbRole _mount_and_name_ - Creates a Role for a Database
* Vault ReadDbRole _mount_and_name_ - Read a Database Role
* Vault UpdateDbRole _mount_and_name_ - Update a Role for a Database
* Vault DeleteDbRole _mount_and_name_ - Remove a Database Role
* Vault ListDbRoles _mount_point_ - List Database Roles for a mount point
* Vault GenerateDbRoleCredentials _mount_and_name_ - Generate a new credentials for a Database Role

_Universal Options_

* Namespace [Is] _namespace_ - the namespace for the operations.
  Default namespace is used if not specified. For some operations, this
  is may be combined with other arguments as the parent namespace.
* Using [Connection] _connection_name_ - the connection to use. If not
  specified the last connection used by another command is assumed.
* [Result | Results] [In] _variable_ - the variable to receive the results
  of the command. If not specified, results are placed in _vault.result_.
* Giving _variable_ - synonym for _Results_

Multiple argument are separated by spaces or optional commas.

_Specialized Options_

* CAS [Is] _version_ - Sets the CAS version if required by operation
* Config [Is] _config_ - Configuration data for the operation; may be
  mutually exclusive with _Data_
* Data [Is] _data_ - Operation data if used by operation
* [Secret | Secrets] [[Is | Are]] _data_ - Synonym for _Data_
* Description [Is] _text_ - Description text if used by operation
* Key [Is] _key_ - Key argument if used by operation
* [Meta | Metadata] [Is] _metadata_ - Metadata if used by operation
* Type [Is] _type_ - Type indicator if used by operation
* [Version | Ver] [Is] _version_ - Version value if used by operation

_Results Structure_

In addition to the data returned by Vault, the Vault statement
adds the following attributes:

* _variable_.status - Human-readable status of the operation. If the operation
  succeeded, it will be _None_. Otherwise it will contain errors or warning reported
  by Vault, or the HTTP status.
* _variable_.vclient.url - The URL used in the operation
* _variable_.vclient.method - The HTTP method used in the operation
* _variable_.vclient.status - The HTTP return code from the operation
* _variable_.vclient.vault_index - value of the returned _X-Vault-Index_ header
* _variable_.vclient.vault_cluster - value of the returned _X-Vault-Cluster_ header
* _variable_.vclient.vault_lease_id - value of the returned _X-Vault-Lease-Id_ header

"""

STATEMENT_HANDLERS = {
    '_vault_help'                  : _vault_help,
    'vault_api_delete'             : execute_api_delete,
    'vault_api_get'                : execute_api_get,
    'vault_api_list'               : execute_api_list,
    'vault_api_patch'              : execute_api_patch,
    'vault_api_post'               : execute_api_post,
    'vault_connect'                : execute_connect,
    'vault_create_db_conn'         : execute_create_db_connection,
    'vault_create_kv_secret'       : execute_create_kv_secret,
    'vault_create_ldap_lib'        : execute_create_ldap_library,
    'vault_create_ldap_role'       : execute_create_ldap_role,
    'vault_create_mount'           : execute_create_mount,
    'vault_create_ns'              : execute_create_ns,
    'vault_default_ns'             : execute_default_ns,
    'vault_delete_db_conn'         : execute_delete_db_connection,
    'vault_delete_db_role'         : execute_delete_db_role,
    'vault_delete_kv_metadata'     : execute_delete_kv_metadata,
    'vault_delete_kv_secret'       : execute_delete_kv_secret,
    'vault_delete_ldap_lib'        : execute_delete_ldap_library,
    'vault_delete_ldap_role'       : execute_delete_ldap_role,
    'vault_delete_mount'           : execute_delete_mount,
    'vault_delete_ns'              : execute_delete_ns,
    'vault_destroy_kv_secret'      : execute_destroy_kv_secret,
    'vault_disconnect'             : execute_disconnect,
    'vault_generate_db_role_creds' : execute_generate_db_role_creds,
    'vault_list_db_conns'          : execute_list_db_connections,
    'vault_list_kv_secrets'        : execute_list_kv_secrets,
    'vault_list_ldap_libs'         : execute_list_ldap_libraries,
    'vault_list_ldap_roles'        : execute_list_ldap_roles,
    'vault_list_mounts'            : execute_list_mounts,
    'vault_list_ns'                : execute_list_ns,
    'vault_lock_ns'                : execute_lock_ns,
    'vault_patch_kv_secret'        : execute_patch_kv_secret,
    'vault_read_db_conn'           : execute_read_db_connection,
    'vault_read_kv_metadata'       : execute_read_kv_metadata,
    'vault_read_kv_secret'         : execute_read_kv_secret,
    'vault_read_ldap_lib'          : execute_read_ldap_library,
    'vault_read_ldap_role'         : execute_read_ldap_role,
    'vault_read_mount'             : execute_read_mount,
    'vault_read_ns'                : execute_read_ns,
    'vault_reset_db_conn'          : execute_reset_db_connection,
    'vault_rotate_db_conn'         : execute_rotate_db_connection_creds,
    'vault_rotate_ldap_role'       : execute_rotate_ldap_role,
    'vault_undelete_kv_secret'     : execute_undelete_kv_secret,
    'vault_unlock_ns'              : execute_unlock_ns,
    'vault_update_db_conn'         : execute_update_db_connection,
    'vault_update_kv_secret'       : execute_update_kv_secret,
    'vault_update_ldap_lib'        : execute_update_ldap_library,
    'vault_update_ldap_role'       : execute_update_ldap_role,
    'vault_update_mount'           : execute_update_mount,
    'vault_update_ns'              : execute_update_ns,
}

# Used with Select statement's From clause
_TARGETS = ('ns', 'mount', 'aws', 'kv', 'ldap', 'db', 'db_role')

_FUNCTIONS = {
    "DurationToMs"      : duration_to_ms,
    "ExtractKVMetadata" : extract_kv_metadata,
    "ExtractKVData"     : extract_kv_data,
    "MsToDuration"      : ms_to_duration,
}

class VaultExtension(VgrExtension):

    def initialize(self, dd: DataDictionary) -> None:
        vault_initialize(dd)

    def extends_select(self):
        return True

    def adds_statements(self):
        return True

    def grammar(self) -> str:
        g = self.read_resource_text(__package__, 'vault.ebnf')
        g += 'vault_from: "Vault"i VAULT_TARGET\n'
        return g + 'VAULT_TARGET: ' + ' | '.join(tuple(f'"{t}"i' for t in _TARGETS))

    def functions(self) -> Dict[str, Callable]:
        return _FUNCTIONS

    def statement_handlers(self) -> Dict[str, Callable]:
        return STATEMENT_HANDLERS
