"""
Vault extension to the grammar
"""

from typing import Dict, Callable

from ..builtins import bound_ops
from ..extn import VgrExtension
from ..data_dict import DataDictionary

from .vault_functions import (
    duration_to_ms,
    extract_kv_data,
    extract_kv_metadata,
    ms_to_duration
)

from .vault_stmts import (
    execute_api_delete,
    execute_api_get,
    execute_api_list,
    execute_api_patch,
    execute_api_post,
    execute_connect,
    execute_create_db_connection,
    execute_create_db_role,
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
    execute_list_db_roles,
    execute_list_kv_secrets,
    execute_list_ldap_libraries,
    execute_list_ldap_roles,
    execute_list_mounts,
    execute_list_ns,
    execute_lock_ns,
    execute_patch_kv_secret,
    execute_read_db_connection,
    execute_read_db_role,
    execute_read_kv_metadata,
    execute_read_kv_secret,
    execute_read_ldap_library,
    execute_read_ldap_role,
    execute_read_mount,
    execute_read_ns,
    execute_reset_db_connection,
    execute_rotate_db_connection_creds,
    execute_rotate_db_role_creds,
    execute_rotate_ldap_role,
    execute_undelete_kv_secret,
    execute_unlock_ns,
    execute_update_db_connection,
    execute_update_db_role,
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

* Vault [Get | Read] *path* - Send a GET to a Vault API
* Vault List *path* - Send a LIST to a Vault API
* Vault Delete *path* - Send a DELETE to a Vault API
* Vault [Post | Create | Update] *path* - Send a POST to a Vault API
* Vault Patch *path* - Send a PATCH to a Vault API

*Namespace Management*

* Vault Create Namespace *namespace* - Create a new namesapce
* Vault Read Namespace *namespace* - Read a namespace
* Vault Update Namespace *namespace* - Update a namespace
* Vault Delete Namespace *namespace* - Delete a namespace
* Vault List Namespaces [*namespace*] - List child namespaces
* Vault Lock Namespace *namespace* - Lock a namespace
* Vault Unlock Namespace *namespace* - Unlock a namespace

*Secret Engine Mount Points*

* Vault Create Mount *mount_point* - Create and configure a secrets engine
* Vault Read Mount *mount_point* - Read the configuration of a secrets engine mount
* Vault Update Mount *mount_point* - Update the configuration of a secrets engine
* Vault Delete Mount *mount_point* - Remove a secrets engine mount
* Vault List Mounts [*namespace*] - List the mount points in a namespace

*KV2 Secrets*

* Vault Create KvSecret *mount_and_path* - Create or update the KV secrets
* Vault Read KvSecret *mount_and_path* - Read the KV secrets
* Vault Read KvMetadata *mount_and_path* - Read the KV metadata
* Vault Delete KvMetadata *mount_and_path* - Delete KV metadata
* Vault Update KvSecret *mount_and_path* - Update the KV secrets data and/or metadata
* Vault Delete KvSecret *mount_and_path* - Delete a KV secret
* Vault Undelete KvSecret *mount_and_path* - Undelete a KV secret
* Vault Destroy KvSecret *mount_and_path* - Destroy a KV secret
* Vault List KvSecrets *mount_and_path* - List KV secrets at a path location
* Vault Patch KvSecret *mount_and_path* - Patch the KV secrets data and/or metadata

*LDAP Libraries Sets*

* Vault Create LdapLibrary *mount_and_set* - Create a set of LDAP credentials
* Vault Read LdapLibrary *mount_and_set* - Get the configuraiton of a set of LDAP credentials
* Vault Update LdapLibrary *mount_and_set* - Update the configuraiton of a set of LDAP credentials
* Vault Delete LdapLibrary *mount_and_set* - Remove a set of LDAP credentials
* Vault List LdapLibraries *mount_point* - List LDAP library set names

*LDAP Roles*

* Vault Create LdapRole *mount_and_role* - Create a static LDAP role
* Vault Read LdapRole *mount_and_role* - Get a static LDAP role
* Vault Update LdapRole *mount_and_role* - Update a static LDAP role
* Vault Delete LdapRole *mount_and_role* - Remove a static LDAP role
* Vault List LdapRoles *mount_point* - List static LDAP roles
* Vault Rotate LdapRole Credentials *mount_and_role* - Rotate the password of a static LDAP role

*Database Connections*

* Vault Create DbConnection *mount_and_name* - Create and configure a Database Connection
* Vault Read DbConnection *mount_and_name* - Read a Database Connection configuration
* Vault Update DbConnection *mount_and_name* - Update a Database Connection configuration
* Vault Delete DbConnection *mount_and_name* - Remove a Database Connection
* Vault List DbConnections *mount_point* - List Database Connections
* Vault Reset DbConnection *mount_and_name* - Closes a Database Connection and it's plugin and restarts it
* Vault Rotate DbConnection Credentials *mount_and_name* - Rotate the user credentials of the Database Connection

*Database Roles*

* Vault Create DbRole *mount_and_name* - Creates a Role for a Database
* Vault Read DbRole *mount_and_name* - Read a Database Role
* Vault Update DbRole *mount_and_name* - Update a Role for a Database
* Vault Delete DbRole *mount_and_name* - Remove a Database Role
* Vault List DbRoles *mount_point* - List Database Roles for a mount point
* Vault Generate DbRole Credentials *mount_and_name* - Generate a new credentials for a Database Role

*Universal Options*

* Namespace [Is] *namespace* - the namespace for the operations.
  Default namespace is used if not specified. For some operations, this
  is may be combined with other arguments as the parent namespace.
* Using [Connection] *connection_name* - the connection to use. If not
  specified the last connection used by another command is assumed.
* Giving *variable* - the variable to receive the results of the
  command. If not specified, results are placed in *vault.result*.

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
* *variable*.vclient.status_code - The HTTP return code from the operation

"""
    # This is a "nop"

STATEMENT_HANDLERS = {
    'vault_help'                   : _vault_help,
    'vault_api_delete'             : execute_api_delete,
    'vault_api_get'                : execute_api_get,
    'vault_api_list'               : execute_api_list,
    'vault_api_patch'              : execute_api_patch,
    'vault_api_post'               : execute_api_post,
    'vault_connect'                : execute_connect,
    'vault_create_db_conn'         : execute_create_db_connection,
    'vault_create_db_role'         : execute_create_db_role,
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
    'vault_list_db_roles'          : execute_list_db_roles,
    'vault_list_kv_secrets'        : execute_list_kv_secrets,
    'vault_list_ldap_libs'         : execute_list_ldap_libraries,
    'vault_list_ldap_roles'        : execute_list_ldap_roles,
    'vault_list_mounts'            : execute_list_mounts,
    'vault_list_ns'                : execute_list_ns,
    'vault_lock_ns'                : execute_lock_ns,
    'vault_patch_kv_secret'        : execute_patch_kv_secret,
    'vault_read_db_conn'           : execute_read_db_connection,
    'vault_read_db_role'           : execute_read_db_role,
    'vault_read_kv_metadata'       : execute_read_kv_metadata,
    'vault_read_kv_secret'         : execute_read_kv_secret,
    'vault_read_ldap_lib'          : execute_read_ldap_library,
    'vault_read_ldap_role'         : execute_read_ldap_role,
    'vault_read_mount'             : execute_read_mount,
    'vault_read_ns'                : execute_read_ns,
    'vault_reset_db_conn'          : execute_reset_db_connection,
    'vault_rotate_db_conn'         : execute_rotate_db_connection_creds,
    'vault_rotate_ldap_role'       : execute_rotate_ldap_role,
    'vault_rotate_db_role_creds'   : execute_rotate_db_role_creds,
    'vault_undelete_kv_secret'     : execute_undelete_kv_secret,
    'vault_unlock_ns'              : execute_unlock_ns,
    'vault_update_db_conn'         : execute_update_db_connection,
    'vault_update_db_role'         : execute_update_db_role,
    'vault_update_kv_secret'       : execute_update_kv_secret,
    'vault_update_ldap_lib'        : execute_update_ldap_library,
    'vault_update_ldap_role'       : execute_update_ldap_role,
    'vault_update_mount'           : execute_update_mount,
    'vault_update_ns'              : execute_update_ns,
}

_FUNCTIONS = {
    "DurationToMs"      : duration_to_ms,
    "ExtractKVMetadata" : extract_kv_metadata,
    "ExtractKVData"     : extract_kv_data,
    "MsToDuration"      : ms_to_duration,
}

class VaultExtension(VgrExtension):

    def initialize(self, dd: DataDictionary) -> None:
        vault_initialize(dd)

    def adds_statements(self):
        return True

    def grammar(self) -> str:
        return self.read_resource_text(__package__, 'vault.lark')

    def functions(self) -> Dict[str, Callable]:
        return _FUNCTIONS

    def statement_handlers(self) -> Dict[str, Callable]:
        return STATEMENT_HANDLERS
