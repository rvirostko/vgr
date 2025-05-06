"""
Test
"""

from typing import Dict, Callable
from pathlib import Path

from lark import Tree

from extn import VgrExtension
from data_dict import DataDictionary
from evaluate import eval_to_str

from .functions import duration_to_ms, ms_to_duration

def execute_default_ns(dd: DataDictionary, statement: Tree) -> None:
    ns: str = eval_to_str(dd, statement.children[0], 'Default Namespace', True)
    dd.set_var('' if ns is None or ns.isspace() else ns.strip(), *_DEFAULT_NS_PATH)

STATEMENT_HANDLERS = {
    'vault_default_ns' : execute_default_ns,
#    'vault_create_ns' : execute_create_ns,
#    'vault_read_ns'   : execute_read_ns,
#    'vault_update_ns' : execute_update_ns,
#    'vault_delete_ns' : execute_delete_ns,
#    'vault_list_ns'   : execute_list_ns,
#    'vault_lock_ns'   : execute_lock_ns,
#    'vault_unlock_ns' : execute_unlock_ns,
}

# 'vault_create_mount' : execute_
# 'vault_read_mount'   : execute_
# 'vault_update_mount' : execute_
# 'vault_delete_mount' : execute_
# 'vault_list_mounts'  : execute_

# 'vault_create_kv' : execute_
# 'vault_read_kv'   : execute_
# 'vault_update_kv' : execute_
# 'vault_delete_kv' : execute_
# 'vault_list_kvs'  : execute_

# 'vault_create_ldap_lib' : execute_
# 'vault_read_ldap_lib'   : execute_
# 'vault_update_ldap_lib' : execute_
# 'vault_delete_ldap_lib' : execute_
# 'vault_list_ldap_libs'  : execute_

# 'vault_create_ldap_secret' : execute_
# 'vault_read_ldap_secret'   : execute_
# 'vault_update_ldap_secret' : execute_
# 'vault_delete_ldap_secret' : execute_
# 'vault_list_ldap_secrets'  : execute_
# 'vault_rotate_ldap_secret' : execute_

_TARGETS = ('ns', 'mount', 'aws', 'kv', 'ldap', 'db', 'db_role')

_VAULT_PREFIX = 'vault'
_DEFAULT_NS_PATH = (_VAULT_PREFIX, 'default_ns')

_FUNCTIONS = {
  "DurationToMs": duration_to_ms,
  "MsToDuration": ms_to_duration,
}

class VaultExtension(VgrExtension):

    def initialize(self, dd: DataDictionary) -> None:
        dd.add_immutable_prefix('vault')
        dd.set_var('', *_DEFAULT_NS_PATH)

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
