# # Transfer
# def visit_kv_mount(namespace :str, mount_point :str) -> None:
#     """
#     Produces a list of secrets and sub-paths in a Key Value store
#     Returns: A list of dictionaries where each dictionary represents a path.
#         In addition to Vault's metadata, we add these keys.
#             - "path": The full path.
#             - "name": The last component of the path.
#             - "parent": The parent part of the path (None for the root path).
#             - "secrets": List of secrets at the path.
#             - "sub_paths": List of sub-paths under the path.
#     """
#     LOG.dbg(f'visit_kv_mount({namespace}, {mount_point}, {type})')
#     paths_to_process = get_kv_subpaths(namespace, mount_point)
#     # We "visit" the mount's root, which will have no secrets, just our first level of the paths (if any)
#     visit_kv('', paths_to_process)
#     # Follow the paths of the "tree", visiting at each level
#     # TODO use "deque"?
#     while paths_to_process:
#         path = paths_to_process.pop(0)
#         secrets = get_kv_secrets(namespace, mount_point, path)
#         sub_paths = get_kv_subpaths(namespace, mount_point, '/' + path)
#         metadata = get_kv_metadata(namespace, mount_point, '/' + path)
#         visit_kv(mount_point, path, sub_paths, metadata, secrets)
#         # Push the sub paths (after making them fully qualified) at the head of our queue
#         if sub_paths: paths_to_process = [ path + '/' + p for p in sub_paths] + paths_to_process

# def get_kv_secrets(namespace: str, mount_point: str, path: str='') -> list:
#     try:
#         subkeys = vault_get(encode_url(f'/v1/{mount_point}/subkeys/{path}') + '?depth=1', namespace).get('data', {}).get('subkeys', {})
#         return [key for key in subkeys.keys()] if subkeys else []
#     except HTTPError as e:
#         if e.code == HTTPStatus.NOT_FOUND: return []
#         raise e

# def get_kv_subpaths(namespace: str, mount_point: str, path: str='') -> list:
#     LOG.dbg(f'get_kv_subpaths({namespace}, {mount_point}, {path})')
#     try:
#         paths = vault_list(encode_url(f'/v1/{mount_point}/metadata{path}'), namespace).get('data', {}).get('keys', [])
#         return sorted(list(set([f"{path.rstrip('/')}" for path in paths])))
#     except HTTPError as e:
#         if e.code == HTTPStatus.NOT_FOUND: return []
#         raise e

# def get_kv_metadata(namespace: str, mount_point: str, path: str='') -> dict:
#     LOG.dbg(f'get_kv_metadata({namespace}, {mount_point}, {path})')
#     try:
#         return vault_get(encode_url(f'/v1/{mount_point}/metadata{path}'), namespace).get('data', {})
#     except HTTPError as e:
#         if e.code == HTTPStatus.NOT_FOUND: return {}
#         raise e

# def visit_kv(mount_point: str, path: str, sub_paths: list=[], metadata: dict={}, secrets: list=[]) -> None:
#     LOG.dbg(f'visit_kv({path}, {sub_paths}, {metadata}, {secrets})')
#     context: str = 'kv'
#     try:
#         # The metadata is what came back from Vault, and we are just going to pass it on
#         kv: dict = dict(metadata)
#         # We add these values to the metadata
#         kv['mount_point'] = mount_point
#         kv['path'] = '/' + path
#         kv['parent'] = None if not path else '/' + '/'.join(path.split('/')[:-1])
#         # Extract the last component of the path
#         kv['name'] = path.split('/')[-1]
#         kv['secrets'] = secrets
#         kv['sub_paths'] = sub_paths
#         DD[context] = kv
#         if filter_target(context): format_output()
#     finally:
#         if context in DD: DD.pop(context)

# def visit_aws_mount(namespace: str, mount_point: str) -> None:
#     LOG.dbg(f'vist_aws_mount({namespace}, {mount_point})')
#     config = vault_get(encode_url(f'/v1/{mount_point}/config/root'), namespace).get('data', {})
#     for role in get_aws_roles(namespace, mount_point):
#         visit_aws_role(namespace, mount_point, role, config)

# def visit_aws_role(namespace: str, mount_point: str, role: str, config: dict) -> None:
#     context: str = "aws"
#     try:
#         aws: dict = vault_get(encode_url(f'/v1/{mount_point}/roles/{role}'), namespace).get('data', {})
#         aws.update(config)
#         aws['mount_point'] = mount_point
#         aws['name'] = role
#         DD[context] = aws
#         if filter_target(context): format_output()
#     except HTTPError as e:
#         # 404 means no longer exists
#         if e.code != HTTPStatus.NOT_FOUND: raise e
#     finally:
#         if context in DD: DD.pop(context)

# def get_aws_roles(namespace: str, mount_point: str) -> List[str]:
#     try:
#         return sorted(vault_list(encode_url(f'/v1/{mount_point}/roles'), namespace).get('data', {}).get('keys', []))
#     except HTTPError as e:
#         # 404 means no roles
#         if e.code == HTTPStatus.NOT_FOUND: return []
#         raise e

# def fix_dn(dn: str) -> str:
#     return None if dn is None else dn.replace(', ', ',')

