import argparse
from typing import Any, Dict

from vault_api import VaultClient, VaultNamespaceVisitor, VaultMountVisitor

from data_xtract import QueryFilter

class TestQueryFilter(QueryFilter):
    def __init__(self):
        self._dd = {}

    def filter_intermediate(self) -> bool:
        print('intermediate :', repr(self._dd.keys()))
        return True

    def filter_target(self, data: Any) -> bool:
        print('target :', repr(self._dd.keys()))
        return True

    def set_data(self, key: str, data: Any) -> None:
        print('set :', key)
        self._dd[key] = data

    def unset_data(self, key: str) -> None:
        print('unset :', key)
        self._dd.pop(key, None)

class VaultWalker(VaultNamespaceVisitor, VaultMountVisitor):
    _FAKE_ROOT_JSON = {
        "name": "",
        "path": "/",
        "id": "00000",
      }

    # Key the mount type, and the value is possible targets
    # So if we run into a "database" mount, and are looking for db_role, we should
    # walk it.
    _MOUNT_TO_TARGET = {
        'aws':      ['aws'],
        'database': ['db', 'db_role'],
        'kv':       ['kv'],
        'ldap':     ['ldap']
    }

    def __init__(self, client, qfilter: QueryFilter, target: str):
        super().__init__(client)
        self._client = client
        self._qfilter = qfilter
        self._target = target

    def walk(self) -> None:
        self.visit_root_namespace()

    def visit_root_namespace(self) -> None:
        self._visit_mounts('', self._FAKE_ROOT_JSON.copy())

    def visit_namespace(self, namespace: str, data: Dict[str, Any]) -> None:
        data['name'] = namespace
        self._visit_mounts(namespace, data)

    def _visit_mounts(self, namespace: str, data: Dict[str, Any]) -> None:
        try:
            data['namespace'] = namespace
            self._qfilter.set_data('ns', data)
            if self._target == 'ns':
                self._qfilter.filter_target(data)
            else:
                if self._qfilter.filter_intermediate():
                    self.visit_mounts(namespace)
            self.visit_namespace_children(namespace)
        finally:
            self._qfilter.unset_data('ns')

    def visit_mount(self, namespace: str, name: str, mtype: str, data: Dict[str, Any]) -> None:
        try:
            self._qfilter.set_data('mount', data)
            if self._target == 'mount':
                self._qfilter.filter_target(data)
            else:
                if self._qfilter.filter_intermediate():
                    if mtype in self._MOUNT_TO_TARGET.get(self._target, []):
                        self.visit_mount_details(namespace, name, mtype)
        finally:
            self._qfilter.unset_data('mount')

#import os
#url = os.environ.get("VAULT_ADDR")
#token = os.environ.get("VAULT_TOKEN")
#    if not url or not token:
#        raise RuntimeError("VAULT_ADDR and VAULT_TOKEN must be set in the environment")

def main():
    parser = argparse.ArgumentParser(description='test')
    parser.add_argument(
        "--target", choices=['ns', 'mount', 'aws', 'kv', 'ldap', 'db', 'db_role'],
        default="mount", help="Limit recursion depth"
    )
    args = parser.parse_args()
    url = 'http://127.0.0.1:8200'
    token = 'hvs.mVwhVUmYjv0wlpdQFOZy6DZo'
    client = VaultClient(url, token)

    VaultWalker(client, TestQueryFilter(), args.target).walk()

if __name__ == "__main__":
    main()
