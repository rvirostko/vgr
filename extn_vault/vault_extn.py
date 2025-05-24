"""
Vault extension to the grammar
"""

from typing import Dict, Callable
from pathlib import Path

from extn import VgrExtension
from data_dict import DataDictionary

from .dd_consts import (
    VAULT_PREFIX,
    DEFAULT_NS_PATH,
    DEFAULT_RESULT_PATH,
    DEFAULT_CONN_PATH,
)
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
    execute_create_kv_secret,
    execute_create_ldap_lib,
    execute_create_ldap_secret,
    execute_create_mount,
    execute_create_ns,
    execute_default_ns,
    execute_delete_kv_secret,
    execute_delete_ldap_lib,
    execute_delete_ldap_secret,
    execute_delete_mount,
    execute_delete_ns,
    execute_disconnect,
    execute_list_kv_secrets,
    execute_list_ldap_libs,
    execute_list_ldap_secrets,
    execute_list_mounts,
    execute_list_ns,
    execute_lock_ns,
    execute_patch_kv_secret,
    execute_read_kv_metadata,
    execute_read_kv_secret,
    execute_read_ldap_lib,
    execute_read_ldap_secret,
    execute_read_mount,
    execute_read_ns,
    execute_rotate_ldap_secret,
    execute_unlock_ns,
    execute_update_kv_secret,
    execute_update_ldap_lib,
    execute_update_ldap_secret,
    execute_update_mount,
    execute_update_ns,
)

STATEMENT_HANDLERS = {
    'vault_api_delete'         : execute_api_delete,
    'vault_api_get'            : execute_api_get,
    'vault_api_list'           : execute_api_list,
    'vault_api_patch'          : execute_api_patch,
    'vault_api_post'           : execute_api_post,
    'vault_connect'            : execute_connect,
    'vault_create_ns'          : execute_create_ns,
    'vault_default_ns'         : execute_default_ns,
    'vault_disconnect'         : execute_disconnect,
    'vault_read_ns'            : execute_read_ns,
    'vault_update_ns'          : execute_update_ns,
    'vault_delete_ns'          : execute_delete_ns,
    'vault_list_ns'            : execute_list_ns,
    'vault_lock_ns'            : execute_lock_ns,
    'vault_unlock_ns'          : execute_unlock_ns,
    'vault_create_mount'       : execute_create_mount,
    'vault_read_mount'         : execute_read_mount,
    'vault_update_mount'       : execute_update_mount,
    'vault_delete_mount'       : execute_delete_mount,
    'vault_list_mounts'        : execute_list_mounts,
    'vault_create_kv_secret'   : execute_create_kv_secret,
    'vault_read_kv_secret'     : execute_read_kv_secret,
    'vault_read_kv_metadata'   : execute_read_kv_metadata,
    'vault_update_kv_secret'   : execute_update_kv_secret,
    'vault_delete_kv_secret'   : execute_delete_kv_secret,
    'vault_list_kv_secrets'    : execute_list_kv_secrets,
    'vault_patch_kv_secret'    : execute_patch_kv_secret,
    'vault_create_ldap_lib'    : execute_create_ldap_lib,
    'vault_read_ldap_lib'      : execute_read_ldap_lib,
    'vault_update_ldap_lib'    : execute_update_ldap_lib,
    'vault_delete_ldap_lib'    : execute_delete_ldap_lib,
    'vault_list_ldap_libs'     : execute_list_ldap_libs,
    'vault_create_ldap_secret' : execute_create_ldap_secret,
    'vault_read_ldap_secret'   : execute_read_ldap_secret,
    'vault_update_ldap_secret' : execute_update_ldap_secret,
    'vault_delete_ldap_secret' : execute_delete_ldap_secret,
    'vault_list_ldap_secrets'  : execute_list_ldap_secrets,
    'vault_rotate_ldap_secret' : execute_rotate_ldap_secret,
}

_TARGETS = ('ns', 'mount', 'aws', 'kv', 'ldap', 'db', 'db_role')

_FUNCTIONS = {
    "DurationToMs"      : duration_to_ms,
    "ExtractKVMetadata" : extract_kv_metadata,
    "ExtractKVData"     : extract_kv_data,
    "MsToDuration"      : ms_to_duration,
}

class VaultExtension(VgrExtension):

    def initialize(self, dd: DataDictionary) -> None:
        dd.add_immutable_prefix(VAULT_PREFIX)
        dd.set_var('', *DEFAULT_NS_PATH)
        dd.set_var(None, *DEFAULT_RESULT_PATH)
        dd.set_var(None, *DEFAULT_CONN_PATH)

    def extends_select(self):
        return True

    def adds_statements(self):
        return True

    def grammar(self) -> str:
        extn_grammar = Path(__file__).parent / 'vault.ebnf'
        with extn_grammar.open('r', encoding='utf-8') as f:
            g = f.read()
        g += 'vault_from: "Vault"i VAULT_TARGET\n'
        return g + 'VAULT_TARGET: ' + ' | '.join(tuple(f'"{t}"i' for t in _TARGETS))

    def functions(self) -> Dict[str, Callable]:
        return _FUNCTIONS

    def statement_handlers(self) -> Dict[str, Callable]:
        return STATEMENT_HANDLERS
