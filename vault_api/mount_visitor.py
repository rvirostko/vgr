"""
Visitor pattern for Secrets Mounts
"""

from typing import Any, Dict

from .util import vault_normalize_path
from .vclient import VaultClient

class VaultMountVisitor:
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
                mount_info['name'] = name
                # TODO if kv, then send in kv or kv1
                self.visit_mount(name, namespace, mount_info.get('type', ''), mount_info)
        finally:
            self._namespace = None

    def visit_mount_details(self, namespace: str, name: str, mtype: str) -> None:
        if mtype == 'aws':
            return
        if mtype == 'cubbyhole':
            return
        if mtype == 'databse':
            return
        if mtype == 'identity':
            return
        if mtype == 'sys':
            return
        if mtype == 'kv':
            # TODO should look for "options.version == 2" vs 1
            return
        if mtype == 'ldap':
            return
        raise NotImplementedError(f'Mount type {repr(mtype)} not handled')

    #pylint: disable=unused-argument
    def visit_mount(self, namespace: str, name: str, mtype: str, data: Dict[str, Any]) -> None:
        """
        Called to visit the generic information about the mount.
        If you wish more information on the mount, call visit_mount_details().
        The default implementation does exactly that.
        """
        self.visit_mount_details(namespace, name, mtype)
    #pylint: enable=unused-argument

    def visit_aws_mount(self) -> None:
        pass

    def visit_cubbyhole_mount(self) -> None:
        pass

    def visit_database_mount(self) -> None:
        pass

    def visit_identity_mount(self) -> None:
        pass

    def visit_sys_mount(self) -> None:
        pass

    def visit_kv_mount(self) -> None:
        pass

    def visit_ldap_mount(self) -> None:
        pass
