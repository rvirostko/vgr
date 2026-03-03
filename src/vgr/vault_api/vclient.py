"""
A client for talking to Vault
"""

from http import HTTPStatus
from typing import Any, Dict
from urllib.error import HTTPError
from urllib.parse import urlparse
import http.client
import json
import logging

from ..builtins import poly_type
from .util import encode_url

_MIME_JSON: str = 'application/json'
_MIME_JSON_PATCH: str = 'application/merge-patch+json'
_UTF_8: str = 'utf-8'

_M_GET = 'GET'
_M_LIST = 'LIST'
_M_DELETE = 'DELETE'
_M_POST = 'POST'
_M_PATCH = 'PATCH'
_M_HEAD = 'HEAD'
_M_OPTIONS = 'OPTIONS'

_CM_KEY = 'custom_metadata'
_CM_KEY_MAX_LEN = 128
_CM_VALUE_MAX_LEN = 150
_DATA_KEY = 'data'
_UNLOCK_KEY = 'unlock_key'

_HUNG_UP_EXCEPTIONS = (
    http.client.RemoteDisconnected,
    http.client.CannotSendRequest,
    http.client.ResponseNotReady,
    BrokenPipeError,
    ConnectionResetError,
)

_SAFE_METHODS = { _M_GET, _M_LIST, _M_HEAD, _M_OPTIONS }

