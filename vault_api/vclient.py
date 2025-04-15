"""
A client for talking to Vault
"""

from http import HTTPStatus
from typing import Any, Dict
from urllib.error import HTTPError
from urllib.parse import urlparse
import http.client
import json
import re
import urllib

_MIME_JSON: str = 'application/json'
_UTF_8: str = 'utf-8'

#self._conn: http.client.HTTPSConnection = None

class VaultClient():

    def __init__(self, addr: str, token: str, default_ns: str=None):
        if not addr: raise ValueError("Vault host address not provided")
        if not token: raise ValueError("Vault token not provided")
        self._token = token
        self._addr = addr
        self._conn = None # See open()/close()
        self._default_ns = default_ns
        self._timeout = 30.0 # in seconds
        self._blocksize = 8192

    @property
    def timeout(self) -> float:
        return self._timeout

    @timeout.setter
    def timeout(self, value) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("timeout must be a number")
        if value < 0:
            raise ValueError("timeout must be non-negative")
        self._timeout = float(value)

    @property
    def blocksize(self) -> int:
        return self._blocksize

    @blocksize.setter
    def blocksize(self, value) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("blocksize must be a number")
        if value <= 0:
            raise ValueError("blocksize must be positive")
        self._blocksize = int(value)

    def do_get(self, url: str, namespace: str=None) -> Dict[str, Any]:
        return self.make_request(url, 'GET', None, namespace)

    def do_list(self, url: str, namespace: str=None) -> Dict[str, Any]:
        return self.make_request(url, 'LIST', None, namespace)

    def do_post(self, url: str, data: Dict[str, Any]=None, namespace: str=None) -> Dict[str, Any]:
        return self.make_request(url, 'POST', data, namespace)

    def make_request(self, url: str, method: str, data: Dict[str, Any], namespace: str) -> Dict[str, Any]:
        """Call a Vault REST API and return the results"""
        if not url: raise ValueError('Missing Vault operation URL')
        self.open()
        self._info(method, self._addr, url, '(X-Vault-Namespace=', namespace, ')')
        headers = {
            'X-Vault-Token': self._token,
            'X-Vault-Namespace': namespace,
            'Accept': f'{_MIME_JSON}; charset={_UTF_8}'
        }
        data_bytes = None
        if data is not None:
            headers['Content-Type'] = f'{_MIME_JSON}; charset={_UTF_8}'
            data_bytes = json.dumps(data).encode(_UTF_8)
        try:
            self._conn.request(url=url, method=method, headers=headers, body=data_bytes)
            text_response = self._conn.getresponse().read().decode(_UTF_8)
            if text_response:
                rc = json.loads(text_response)
            else:
                # Some operations return no text
                rc = {}
            return rc
        except HTTPError as e:
            self._debug(e.code, 'on', url)
            # TODO - Should this only be true for LIST and/or GET?
            # 404s are passed directly to the caller as they are the way
            # Vault says a collection does not exist
            if e.code == HTTPStatus.NOT_FOUND: raise
            # See if Vault has a decent description of the problem besides just the HTTP error code
            err = json.loads(e.read().decode(_UTF_8))
            if not 'errors' in err: raise # Errors not present
            errors = err['errors']
            if not errors: raise # Empty errors
            raise HTTPError(url=url, code=e.code, msg=f'{e.code} - {errors[0]}', hdrs=e.headers, fp=e.fp) from e

    def open(self):
        if self._conn is None:
            self._info('Opening connection to', self._addr)
            p = urlparse(self._addr)
            if p.scheme.lower() == 'https':
                self._conn = http.client.HTTPSConnection(p.hostname,
                                                         p.port or 443,
                                                         timeout=self.timeout,
                                                         blocksize=self.blocksize)
            else:
                self._conn = http.client.HTTPConnection(p.hostname,
                                                        p.port or 80,
                                                        timeout=self.timeout,
                                                        blocksize=self.blocksize)
        return self

    def close(self):
        if self._conn is not None:
            try:
                self._info('Closing connection to', self._addr)
                self._conn.close()
            finally:
                self._conn = None

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @staticmethod
    def _info(*args) -> None:
        pass

    @staticmethod
    def _debug(*args) -> None:
        pass

# Utility methods

def normalize_path(path: str) -> str:
    """Strips, removes trailing slash and doubled slashes"""
    return re.sub(r'/+', '/', path.strip().strip('/'))

def encode_url(s: str) -> str:
    return urllib.parse.quote(s)
