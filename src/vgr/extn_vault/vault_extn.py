"""
Vault extension to the grammar
"""

from typing import Dict, Callable

from ..builtins import bound_ops
from ..extn import VgrExtension
from ..data_dict import DataDictionary

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

*Connections*

* Vault Connect\\
  &emsp;&emsp;To [Host] *host*\\
  &emsp;&emsp;[With Token | [Token Is] *token*\\
  &emsp;&emsp;As *connection_name* - Opens a connection to a Vault instance
* Vault Disconnect [[From] *connection_name*] - Closes a connection

*Generic API Calls*

* Vault APIGet *path* - Send a GET to a Vault API
* Vault APIList *path* - Send a LIST to a Vault API
* Vault APIDelete *path* - Send a DELETE to a Vault API
* Vault APIPost *path* - Send a PATCH to a Vault API
* Vault APIPatch *path* - Send a POST to a Vault API

*Namespace Management*

* Vault CreateNamespace *namespace* - Create a new namesapce
* Vault ReadNamespace *namespace* - Read a namespace
* Vault UpdateNamespace *namespace* - Update a namespace
* Vault DeleteNamespace *namespace* - Delete a namespace
* Vault ListNamespaces [*namespace*] - List child namespaces
* Vault LockNamespace *namespace* - Lock a namespace
* Vault UnlockNamespace *namespace* - Unlock a namespace
* Vault DefaultNamespace *namespace* - Set the namespace to be used by subsequent requests

*Secret Engine Mount Points*

* Vault CreateMount *mount_point* - Create and configure a secrets engine
* Vault ReadMount *mount_point* - Read the configuration of a secrets engine mount
* Vault UpdateMount *mount_point* - Update the configuration of a secrets engine
* Vault DeleteMount *mount_point* - Remove a secrets engine mount
* Vault ListMounts [*namespace*] - List the mount points in a namespace

*KV2 Secrets*

* Vault CreateKvSecret *mount_and_path* - Create or update the KV secrets
* Vault ReadKvSecret *mount_and_path* - Read the KV secrets
* Vault ReadKvMetadata *mount_and_path* - Read the KV metadata
* Vault DeleteKvMetadata *mount_and_path* - Delete KV metadata
* Vault UpdateKvSecret *mount_and_path* - Update the KV secrets data and/or metadata
* Vault DeleteKvSecret *mount_and_path* - Delete a KV secret
* Vault UndeleteKvSecret *mount_and_path* - Undelete a KV secret
* Vault DestroyKvSecret *mount_and_path* - Destroy a KV secret
* Vault ListKvSecrets *mount_and_path* - List KV secrets at a path location
* Vault PatchKvSecret *mount_and_path* - Patch the KV secrets data and/or metadata

*LDAP Libraries Sets*

* Vault CreateLdapLibrary *mount_and_set* - Create a set of LDAP credentials
* Vault ReadLdapLibrary *mount_and_set* - Get the configuraiton of a set of LDAP credentials
* Vault UpdateLdapLibrary *mount_and_set* - Update the configuraiton of a set of LDAP credentials
* Vault DeleteLdapLibrary *mount_and_set* - Remove a set of LDAP credentials
* Vault ListLdapLibraries *mount_point* - List LDAP library set names

*LDAP Static Roles*

* Vault CreateLdapRole *mount_and_role* - Create a static LDAP role
* Vault ReadLdapRole *mount_and_role* - Get a static LDAP role
* Vault UpdateLdapRole *mount_and_role* - Update a static LDAP role
* Vault DeleteLdapRole *mount_and_role* - Remove a static LDAP role
* Vault ListLdapRoles *mount_point* - List static LDAP roles
* Vault RotateLdapRole *mount_and_role* - Rotate the password of a static LDAP role

*Database Connections*

* Vault CreateDbConnection *mount_and_name* - Create and configure a Database Connection
* Vault ReadDbConnection *mount_and_name* - Read a Database Connection configuration
* Vault UpdateDbConnection *mount_and_name* - Update a Database Connection configuration
* Vault DeleteDbConnection *mount_and_name* - Remove a Database Connection
* Vault ListDbConnections *mount_point* - List Database Connections
* Vault ResetDbConnection *mount_and_name* - Closes a Database Connection and it's plugin and restarts it
* Vault RotateDbConnectionCredentials *mount_and_name* - Rotate the user credentials of the Database Connection

*Database Roles*

* Vault CreateDbRole *mount_and_name* - Creates a Role for a Database
* Vault ReadDbRole *mount_and_name* - Read a Database Role
* Vault UpdateDbRole *mount_and_name* - Update a Role for a Database
* Vault DeleteDbRole *mount_and_name* - Remove a Database Role
* Vault ListDbRoles *mount_point* - List Database Roles for a mount point
* Vault GenerateDbRoleCredentials *mount_and_name* - Generate a new credentials for a Database Role

*Universal Options*

* Namespace [Is] *namespace* - the namespace for the operations.
  Default namespace is used if not specified. For some operations, this
  is may be combined with other arguments as the parent namespace.
* Using [Connection] *connection_name* - the connection to use. If not
  specified the last connection used by another command is assumed.
* [Result | Results] [In] *variable* - the variable to receive the results
  of the command. If not specified, results are placed in *vault.result*.
* Giving *variable* - synonym for _Results_

Multiple argument are separated by spaces or optional commas.

*Specialized Options*

* CAS [Is] *version* - Sets the CAS version if required by operation
* Config [Is] *config* - Configuration data for the operation; may be
  mutually exclusive with `Data`
* Data [Is] *data* - Operation data if used by operation
* [Secret | Secrets] [[Is | Are]] *data* - Synonym for _Data_
* Description [Is] *text* - Description text if used by operation
* Key [Is] *key* - Key argument if used by operation
* [Meta | Metadata] [Is] *metadata* - Metadata if used by operation
* Type [Is] *type* - Type indicator if used by operation
* [Version | Ver] [Is] *version* - Version value if used by operation

*Results Structure*

In addition to the data returned by Vault, the Vault statement
adds the following attributes:

* *variable*.status - Human-readable status of the operation. If the operation
  succeeded, it will be `None`. Otherwise it will contain errors or warning reported
  by Vault, or the HTTP status.
* *variable*.vclient.url - The URL used in the operation
* *variable*.vclient.method - The HTTP method used in the operation
* *variable*.vclient.status - The HTTP return code from the operation
* *variable*.vclient.vault_index - value of the returned _X-Vault-Index_ header
* *variable*.vclient.vault_cluster - value of the returned _X-Vault-Cluster_ header
* *variable*.vclient.vault_lease_id - value of the returned _X-Vault-Lease-Id_ header

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
