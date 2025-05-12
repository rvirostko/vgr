"""
Visitor pattern for Secrets Mounts
"""

from typing import Any, Dict

from .util import vault_normalize_path, encode_url
from .vclient import VaultClient

class VaultMountVisitor:
    _GEN_DB_PLUGIN_SUFFIX = '-database-plugin'

    def __init__(self, client: VaultClient):
        self._client = client
        self._namespace = None

    @property
    def client(self) -> VaultClient:
        return self._client

    def visit_mounts(self, namespace: str) -> None:
        try:
            self._namespace = namespace
            data = self.client.list_mounts(namespace).get('data', {})
            for key in sorted(data.keys()):
                mount_info = data.get(key)
                name = vault_normalize_path(key)
                mtype = mount_info.get('type', '')
                # kv -> ver2; kv1 -> ver1
                if mtype == 'kv':
                    if int(mount_info.get('options', {}).get('version', 1)) != 2:
                        mtype = 'kv1'
                self.visit_mount(name, namespace, mtype, mount_info)
        finally:
            self._namespace = None

    #pylint: disable=unused-argument
    def visit_mount(self, namespace: str, name: str, mtype: str, data: Dict[str, Any]) -> None:
        """
        Called to visit the generic information about the mount.
        If you wish more information on the mount, call visit_mount_details().
        The default implementation does exactly that.
        """
        self.visit_mount_details(namespace, name, mtype)
    #pylint: enable=unused-argument

    def visit_mount_details(self, namespace: str, mount_point: str, mtype: str) -> None:
        if mtype == 'aws':
            # TODO why is this one different?
            config = self.client.do_get(encode_url(f'/v1/{mount_point}/config/root'), namespace).get('data', {})
            self.visit_aws_mount(namespace, mount_point, config)
        elif mtype == 'database':
            config = self.client.do_list(encode_url(f'/v1/{mount_point}/config'), namespace).get('data', {})
            self.visit_database_mount(namespace, mount_point, config)
        elif mtype == 'kv':
            config = self.client.read_kv2_config(mount_point, namespace).get('data', {})
            self.visit_kv_mount(namespace, mount_point, config)
        elif mtype == 'ldap':
            config = self.client.do_get(encode_url(f'/v1/{mount_point}/config'), namespace).get('data', {})
            self.visit_ldap_mount(namespace, mount_point, config)
        else:
            raise NotImplementedError(f'Mount type {repr(mtype)} not handled')

    def visit_aws_mount(self, namespace: str, mount_point: str, config: Dict[str, Any]) -> None:
        """
        Called to visit an AWS mount.
        Call visit_aws_roles() to visit the AWS roles individually and in detail.
        """

    def visit_aws_roles(self, namespace: str, mount_point: str, config: Dict[str, Any]) -> None:
        roles = self.client.do_list(encode_url(f'/v1/{mount_point}/roles'), namespace).get('data', {}).get('keys', [])
        for role in sorted(roles):
            data = self.client.do_get(encode_url(f'/v1/{mount_point}/roles/{role}'), namespace).get('data', {})
            self.visit_aws_role(namespace, mount_point, config, role, data)

    #pylint: disable=unused-argument
    def visit_aws_role(self, namespace: str, mount_point: str, config: Dict[str, Any],
                       role: str, data: Dict[str, Any]) -> None:
        """
        Called to visit an AWS role
        """
    #pylint: enable=unused-argument

    #pylint: disable=unused-argument
    def visit_database_mount(self, namespace :str, mount_point :str, config: Dict[str, Any]) -> None:
        """
        Called to visit a database mount.
        From here you should either call visit_database_connections() or visit_database_roles().
        """
    #pylint: enable=unused-argument

    def visit_database_connections(self, namespace :str, mount_point :str, config: Dict[str, Any]) -> None:
         """
         Call this method to visit all the database connections associated with the mount point.
         """
         for conn_name in config.get('keys', []):
            conn = self.client.do_get(encode_url(f'/v1/{mount_point}/config/{conn_name}'), namespace).get('data', {})
            self.visit_database_connection(namespace, mount_point, config, conn_name, conn)

    #pylint: disable=unused-argument
    def visit_database_connection(self, namespace :str, mount_point :str, config: Dict[str, Any],
                                  name: str, conn: Dict[str, Any]) -> None:
        """
        Called to visit a database connection
        Call visit_database_roles() to get details on configured roles
        """
    #pylint: enable=unused-argument

    def visit_database_roles(self, namespace :str, mount_point :str, config: Dict[str, Any]) -> None:
        for end_point, role_type in [('roles', 'dynamic'), ('static-roles', 'static')]:
            roles = self.client.do_list(encode_url(f'/v1/{mount_point}/{end_point}'), namespace).get('data', {})
            for role_name in roles.get('keys', []):
                data = self.client.do_get(encode_url(f'/v1/{mount_point}/{end_point}/{role_name}'), namespace).get('data', {})
                self.visit_database_role(namespace, mount_point, config, role_name, role_type, data)

    #pylint: disable=unused-argument
    def visit_database_role(self, namespace :str, mount_point :str, config: Dict[str, Any],
                            name: str, role_type: str, role: Dict[str, Any]) -> None:
        """
        Called to visit a database role
        """
    #pylint: enable=unused-argument

    def visit_ldap_mount(self, namespace: str, mount_point: str, config: Dict[str, Any]) -> None:
        """
        Called to visit an LDAP mount.
        Call this visit_ldap_static_roles() and/or visit_ldap_libraries()
        for details.
        """

    def visit_ldap_static_roles(self, namespace: str, mount_point: str, config: Dict[str, Any]) -> None:
        roles = self.client.do_list(encode_url(f'/v1/{mount_point}/static-role'), namespace).get('data', {})
        for role_name in roles.get('keys', []):
            role = self.client.do_get(encode_url(f'/v1/{mount_point}/static-role/{role_name}'), namespace).get('data')
            self.visit_ldap_static_role(namespace, mount_point, config, role_name, role)

    #pylint: disable=unused-argument
    def visit_ldap_static_role(self, namespace: str, mount_point: str, config: Dict[str, Any],
                               name: str, role: Dict[str, Any]) -> None:
        """
        Called to visit an LDAP static role
        """
    #pylint: enable=unused-argument

    def visit_ldap_libraries(self, namespace: str, mount_point: str, config: Dict[str, Any]) -> None:
        libraries = self.client.do_list(encode_url(f'/v1/{mount_point}/library'), namespace).get('data', {})
        for library_name in libraries.get('keys', []):
            library = self.client.do_get(encode_url(f'/v1/{mount_point}/library/{library_name}'), namespace).get('data', {})
            self.visit_ldap_static_role(namespace, mount_point, config, library_name, library)

    #pylint: disable=unused-argument
    def visit_ldap_library(self, namespace: str, mount_point: str, config: Dict[str, Any],
                           name: str, library: Dict[str, Any]) -> None:
        """
        Called to visit an LDAP library
        """
    #pylint: enable=unused-argument

    #pylint: disable=unused-argument
    def visit_kv_mount(self, namespace: str, mount_point: str, config: Dict[str, Any]) -> None:
        """
        Called to visit a KV2 secret store
        Call visit_kv_paths() to get details of the secret store's contents
        """
    #pylint: enable=unused-argument

    def visit_kv_paths(self, namespace: str, mount_point: str, config: Dict[str, Any]) -> None:
        paths_to_process = self.client.list_kv2_subpaths(namespace, mount_point)
        # We "visit" the mount's root, which will have no secrets, just our first level of the paths (if any)
        self.visit_kv_path(namespace, mount_point, config, '', paths_to_process, {}, [])
        # Follow the paths of the "tree", visiting at each level
        while paths_to_process:
            path = paths_to_process.pop(0)
            subkeys = self.client.get_kv2_subkeys(namespace, mount_point, path)
            sub_paths = self.client.list_kv2_subpaths(namespace, mount_point, path)
            metadata = self.client.read_kv2_metadata(namespace, mount_point, path)
            self.visit_kv_path(namespace, mount_point, config, path, sub_paths, metadata, subkeys)
            # Push the sub paths (after making them fully qualified) at the head of our queue
            if sub_paths: paths_to_process = [ path + '/' + p for p in sub_paths] + paths_to_process

    #pylint: disable=unused-argument
    def visit_kv_path(self, namespace: str, mount_point: str, config: Dict[str, Any],
                      path: str, sub_paths: list, metadata: dict, subkeys: list) -> None:
        """
        Called to visit a KV path.
        No secret values are present in the data.
        """
    #pylint: enable=unused-argument
