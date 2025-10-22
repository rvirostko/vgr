"""
Wrappers around ldap3 for managing
LDAP clients and executing operations
"""

from typing import Optional, Dict
from urllib.parse import urlparse
import logging

from ldap3 import (
    ALL_ATTRIBUTES,
    ALL,
    Connection,
    DEREF_NEVER,
    LEVEL,
    Server,
    SIMPLE,
)
from ldap3.core.exceptions import (
    LDAPException,
    LDAPExceptionError,
)

from ..mathpak import poly_clamp

# Testing
# See: https://www.forumsys.com/2022/05/10/online-ldap-test-server/
# LDAP Server Information (read-only access):
# Server: ldap.forumsys.com   Port: 389
# Bind DN: cn=read-only-admin,dc=example,dc=com
# Bind Password: password
# ou=mathematicians,dc=example,dc=com
# ou=scientists,dc=example,dc=com

class LdapClient:
    RC_SUCCESS = 0
    RC_NO_SUCH_OBJECT = 32
    LOG = logging.getLogger(__name__)

    def __init__(self, *,
                 url: str,
                 user: str=None,
                 password: str=None,
                 authentication: str=SIMPLE,
                 read_only: bool=True,
                 return_empty_attributes: bool=True,
                 time_limit: int=30,
                 paged_size: int=500):
        self._url = validate_ldap_url(self._required_string(url, 'url'), 'URL')
        self._authentication = authentication
        self._user = user
        self._password = password
        self._read_only = bool(read_only)
        self._return_empty_attributes = bool(return_empty_attributes)
        self._time_limit = poly_clamp(time_limit, 0, 3_600) # unlimited and 1 hour
        self._paged_size = poly_clamp(paged_size, 0, 1_000)
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

    def search(self,
               search_base: str=None,
               search_filter="(objectClass=*)",
               search_scope: str=LEVEL,
               attributes=ALL_ATTRIBUTES,
               dereference_aliases=DEREF_NEVER,
               get_operational_attributes=False,
               time_limit: int=0,
               size_limit: int=0) -> dict:
        """Return a dictionary that describes the result of the operation"""
        connection = self.connection
        try:
            search_results = connection.extend.standard.paged_search(
                self._required_string(search_base, "search base"),
                search_filter,
                search_scope=               search_scope,
                attributes=                 attributes,
                dereference_aliases=        dereference_aliases,
                get_operational_attributes= get_operational_attributes,
                size_limit=                 size_limit or 0,
                time_limit=                 time_limit or self._time_limit,
                types_only=                 False,
                controls=                   None,
                paged_size=                 self._paged_size,
                paged_criticality=          True,
                generator=                  True)
            result_code = connection.result.get("result", -1)
            entries = []
            for result in search_results:
                if result.get('type') == 'searchResEntry':
                    attrs = normalize_ldap_entry(result.get('attributes', {}))
                    if 'dn' not in attrs and 'distinguishedName' not in attrs:
                        attrs['dn'] = result.get('dn')
                    entries.append(attrs)
            if result_code in [self.RC_SUCCESS, self.RC_NO_SUCH_OBJECT]:
                return {
                    "success": True,
                    "result_code": result_code,
                    "error": None,
                    "entries": limit_results(size_limit, [] if result_code == self.RC_NO_SUCH_OBJECT else entries)
                }
            return {
                "success": False,
                "result_code": result_code,
                "error": connection.result,
                "entries": limit_results(size_limit, [])
            }
        except LDAPExceptionError as e:
            return {
                "success": False,
                "result_code": -1,
                "error": str(e),
                "entries": limit_results(size_limit, [])
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
        if name not in self._connections:
            raise ValueError(f'LDAP connection {name!r} does not exist')
        return self._connections[name]

    def _normalize_name(self, name: Optional[str]) -> str:
        if not name or name.isspace() == '':
            raise ValueError('Missing name for LDAP connection')
        return name.strip()

def validate_ldap_url(url: str, name: str) -> str:
    """
    Validate an LDAP/LDAPS URL.
    Must have:
      - scheme: ldap or ldaps
      - hostname: present
    May have:
      - port
    Must NOT have:
      - username/password (embedded credentials)
      - path, query, or fragment
    Returns the normalized URL string if valid.
    Raises ValueError with specific complaint if invalid.
    """
    if not isinstance(url, str) or not url.strip(): raise ValueError(f'{name} must be a non-empty string')
    parsed = urlparse(url.strip())
    if parsed.scheme not in ('ldap', 'ldaps'): raise ValueError(f'{name} scheme must be ldap or ldaps')
    if not parsed.hostname: raise ValueError(f'{name} missing hostname')
    if parsed.username or parsed.password: raise ValueError(f'{name} embedded credentials not allowed')
    if parsed.path not in ('', '/'): raise ValueError(f'{name} path not allowed')
    if parsed.query: raise ValueError(f'{name} query parameters not allowed')
    if parsed.fragment: raise ValueError(f'{name} fragment not allowed')
    port = f":{parsed.port}" if parsed.port else ''
    return f"{parsed.scheme}://{parsed.hostname}{port}"

_MULTI_VALUED_ATTRS = {
    'mailAlternateAddress',
    'member',
    'memberOf',
    'objectClass',
    'otherMailbox',
    'otherTelephone',
    'proxyAddresses',
    'servicePrincipalName',
    'telephoneNumber',
    'uniqueMember',
}

def normalize_ldap_entry(entry):
    """
    Convert LDAP3 entry or dict-like result into a plain Python dict,
    with all bytes decoded and CaseInsensitiveDict flattened.
    """
    # If this is an ldap3 Entry object, use its entry_attributes_as_dict()
    if hasattr(entry, 'entry_attributes_as_dict'):
        entry = entry.entry_attributes_as_dict()
    if isinstance(entry, dict):
        normalized = {}
        for key, value in entry.items():
            # Convert keys to plain strings
            if not isinstance(key, str): key = str(key)
            # Convert values
            if isinstance(value, bytes):
                value = value.decode('utf-8', errors='replace')
            elif isinstance(value, (list, tuple)):
                # Decode bytes elements in lists
                value = [
                    v.decode('utf-8', errors='replace') if isinstance(v, bytes) else v
                    for v in value
                ]
            elif isinstance(value, dict):
                # Recurse for nested dicts (rare, but possible)
                value = normalize_ldap_entry(value)
            if key in _MULTI_VALUED_ATTRS:
                value = value if isinstance(value, list) else [value]
            else:
                if value == []:
                   value = None
                else:
                    # Collapse single-value lists
                    if isinstance(value, list) and len(value) == 1:
                        value = value[0]
            normalized[key] = value
        return normalized
    elif hasattr(entry, 'items'):
        return normalize_ldap_entry(dict(entry))
    return entry

def limit_results(size_limit: int, items: list):
    if size_limit == 1:
        if not items: return None
        if len(items) == 1: return items[0]
    return items
