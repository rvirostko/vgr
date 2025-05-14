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
from .functions import duration_to_ms, ms_to_duration
from .stmts import (
    execute_connect,
    execute_disconnect,
    execute_default_ns,
    execute_create_ns,
    execute_read_ns,
    execute_update_ns,
    execute_delete_ns,
    execute_list_ns,
    execute_lock_ns,
    execute_unlock_ns,
    execute_create_mount,
    execute_read_mount,
    execute_update_mount,
    execute_delete_mount,
    execute_list_mounts,
    execute_create_kv,
    execute_read_kv,
    execute_update_kv,
    execute_delete_kv,
    execute_list_kvs,
    execute_create_ldap_lib,
    execute_read_ldap_lib,
    execute_update_ldap_lib,
    execute_delete_ldap_lib,
    execute_list_ldap_libs,
    execute_create_ldap_secret,
    execute_read_ldap_secret,
    execute_update_ldap_secret,
    execute_delete_ldap_secret,
    execute_list_ldap_secrets,
    execute_rotate_ldap_secret,
)

STATEMENT_HANDLERS = {
    'vault_connect'            : execute_connect,
    'vault_disconnect'         : execute_disconnect,
    'vault_default_ns'         : execute_default_ns,
    'vault_create_ns'          : execute_create_ns,
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
    'vault_create_kv'          : execute_create_kv,
    'vault_read_kv'            : execute_read_kv,
    'vault_update_kv'          : execute_update_kv,
    'vault_delete_kv'          : execute_delete_kv,
    'vault_list_kvs'           : execute_list_kvs,
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
    "DurationToMs": duration_to_ms,
    "MsToDuration": ms_to_duration,
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
        with extn_grammar.open("r", encoding="utf-8") as f:
            g = f.read()
        g += 'vault_from: "Vault"i? VAULT_TARGET\n'
        return g + 'VAULT_TARGET: ' + ' | '.join(tuple(f'"{t}"i' for t in _TARGETS))

    def functions(self) -> Dict[str, Callable]:
        return _FUNCTIONS

    def statement_handlers(self) -> Dict[str, Callable]:
        return STATEMENT_HANDLERS
