"""
Wrappers around ldap3 for managing
LDAP clients and executing operations
"""

from typing import Optional, Dict
import logging

from ldap3 import Server, Connection, ALL, ALL_ATTRIBUTES
from ldap3.core.exceptions import LDAPException, LDAPExceptionError

# Testing
# LDAP Server Information (read-only access):
# Server: ldap.forumsys.com   Port: 389
# Bind DN: cn=read-only-admin,dc=example,dc=com
# Bind Password: password

class LdapClient:
    RC_SUCCESS = 0
    RC_NO_SUCH_OBJECT = 32
    LOG = logging.getLogger(__name__)

    def __init__(self, *, url: str, user: str, password: str, authentication: str, read_only: bool, return_empty_attributes: bool):
        self._url = self._required_string(url, 'url')
        self._authentication = authentication or "SIMPLE"
        self._user = user
        self._password = password
        self._read_only = bool(read_only)
        self._return_empty_attributes = bool(return_empty_attributes)
        self._server = Server(self._url, get_info=ALL)
        self._conn = None

    @staticmethod
    def _required_string(value: str, name: str) -> str:
        if value is None: raise ValueError(f'{name!r} cannot be None')
        stripped = value.strip()
        if not stripped: raise ValueError(f'{name!r} cannot be empty or whitespace')
        return stripped

    @property
    def connection(self) -> Connection:
        return self._connect()

    def _connect(self) -> None:
        """Internal lazy connection method"""
        try:
            if self._conn is None:
                self._conn = Connection(
                    self._server,
                    authentication=self._authentication,
                    user=self._user,
                    password=self._password,
                    auto_bind=True,
                    read_only=self._read_only,
                    return_empty_attributes=self._return_empty_attributes
                )
            return self._conn
        except LDAPException as e:
            msg = f'Failed to connect to {self._url!r}'
            self.LOG.exception(msg, exc_info=True)
            raise RuntimeError(msg) from e

    def search(self, base_dn, search_filter="(objectClass=*)", attributes=ALL_ATTRIBUTES) -> dict:
        connection = self.connection
        try:
            connection.search(base_dn, search_filter, attributes=attributes)
            result_code = connection.result.get("result", -1)
            if result_code in [self.RC_SUCCESS, self.RC_NO_SUCH_OBJECT]:
                return {
                    "success": True,
                    "result_code": result_code,
                    "error": None,
                    "entries": [] if result_code == self.RC_NO_SUCH_OBJECT else connection.entries
                }
            return {
                "success": False,
                "result_code": result_code,
                "error": connection.result,
                "entries": []
            }
        except LDAPExceptionError as e:
            return {
                "success": False,
                "result_code": -1,
                "error": str(e),
                "entries": []
            }
        except LDAPException as e:
            msg = f'Connection problem with {self._url!r}'
            self.LOG.exception(msg, exc_info=True)
            self.disconnect()
            raise RuntimeError(msg) from e

    def disconnect(self):
        try:
            if self._conn:
                try:
                    self._conn.unbind()
                except Exception: # pylint: disable=broad-exception-caught
                    self.LOG.exception('Disconnect problem with %s', repr(self._url), exc_info=True)
        finally:
            self._conn = None

    def __enter__(self):
        return self._connect()

    def __exit__(self, _exc_type, _exc_value, _traceback):
        self.disconnect()

class LdapClientManager:

    def __init__(self):
        self._connections: Dict[str, LdapClient] = {}

    def connect(self, name: str, **kwargs) -> LdapClient:
        """Create and store an LdapClient under the given name."""
        name = self._normalize_name(name)
        # if we had one previously, close it
        self.disconnect(name)
        client = LdapClient(**kwargs)
        self._connections[name] = client
        return client

    def disconnect(self, name: Optional[str] = None) -> None:
        """Remove a named connection. No error if it does not exist."""
        name = self._normalize_name(name)
        if name in self._connections:
            self._connections.pop(name).disconnect()

    def get_connection(self, name: Optional[str] = None) -> LdapClient:
        """Return the LdapClient for the given name."""
        name = self._normalize_name(name)
        return self._connections[name] if name in self._connections else self.connect(name)

    def _normalize_name(self, name: Optional[str]) -> str:
        if not name or name.isspace() == '':
            raise ValueError('Missing name for LDAP connection')
        return name.strip()
