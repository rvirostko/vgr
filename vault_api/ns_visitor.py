"""
Visitor pattern for Namespaces
"""

from typing import Any, Dict

from .vclient import VaultClient

class VaultNamespaceVisitor:
    def __init__(self, client: VaultClient):
        self._client = client

    @property
    def client(self) -> VaultClient:
        return self._client

    def visit_namespaces(self) -> None:
        return self.visit_root_namespace()

    def visit_namespace_children(self, namespace: str) -> None:
        data = self.client.list_namespace(namespace).get('data', {})
        info = data.get('key_info')
        for key in sorted(data.get('keys', [])):
            if not self.visit_namespace(key, info.get(key)): return

    def visit_root_namespace(self) -> None:
        """
        NB: To visit recursively, just call visit_namespace_children() with the namespace argument.
        """

    #pylint: disable=unused-argument
    def visit_namespace(self, namespace: str, data: Dict[str, Any]) -> None:
        """
        NB: To visit recursively, just call visit_namespace_children() with the namespace argument.
        """
    #pylint: enable=unused-argument
