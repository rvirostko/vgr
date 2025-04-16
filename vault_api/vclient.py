"""
A client for talking to Vault
"""

from http import HTTPStatus
from typing import Any, Dict
from urllib.error import HTTPError
from urllib.parse import urlparse
import http.client
import json

_MIME_JSON: str = 'application/json'
_UTF_8: str = 'utf-8'

class VaultStatusException(http.client.HTTPException):
    def __init__(self, status, reason, url=None, response_body=None):
        super().__init__(f"{status} {reason}")
        self.status = status
        self.reason = reason
        self.url = url
        self.response_body = response_body

    def __str__(self):
        msg = f'{self.status} {self.reason}'
        if self.url:
            msg += f' {self.url}'
        if self.response_body:
            msg += f' - {self.response_body}'
        return msg

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
        namespace = self._ns(namespace)
        self._info(' ', method, ' ', self._addr, url, ' (X-Vault-Namespace=\'', namespace, '\')', sep='')
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
            response = self._conn.getresponse()
            text_response = response.read().decode(_UTF_8)
            if text_response:
                rc = json.loads(text_response)
            else:
                text_response = ''
                # Some operations return no text
                rc = {}
            retcode = response.status
            if not 200 <= retcode < 300:
                text_response = text_response.strip()
                # TODO look at old code to hunt down the first error if present
                if retcode == HTTPStatus.NOT_FOUND:
                    self._debug(retcode, 'on', self._addr + url, ':', text_response)
                else:
                    self._warn(retcode, 'on', self._addr + url, ':', text_response)
                    raise VaultStatusException(retcode, response.reason, url=self._addr + url, response_body=text_response)
            return rc
        except HTTPError as e:
            self._debug(e.code, 'on', self._addr + '/' + url)
            raise

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


    def create_namespace(self, new_namespace: str, namespace: str=None) -> Dict[str, Any]:
        return self.do_post(f'/v1/sys/namespaces/{new_namespace}', namespace)

    # TODO read_namespace
    # TODO update_namespace
    # TODO delete_namespace

    def list_namespace(self, namespace: str) -> Dict[str, Any]:
        return self.do_list('/v1/sys/namespaces', namespace)

    # TODO lock_namespace
    # TODO unlock_namespace

    def create_mount(self, mount_point: str, config: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        return self.do_post(f'/v1/sys/mounts/{mount_point}', config, namespace)
        # See https://github.com/hashicorp/terraform-provider-vault/issues/677#issuecomment-609116328

    def read_mount(self, mount_point: str, namespace: str=None) -> Dict[str, Any]:
        return self.do_get(f'/v1/sys/mounts/{mount_point}', namespace)

    # TODO update_mount
    # TODO delete_mount

    def list_mounts(self, namespace :str) ->  Dict[str, Any]:
        return self.do_get('/v1/sys/mounts', namespace)

    def load_kv2_secret(self, mount_point: str, path: str, data: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        return self.do_post(f'/v1/{mount_point}/data/{path}', data, namespace)

    def load_kv2_metadata(self, mount_point: str, path: str, meta_data: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        return self.do_post(f'/v1/{mount_point}/metadata/{path}', meta_data, namespace)

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _ns(self, ns: str) -> str:
        # Go thought the options: what the user provided on the call,
        # in the constructor, or default to "root"
        return ns if ns else self._default_ns if self._default_ns else ''

    @staticmethod
    def _warn(*args, **kwargs) -> None:
        print("WARN  ", *args, **kwargs) # TODO

    @staticmethod
    def _info(*args, **kwargs) -> None:
        print("INFO  ", *args, **kwargs) # TODO

    @staticmethod
    def _debug(*args, **kwargs) -> None:
        print("DEBUG ", *args, **kwargs) # TODO