# def visit_ldap_mount(namespace: str, mount_point: str) -> None:
#     LOG.dbg(f'vist_ldap_mount({namespace}, {mount_point})')
#     context: str = "ldap"
#     config = vault_get(encode_url(f'/v1/{mount_point}/config'), namespace).get('data', {})
#     try:
#         config['type'] = 'management'
#         config['name'] = '' # used for name within the mount point, so no meaning here
#         config['mount_point'] = mount_point
#         # clean dn up to usable form
#         config['binddn'] = fix_dn(config.get('binddn'))
#         config['userdn'] = fix_dn(config.get('userdn'))
#         # standardize attrs for use across types
#         config['password_rotation'] = config.get('last_bind_password_rotation')
#         config['dn'] = config.get('binddn')
#         DD[context] = config
#         if filter_target(context): format_output()
#         # NB: Do not nest filtering! TODO - maybe?
#         visit_ldap_static_roles(namespace, mount_point, config)
#         visit_ldap_libraries(namespace, mount_point, config)
#     finally:
#         if context in DD: DD.pop(context)

# def visit_ldap_static_roles(namespace: str, mount_point: str, mount_config: dict) -> None:
#     LOG.dbg(f'visit_ldap_static_roles(namespace={namespace}, mount_point={mount_point})')
#     context: str = "ldap"
#     try:
#         roles = vault_list(f'/v1/{mount_point}/static-role', namespace).get('data', {})
#         for role_name in roles.get('keys', []):
#             LOG.dbg(f'{role_name}')
#             role_data = vault_get(f'/v1/{mount_point}/static-role/{role_name}', namespace).get('data')
#             role_data['type'] = 'static'
#             role_data['name'] = role_name
#             # dup some data from the mount for filtering
#             role_data['password_policy'] = mount_config.get('password_policy')
#             role_data['schema'] = mount_config.get('schema')
#             role_data['url'] = mount_config.get('url')
#             # clean dn up to usable form
#             role_data['dn'] = fix_dn(role_data.get('dn'))
#             # standardize attrs for use across types
#             role_data['password_rotation'] = role_data.get('last_vault_rotation')
#             DD[context] = role_data
#             if filter_target(context): format_output()
#     except HTTPError as e:
#         # 404 means no roles
#         if e.code != HTTPStatus.NOT_FOUND: raise e
#     finally:
#         if context in DD: DD.pop(context)

# def visit_ldap_libraries(namespace: str, mount_point: str, mount_config: dict) -> None:
#     LOG.dbg(f'visit_ldap_libraries(namespace={namespace}, mount_point_name={mount_point}')
#     context: str="ldap"
#     try:
#         libraries = vault_list(f'/v1/{mount_point}/library', namespace).get('data', {})
#         for library_name in libraries.get('keys', []):
#             LOG.dbg(f'{library_name}')
#             library_data = vault_get(f'/v1/{mount_point}/library/{library_name}', namespace).get('data', {})
#             library_data['type'] = 'library'
#             library_data['name'] = library_name
#             # dup some data from the mount for filtering
#             library_data['password_policy'] = mount_config.get('password_policy')
#             library_data['schema'] = mount_config.get('schema')
#             library_data['url'] = mount_config.get('url')
#             # Because we want to deal with the LDAP accounts themselves, not just the
#             # library as an entity, we flatten the array of account names
#             for acct_name in library_data.get('service_account_names', []):
#                 LOG.dbg(f'{acct_name}')
#                 # This may not be universal, but good enough for how
#                 # the way accounts are currently configured
#                 library_data['dn'] = f'CN={acct_name},{mount_config.get("userdn","")}'
#                 # TODO For password_rotation info we will need to talk to AD
#                 DD[context] = library_data
#                 if filter_target(context): format_output()
#     except HTTPError as e:
#         # 404 means no roles
#         if e.code != HTTPStatus.NOT_FOUND: raise e
#     finally:
#         if context in DD: DD.pop(context)

# def visit_database_mount(namespace :str, mount_point :str) -> None:
#     if TARGET == 'db': visit_database_connections(namespace, mount_point)
#     elif TARGET == 'db_role': visit_database_roles(namespace, mount_point)
#     else: raise ValueError(f'TARGET={TARGET} not mapped correctly')

# GEN_DB_PLUGIN_SUFFIX = '-database-plugin'
# def visit_database_connections(namespace :str, mount_point :str) -> None:
#     LOG.dbg(f'vist_database_connections({namespace}, {mount_point})')
#     context: str="db"
#     try:
#         config = vault_list(f'/v1/{mount_point}/config', namespace).get('data', {})
#         for conn_name in config.get('keys', []):
#             LOG.dbg(f'{conn_name}')
#             conn_config = vault_get(f'/v1/{mount_point}/config/{conn_name}', namespace).get('data', {})
#             conn_config['name'] = conn_name
#             plugin: str = conn_config.get('plugin_name', '')
#             if plugin.endswith(GEN_DB_PLUGIN_SUFFIX):
#                 conn_config['type'] = plugin[:-len(GEN_DB_PLUGIN_SUFFIX)]
#             else:
#                 conn_config['type'] = plugin
#             DD[context] = conn_config
#             if filter_target(context): format_output()
#     finally:
#         if context in DD: DD.pop(context)

# def visit_database_roles(namespace :str, mount_point :str) -> None:
#     LOG.dbg(f'vist_database_roles({namespace}, {mount_point})')
#     context: str="db_role"
#     try:
#         for end_point, role_type in [('roles', 'dynamic'), ('static-roles', 'static')]:
#             roles = vault_list(f'/v1/{mount_point}/{end_point}', namespace).get('data', {})
#             for role_name in roles.get('keys', []):
#                 LOG.dbg(f'{role_name} : {role_type}')
#                 role_config = vault_get(f'/v1/{mount_point}/{end_point}/{role_name}', namespace).get('data', {})
#                 role_config['name'] = role_name
#                 role_config['type'] = role_type
#                 DD[context] = role_config
#                 if filter_target(context): format_output()
#     finally:
#         if context in DD: DD.pop(context)