_LOG = logging.getLogger(__name__)

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
        p = urlparse(addr)
        if not p.scheme: p = urlparse("https://" + addr)
        if p.scheme and not p.netloc:
            raise ValueError(f"Address {self._addr!r} has a scheme but no authority (expected //hostname)")
        self._scheme = p.scheme.lower()
        if self._scheme not in ("http", "https"):
            raise ValueError(f"Unsupported URL scheme {p.scheme!r} in address {self._addr!r}")
        if not p.hostname:
            raise ValueError(f"Address {self._addr!r} does not contain a valid hostname")
        self._hostname = p.hostname
        self._port = p.port or (443 if self._scheme == "https" else 80)
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
        return self.make_request(url, _M_GET, None, namespace)

    def do_list(self, url: str, namespace: str=None) -> Dict[str, Any]:
        return self.make_request(url, _M_LIST, None, namespace)

    def do_delete(self, url: str, namespace: str=None) -> Dict[str, Any]:
        return self.make_request(url, _M_DELETE, None, namespace)

    def do_post(self, url: str, data: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        return self.make_request(url, _M_POST, data, namespace)

    def do_patch(self, url: str, data: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        return self.make_request(url, _M_PATCH, data, namespace)

    def make_request(self, url: str, method: str, data: Dict[str, Any], namespace: str) -> Dict[str, Any]:
        """Call a Vault REST API and return the results"""
        if not url: raise ValueError('Missing Vault operation URL')
        self.open()
        namespace = self._ns(namespace)
        self._info(method, ' ', self._addr, url, ' (X-Vault-Namespace=\'', namespace, '\')')
        headers = {
            'X-Vault-Token': self._token,
            'X-Vault-Namespace': namespace,
            'Accept': f'{_MIME_JSON}; charset={_UTF_8}'
        }
        data_bytes = None
        if data is not None:
            mime_type = _MIME_JSON_PATCH if method == _M_PATCH else _MIME_JSON
            headers['Content-Type'] = f'{mime_type}; charset={_UTF_8}'
            data_bytes = json.dumps(data, default=str).encode(_UTF_8)
        try:
            self._request_with_reconnect(url=url, method=method, headers=headers, body=data_bytes)
            response = self._conn.getresponse()
            text_response = response.read().decode(_UTF_8)
            if text_response:
                rc = json.loads(text_response)
            else:
                text_response = ''
                # Some operations return no text
                rc = {}
            retcode = response.status
            # details for those interested
            rc["_vclient"] = {
                "url": url,
                "method": method,
                "status": retcode,
                "vault_index": response.getheader("X-Vault-Index"),
                "vault_cluster": response.getheader("X-Vault-Cluster"),
                "vault_lease_id": response.getheader("X-Vault-Lease-Id"),
            }
            # The top-level status field for a client doing a quick
            # check for problems by seeing if this is not None
            status = None
            if "errors" in rc:             status = rc["errors"]
            elif "warnings" in rc:         status = rc["warnings"]
            elif not 200 <= retcode < 300: status = retcode
            rc['status'] = status
            if not 200 <= retcode < 300:
                if retcode in (HTTPStatus.NOT_FOUND, HTTPStatus.BAD_REQUEST, HTTPStatus.FORBIDDEN):
                    self._warn(retcode, ' on ', self._addr + url, ' : ', status)
                else:
                    self._error(retcode, ' on ', self._addr + url, ' : ', status)
            return rc
        except HTTPError as e:
            self._error(e.code, ' on ', self._addr + url)
            raise

    def _request_with_reconnect(self, *, url, method, headers, body):
        try:
            self._conn.request(url=url, method=method, headers=headers, body=body)
        except _HUNG_UP_EXCEPTIONS as original_e:
            if method not in _SAFE_METHODS: raise original_e
            self._warn(f"Connection stale during {method} request to {url}: {original_e}; reconnecting")
            try:
                self.close()
            except Exception as close_e:
                self._warn("Close failed - ", repr(close_e))
            try:
                self.open()
                self._conn.request(url=url, method=method, headers=headers, body=body)
            except Exception as req_e:
                self._warn("Request retry failed - ", repr(req_e))
                raise req_e from original_e

    def open(self):
        if self._conn is None:
            self._info('Opening connection to', self._addr)
            if self._scheme == 'https':
                self._conn = http.client.HTTPSConnection(self._hostname,
                                                         self._port,
                                                         timeout=self.timeout,
                                                         blocksize=self.blocksize)
            else:
                self._conn = http.client.HTTPConnection(self._hostname,
                                                        self._port or 80,
                                                        timeout=self.timeout,
                                                        blocksize=self.blocksize)
        return self

    def close(self):
        if self._conn is not None:
            try:
                self._info('Closing connection to ', self._addr)
                self._conn.close()
            finally:
                self._conn = None

    def create_namespace(self, new_namespace: str, metadata: Dict[str, Any]=None, parent_namespace: str=None) -> Dict[str, Any]:
        return self.do_post(encode_url(f'/v1/sys/namespaces/{new_namespace}'), _create_metadata(metadata), parent_namespace)

    def read_namespace(self, namespace: str, parent_namespace: str=None) -> Dict[str, Any]:
        return self.do_get(encode_url(f'/v1/sys/namespaces/{namespace}'), parent_namespace)

    def update_namespace(self, namespace: str, metadata: Dict[str, Any]=None, parent_namespace: str=None) -> Dict[str, Any]:
        return self.do_patch(encode_url(f'/v1/sys/namespaces/{namespace}'), _create_metadata(metadata), parent_namespace)

    def delete_namespace(self, namespace: str, parent_namespace: str=None) -> Dict[str, Any]:
        return self.do_delete(f'/v1/sys/namespaces/{namespace}', parent_namespace)

    def list_namespace(self, namespace: str=None) -> Dict[str, Any]:
        return self.do_list('/v1/sys/namespaces', namespace)

    def lock_namespace(self, namespace: str) -> Dict[str, Any]:
        return self.do_post(encode_url('/v1/sys/namespaces/api-lock/lock'), None, namespace)

    def unlock_namespace(self, namespace: str, unlock_key: Any) -> Dict[str, Any]:
        return self.do_post(encode_url('/v1/sys/namespaces/api-lock/unlock'), _create_unlock(unlock_key), namespace)

    def create_mount(self, mount_point: str, data: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        mount_point = self._fix_mount_point(mount_point).removesuffix('/')
        return self.do_post(encode_url(f'/v1/sys/mounts/{mount_point}'), data, namespace)
        # See https://github.com/hashicorp/terraform-provider-vault/issues/677#issuecomment-609116328

    def read_mount(self, mount_point: str, namespace: str=None) -> Dict[str, Any]:
        mount_point = self._fix_mount_point(mount_point)
        return self.do_get(encode_url(f'/v1/sys/mounts/{mount_point}'), namespace)

    def update_mount(self, mount_point: str, config: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        mount_point = self._fix_mount_point(mount_point)
        return self.do_post(encode_url(f'/v1/sys/mounts/{mount_point}'), config, namespace)

    def delete_mount(self, mount_point: str, namespace: str=None) -> Dict[str, Any]:
        mount_point = self._fix_mount_point(mount_point)
        return self.do_delete(encode_url(f'/v1/sys/mounts/{mount_point}'), namespace)

    def list_mounts(self, namespace :str) ->  Dict[str, Any]:
        return self.do_get('/v1/sys/mounts', namespace)

    def _fix_kv_path(self, path: str) -> str:
        return path if path.startswith('/') else '/' + path

    def _fix_mount_point(self, mount_point: str) -> str:
        mount_point = mount_point[1:] if mount_point.startswith('/') else mount_point
        return mount_point if mount_point.endswith('/') else mount_point + '/'

    def read_kv2_config(self, mount_point: str, namespace: str=None) -> Dict[str, Any]:
        mount_point = self._fix_mount_point(mount_point)
        # https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2#read-kv-engine-configuration
        return self.do_get(encode_url(f'/v1/{mount_point}config'), namespace)

    def update_kv2_config(self, mount_point: str, config: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        mount_point = self._fix_mount_point(mount_point)
        # https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2#configure-the-kv-engine
        return self.do_post(encode_url(f'/v1/{mount_point}config'), config, namespace)

    def create_kv2_secret(self, mount_point: str, path: str, data: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        mount_point = self._fix_mount_point(mount_point)
        path = self._fix_kv_path(path)
        # https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2#create-update-secret
        return self.do_post(encode_url(f'/v1/{mount_point}data{path}'), _create_kv_data(data), namespace)

    def read_kv2_secret(self, mount_point: str, path: str, version: int=None, namespace: str=None) -> Dict[str, Any]:
        mount_point = self._fix_mount_point(mount_point)
        path = self._fix_kv_path(path)
        # https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2#read-secret-version
        return self.do_get(encode_url(f'/v1/{mount_point}data{path}') + (f'?version={version}' if version else ''), namespace)

    def update_kv2_secret(self, mount_point: str, path: str, data: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        return self.create_kv2_secret(mount_point, path, data, namespace)

    def patch_kv2_secret(self, mount_point: str, path: str, data: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        mount_point = self._fix_mount_point(mount_point)
        path = self._fix_kv_path(path)
        # https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2#patch-secret
        return self.do_patch(encode_url(f'/v1/{mount_point}data{path}'), _create_kv_data(data), namespace)

    def delete_kv2_secret(self, mount_point: str, path: str, data: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        """Soft delete of current or specified versions"""
        mount_point = self._fix_mount_point(mount_point)
        path = self._fix_kv_path(path)
        if data is None or not 'versions' in data:
            # Delete the latest version
            # https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2#delete-latest-version-of-secret
            return self.do_delete(encode_url(f'/v1/{mount_point}data{path}'), namespace)
        # Delete the specified versions
        # https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2#delete-secret-versions
        return self.do_post(encode_url(f'/v1/{mount_point}delete{path}'), {'versions': data['versions']}, namespace)

    def undelete_kv2_secret(self, mount_point: str, path: str, data: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        mount_point = self._fix_mount_point(mount_point)
        path = self._fix_kv_path(path)
        if data is None or not 'versions' in data:
            raise ValueError('versions required for undelete')
        # https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2#undelete-secret-versions
        return self.do_post(encode_url(f'/v1/{mount_point}undelete{path}'), {'versions': data['versions']}, namespace)

    def destroy_kv2_secret(self, mount_point: str, path: str, data: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        mount_point = self._fix_mount_point(mount_point)
        path = self._fix_kv_path(path)
        if data is None or not 'versions' in data:
            raise ValueError('versions required for destroy')
        # https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2#destroy-secret-versions
        return self.make_request(encode_url(f'/v1/{mount_point}destroy{path}'),
                                "PUT", # That's what the docs say
                                {'versions': data['versions']},
                                namespace)

    def list_kv2_secrets(self, mount_point: str, path: str, namespace: str=None) -> Dict[str, Any]:
        mount_point = self._fix_mount_point(mount_point)
        path = self._fix_kv_path(path)
        # https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2#list-secrets
        return self.do_list(encode_url(f'/v1/{mount_point}metadata{path}'), namespace)

    def create_kv2_metadata(self, mount_point: str, path: str, metadata: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        mount_point = self._fix_mount_point(mount_point)
        path = self._fix_kv_path(path)
        # https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2#create-update-metadata
        # NB: only supports the custom metadata part ATM, not other things like CAS et al
        return self.do_post(encode_url(f'/v1/{mount_point}metadata{path}'), _create_metadata(metadata), namespace)

    def read_kv2_metadata(self, mount_point: str, path: str, namespace: str=None) -> Dict[str, Any]:
        mount_point = self._fix_mount_point(mount_point)
        path = self._fix_kv_path(path)
        # https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2#read-secret-metadata
        return self.do_get(encode_url(f'/v1/{mount_point}metadata{path}'), namespace)

    def update_kv2_metadata(self, mount_point: str, path: str, metadata: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        return self.create_kv2_metadata(mount_point, path, metadata, namespace)

    def patch_kv2_metadata(self, mount_point: str, path: str, metadata: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        mount_point = self._fix_mount_point(mount_point)
        path = self._fix_kv_path(path)
        # https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2#patch-metadata
        # NB: only supports the custom metadata part ATM, not other things like CAS et al
        return self.do_patch(encode_url(f'/v1/{mount_point}metadata{path}'), _create_metadata(metadata), namespace)

    def delete_kv2_metadata(self, mount_point: str, path: str, namespace: str=None) -> Dict[str, Any]:
        mount_point = self._fix_mount_point(mount_point)
        # https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2#delete-metadata-and-all-versions
        return self.do_delete(encode_url(f'/v1/{mount_point}metadata{path}'), namespace)

    def get_kv2_subkeys(self, namespace: str, mount_point: str, path: str) -> list:
        mount_point = self._fix_mount_point(mount_point)
        path = self._fix_kv_path(path)
        # https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2#read-secret-subkeys
        return  self.do_get(encode_url(f'/v1/{mount_point}subkeys{path}') + '?depth=1', namespace)

    def read_aws_config(self, mount_point: str, namespace: str=None) -> Dict[str, Any]:
        """
        Read the AWS secrets engine configuration for the given mount point.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_get(encode_url(f'/v1/{mount_point}config'), namespace)

    def update_aws_config(self, mount_point: str, config: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        """
        Update the AWS secrets engine configuration for the given mount point.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_post(encode_url(f'/v1/{mount_point}config'), config, namespace)

    def delete_aws_config(self, mount_point: str, namespace: str=None) -> Dict[str, Any]:
        """
        Delete the AWS secrets engine configuration for the given mount point.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_delete(encode_url(f'/v1/{mount_point}config'), namespace)

    def create_aws_role(self, mount_point: str, role_name: str, config: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        """
        Create or update an AWS role at the given mount point.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_post(encode_url(f'/v1/{mount_point}roles/{role_name}'), config, namespace)

    def read_aws_role(self, mount_point: str, role_name: str, namespace: str=None) -> Dict[str, Any]:
        """
        Read an AWS role definition from the given mount point.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_get(encode_url(f'/v1/{mount_point}roles/{role_name}'), namespace)

    def update_aws_role(self, mount_point: str, role_name: str, config: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        """
        Update an AWS role definition (alias for create_aws_role).
        """
        return self.create_aws_role(mount_point, role_name, config, namespace)

    def delete_aws_role(self, mount_point: str, role_name: str, namespace: str=None) -> Dict[str, Any]:
        """
        Delete an AWS role from the given mount point.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_delete(encode_url(f'/v1/{mount_point}roles/{role_name}'), namespace)

    def list_aws_roles(self, mount_point: str, namespace: str=None) -> Dict[str, Any]:
        """
        List AWS roles at the given mount point.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_list(encode_url(f'/v1/{mount_point}roles'), namespace)

    def generate_aws_credentials(self, mount_point: str, role_name: str, namespace: str=None) -> Dict[str, Any]:
        """
        Generate AWS credentials for the given role at the mount point.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_get(encode_url(f'/v1/{mount_point}creds/{role_name}'), namespace)

    def read_ldap_config(self, mount_point: str, namespace: str=None) -> Dict[str, Any]:
        """
        Read the LDAP secrets engine configuration for the given mount point.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_get(encode_url(f'/v1/{mount_point}config'), namespace)

    def update_ldap_config(self, mount_point: str, config: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        """
        Update the LDAP secrets engine configuration for the given mount point.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_post(encode_url(f'/v1/{mount_point}config'), config, namespace)

    def delete_ldap_config(self, mount_point: str, namespace: str=None) -> Dict[str, Any]:
        """
        Delete the LDAP secrets engine configuration for the given mount point.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_delete(encode_url(f'/v1/{mount_point}config'), namespace)

    def create_ldap_library(self, mount_point: str, name: str, config: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        """
        Create or update an LDAP library.
        """
        # https://developer.hashicorp.com/vault/api-docs/secret/ldap
        mount_point = self._fix_mount_point(mount_point)
        return self.do_post(encode_url(f'/v1/{mount_point}library/{name}'), config, namespace)

    def read_ldap_library(self, mount_point: str, name: str, namespace: str=None) -> Dict[str, Any]:
        """
        Read an LDAP library definition.
        """
        # https://developer.hashicorp.com/vault/api-docs/secret/ldap
        mount_point = self._fix_mount_point(mount_point)
        return self.do_get(encode_url(f'/v1/{mount_point}library/{name}'), namespace)

    def update_ldap_library(self, mount_point: str, name: str, config: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        """
        Update an LDAP library (alias for create_ldap_library).
        """
        # https://developer.hashicorp.com/vault/api-docs/secret/ldap
        return self.create_ldap_library(mount_point, name, config, namespace)

    def delete_ldap_library(self, mount_point: str, name: str, namespace: str=None) -> Dict[str, Any]:
        """
        Delete an LDAP library.
        """
        # https://developer.hashicorp.com/vault/api-docs/secret/ldap
        mount_point = self._fix_mount_point(mount_point)
        return self.do_delete(encode_url(f'/v1/{mount_point}library/{name}'), namespace)

    def list_ldap_libraries(self, mount_point: str, namespace: str=None) -> Dict[str, Any]:
        """
        List LDAP libraries at the given mount point.
        """
        # https://developer.hashicorp.com/vault/api-docs/secret/ldap
        mount_point = self._fix_mount_point(mount_point)
        return self.do_list(encode_url(f'/v1/{mount_point}library'), namespace)

    def create_ldap_role(self, mount_point: str, name: str, config: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        """
        Create or update an LDAP static role.
        """
        # https://developer.hashicorp.com/vault/api-docs/secret/ldap
        mount_point = self._fix_mount_point(mount_point)
        return self.do_post(encode_url(f'/v1/{mount_point}static-cred/{name}'), config, namespace)

    def read_ldap_role(self, mount_point: str, name: str, namespace: str=None) -> Dict[str, Any]:
        """
        Read an LDAP static role.
        """
        # https://developer.hashicorp.com/vault/api-docs/secret/ldap
        mount_point = self._fix_mount_point(mount_point)
        return self.do_get(encode_url(f'/v1/{mount_point}static-cred/{name}'), namespace)

    def update_ldap_role(self, mount_point: str, name: str, config: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        """
        Update an LDAP static role (alias for create_ldap_role).
        """
        # https://developer.hashicorp.com/vault/api-docs/secret/ldap
        return self.create_ldap_role(mount_point, name, config, namespace)

    def delete_ldap_role(self, mount_point: str, name: str, namespace: str=None) -> Dict[str, Any]:
        """
        Delete an LDAP static role.
        """
        # https://developer.hashicorp.com/vault/api-docs/secret/ldap
        mount_point = self._fix_mount_point(mount_point)
        return self.do_delete(encode_url(f'/v1/{mount_point}static-cred/{name}'), namespace)

    def list_ldap_roles(self, mount_point: str, namespace: str=None) -> Dict[str, Any]:
        """
        List LDAP static roles at the given mount point.
        """
        # https://developer.hashicorp.com/vault/api-docs/secret/ldap
        mount_point = self._fix_mount_point(mount_point)
        return self.do_list(encode_url(f'/v1/{mount_point}static-cred'), namespace)

    def rotate_ldap_role(self, mount_point: str, name: str, namespace: str=None) -> Dict[str, Any]:
        """
        Rotate credentials for an LDAP static role.
        """
        # https://developer.hashicorp.com/vault/api-docs/secret/ldap
        mount_point = self._fix_mount_point(mount_point)
        return self.do_post(encode_url(f'/v1/{mount_point}static-cred/{name}/rotate'), None, namespace)

    def create_database_connection(self, mount_point: str, name: str, config: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        # https://developer.hashicorp.com/vault/api-docs/secret/databases#configure-connection
        mount_point = self._fix_mount_point(mount_point)
        return self.do_post(encode_url(f'/v1/{mount_point}config/{name}'), config, namespace)

    def read_database_connection(self, mount_point: str, name:str, namespace: str=None) -> Dict[str, Any]:
        # https://developer.hashicorp.com/vault/api-docs/secret/databases#read-connection
        mount_point = self._fix_mount_point(mount_point)
        return self.do_get(encode_url(f'/v1/{mount_point}config/{name}'), namespace)

    def update_database_connection(self, mount_point: str, name: str, config: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        # https://developer.hashicorp.com/vault/api-docs/secret/databases#configure-connection
        return self.create_database_connection(mount_point, name, config, namespace)

    def delete_database_connection(self, mount_point: str, name:str, namespace: str=None) -> Dict[str, Any]:
        # https://developer.hashicorp.com/vault/api-docs/secret/databases#delete-connection
        mount_point = self._fix_mount_point(mount_point)
        return self.do_delete(encode_url(f'/v1/{mount_point}config/{name}'), namespace)

    def list_database_connections(self, mount_point: str, namespace: str=None) -> Dict[str, Any]:
        # https://developer.hashicorp.com/vault/api-docs/secret/databases#list-connections
        mount_point = self._fix_mount_point(mount_point)
        return self.do_list(encode_url(f'/v1/{mount_point}config'), namespace)

    def reset_database_connection(self, mount_point: str, name: str, namespace: str=None) -> Dict[str, Any]:
        # https://developer.hashicorp.com/vault/api-docs/secret/databases#reset-connection
        mount_point = self._fix_mount_point(mount_point)
        return self.do_post(encode_url(f'/v1/{mount_point}reset/{name}'), None, namespace)

    def rotate_database_connection_creds(self, mount_point: str, name: str, namespace: str=None) -> Dict[str, Any]:
        # https://developer.hashicorp.com/vault/api-docs/secret/databases#rotate-root-credentials
        mount_point = self._fix_mount_point(mount_point)
        return self.do_post(encode_url(f'/v1/{mount_point}rotate-root/{name}'), None, namespace)

    def _static_pfx(self, path: str, is_static: bool) -> str:
        return "static-" + path if is_static else path

    def create_database_role(self, mount_point: str, role_name: str, is_static: bool, config: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        # https://developer.hashicorp.com/vault/api-docs/secret/databases#create-role
        mount_point = self._fix_mount_point(mount_point)
        return self.do_post(encode_url(f'/v1/{mount_point}{self._static_pfx("roles", is_static)}/{role_name}'), config, namespace)

    def read_database_role(self, mount_point: str, role_name: str, is_static: bool, namespace: str=None) -> Dict[str, Any]:
        # https://developer.hashicorp.com/vault/api-docs/secret/databases#read-role
        mount_point = self._fix_mount_point(mount_point)
        return self.do_get(encode_url(f'/v1/{mount_point}{self._static_pfx("roles", is_static)}/{role_name}'), namespace)

    def update_database_role(self, mount_point: str, role_name: str, is_static: bool, config: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        # https://developer.hashicorp.com/vault/api-docs/secret/databases#create-role
        return self.create_database_role(mount_point, role_name, is_static, config, namespace)

    def delete_database_role(self, mount_point: str, role_name: str, is_static: bool, namespace: str=None) -> Dict[str, Any]:
        # https://developer.hashicorp.com/vault/api-docs/secret/databases#delete-role
        mount_point = self._fix_mount_point(mount_point)
        return self.do_delete(encode_url(f'/v1/{mount_point}{self._static_pfx("roles", is_static)}/{role_name}'), namespace)

    def list_database_roles(self, mount_point: str, is_static: bool, namespace: str=None) -> Dict[str, Any]:
        # https://developer.hashicorp.com/vault/api-docs/secret/databases#delete-role
        mount_point = self._fix_mount_point(mount_point)
        return self.do_list(encode_url(f'/v1/{mount_point}{self._static_pfx("roles", is_static)}'), namespace)

    def generate_database_role_credentials(self, mount_point: str, role_name: str, is_static: bool, namespace: str=None) -> Dict[str, Any]:
        # https://developer.hashicorp.com/vault/api-docs/secret/databases#generate-credentials
        mount_point = self._fix_mount_point(mount_point)
        return self.do_get(encode_url(f'/v1/{mount_point}{self._static_pfx("creds", is_static)}/{role_name}'), namespace)

    def rotate_database_static_role_credentials(self, mount_point: str, role_name: str, namespace: str=None) -> Dict[str, Any]:
        # https://developer.hashicorp.com/vault/api-docs/secret/databases#rotate-static-role-credentials        mount_point = self._fix_mount_point(mount_point)
        return self.do_post(encode_url(f'/v1/{mount_point}rotate-role/{role_name}'), None, namespace)

    def __enter__(self):
        return self.open()

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        self.close()

    def _ns(self, ns: str) -> str:
        # Go thought the options: what the user provided on the call,
        # in the constructor, or default to "root"
        return ns if ns else self._default_ns if self._default_ns else ''

    @staticmethod
    def _error(*args) -> None:
        _LOG.error(''.join(str(arg) for arg in args))

    @staticmethod
    def _warn(*args) -> None:
        if _LOG.isEnabledFor(logging.WARNING):
            _LOG.warning(''.join(str(arg) for arg in args))

    @staticmethod
    def _info(*args) -> None:
        if _LOG.isEnabledFor(logging.INFO):
            _LOG.info(''.join(str(arg) for arg in args))

    @staticmethod
    def _debug(*args) -> None:
        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug(''.join(str(arg) for arg in args))

def _create_kv_data(data: Any) -> Dict[str, Any]:
    """Create a data dictionary for kv data."""
    if not data:
        return {_DATA_KEY: {}}
    if isinstance(data, dict):
        # User has passed in something that might be round tripped
        if _DATA_KEY in data:
            return data
        # We assume that the dictionary we got is the data itself
        return {_DATA_KEY: data}
    raise ValueError(f'Data must be a dictionary, found {poly_type(data)!r}')

def _create_metadata(metadata: Any) -> Dict[str, Any]:
    """Create a custom_metadata dictionary that conforms to Vault's limits."""
    if not metadata:
        return {_CM_KEY: {}}
    if isinstance(metadata, dict):
        return {_CM_KEY: _validate_metadata(metadata.get(_CM_KEY, metadata))}
    raise ValueError(f'Metadata must be a dictionary, found {poly_type(metadata)!r}')

def _validate_metadata(metadata: Dict[str, Any]) -> Dict[str, str]:
    """Validate and format metadata keys and values."""
    validated_metadata = {}
    for key, value in metadata.items():
        # Ensure the key is a string and no longer than MAX_KEY_LENGTH bytes
        key = str(key) if not isinstance(key, str) else key
        if len(key.encode('utf-8')) > _CM_KEY_MAX_LEN:
            raise ValueError(f'{_CM_KEY} key {key!r} exceeds {_CM_KEY_MAX_LEN} bytes')
        if value is not None:
            # Ensure the value is a string and no longer than MAX_VALUE_LENGTH bytes
            value = str(value) if not isinstance(value, str) else value
            if len(value.encode('utf-8')) > _CM_VALUE_MAX_LEN:
                raise ValueError(f'{_CM_KEY} value for {key!r} exceeds {_CM_VALUE_MAX_LEN} bytes')
            # Vault can't store empty entries, so skip them
            if value: validated_metadata[key] = value
    return validated_metadata

def _create_unlock(data: Any) -> Dict[str, Any]:
    if data is None:
        return {}
    if isinstance(data, str):
        return {_UNLOCK_KEY: data}
    if isinstance(data, dict):
        if _UNLOCK_KEY in data:
            return {_UNLOCK_KEY: data[_UNLOCK_KEY]}
        return {}
    raise ValueError(f'Key must be a string or dictionary, found {poly_type(data)!r}')
