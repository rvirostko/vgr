"""
Implementations of Vault Statements
"""

# vault_default_ns : "Vault"i "DefaultNamespace"i expr _SEMICOLON?
# vault_create_ns : "Vault"i "CreateNamespace"i expr vault_args _SEMICOLON?
# vault_read_ns   : "Vault"i "ReadNamespace"i expr vault_args _SEMICOLON?
# vault_update_ns : "Vault"i "UpdateNamespace"i expr vault_args _SEMICOLON?
# vault_delete_ns : "Vault"i "DeleteNamespace"i expr vault_args _SEMICOLON?
# vault_list_ns   : "Vault"i "ListNamespaces"i expr? vault_args _SEMICOLON?
# vault_lock_ns   : "Vault"i "LockNamespace"i expr vault_args _SEMICOLON?
# vault_unlock_ns : "Vault"i "UnlockNamespace"i expr vault_args _SEMICOLON?

# // Secrete Engine Mount Points
# vault_create_mount : "Vault"i "CreateMount"i expr vault_args _SEMICOLON?
# vault_read_mount   : "Vault"i "ReadMount"i expr vault_args _SEMICOLON?
# vault_update_mount : "Vault"i "UpdateMount"i expr vault_args _SEMICOLON?
# vault_delete_mount : "Vault"i "DeleteMount"i expr vault_args _SEMICOLON?
# vault_list_mounts  : "Vault"i "ListMounts"i expr vault_args _SEMICOLON?

# // KV2 Secrets
# vault_create_kv : "Vault"i "CreateKvSecret"i expr vault_args _SEMICOLON?
# vault_read_kv   : "Vault"i "ReadKvSecret"i expr vault_args _SEMICOLON?
# vault_update_kv : "Vault"i "UpdateKvSecret"i expr vault_args _SEMICOLON?
# vault_delete_kv : "Vault"i "DeleteKvSecret"i expr vault_args _SEMICOLON?
# vault_list_kvs  : "Vault"i "ListKvSecrets"i expr vault_args _SEMICOLON?

# // LDAP Libraries Secrets
# vault_create_ldap_lib : "Vault"i "CreateLdapLibrary"i expr vault_args _SEMICOLON?
# vault_read_ldap_lib   : "Vault"i "ReadLdapLibrary"i expr vault_args _SEMICOLON?
# vault_update_ldap_lib : "Vault"i "UpdateLdapLibrary"i expr vault_args _SEMICOLON?
# vault_delete_ldap_lib : "Vault"i "DeleteLdapLibrary"i expr vault_args _SEMICOLON?
# vault_list_ldap_libs  : "Vault"i "ListLdapLibraries"i expr vault_args _SEMICOLON?

# // LDAP Static Secrets
# vault_create_ldap_secret : "Vault"i "CreateLdapSecret"i expr vault_args _SEMICOLON?
# vault_read_ldap_secret   : "Vault"i "ReadLdapSecret"i expr vault_args _SEMICOLON?
# vault_update_ldap_secret : "Vault"i "UpdateLdapSecret"i expr vault_args _SEMICOLON?
# vault_delete_ldap_secret : "Vault"i "DeleteLdapSecret"i expr vault_args _SEMICOLON?
# vault_list_ldap_secrets  : "Vault"i "ListLdapSecrets"i expr vault_args _SEMICOLON?
# vault_rotate_ldap_secret : "Vault"i "RotateLdapSecret"i expr vault_args _SEMICOLON?
