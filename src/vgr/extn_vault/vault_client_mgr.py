"""
Manage named VaultClient instances
"""

from typing import Optional, Dict

from .vault_client import VaultClient

class VaultClientManager:

    def __init__(self):
        self._connections: Dict[str, VaultClient] = {}

    def connect(self, name: str, addr: str=None, token: str=None) -> VaultClient:
        """Create and store a VaultClient under the given name."""
        name = self._normalize_name(name)
        if addr is None: raise ValueError('Vault address must be provided')
        # if we had one previously, close it
        self.disconnect(name)
        client = VaultClient(addr, token)
        client.open()
        self._connections[name] = client
        return client

    def disconnect(self, name: Optional[str] = None) -> None:
        """Remove a named connection. No error if it does not exist."""
        name = self._normalize_name(name)
        if name in self._connections:
            self._connections.pop(name).close()

    def get_connection(self, name: Optional[str] = None) -> VaultClient:
        """Return the VaultClient for the given name, creating it from env if needed."""
        name = self._normalize_name(name)
        return self._connections[name] if name in self._connections else self.connect(name)

    def _normalize_name(self, name: Optional[str]) -> str:
        if name is None or name.isspace():
            raise ValueError('Missing name for Vault connection')
        return name.strip()
