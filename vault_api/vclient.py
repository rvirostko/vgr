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

from .util import encode_url

_MIME_JSON: str = 'application/json'
_MIME_JSON_PATCH: str = 'application/merge-patch+json'
_UTF_8: str = 'utf-8'

_M_GET = 'GET'
_M_LIST = 'LIST'
_M_DELETE = 'DELETE'
_M_POST = 'POST'
_M_PATCH = 'PATCH'

_CM_KEY = 'custom_metadata'
_CM_KEY_MAX_LEN = 128
_CM_VALUE_MAX_LEN = 150
_DATA_KEY = 'data'
_UNLOCK_KEY = 'unlock_key'

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

    def do_post(self, url: str, data: Dict[str, Any]=None, namespace: str=None) -> Dict[str, Any]:
        return self.make_request(url, _M_POST, data, namespace)

    def do_patch(self, url: str, data: Dict[str, Any]=None, namespace: str=None) -> Dict[str, Any]:
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
            if "errors" in rc:               status = rc["errors"]
            elif "warnings" in rc:           status = rc["warnings"]
            elif not (200 <= retcode < 300): status = retcode
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
        return self.do_post(encode_url('/v1/sys/namespaces/api-lock/lock'), namespace)

    def unlock_namespace(self, namespace: str, unlock_key: Any) -> Dict[str, Any]:
        return self.do_post(encode_url('/v1/sys/namespaces/api-lock/unlock'), _create_unlock(unlock_key), namespace)

    def create_mount(self, mount_point: str, data: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        mount_point = self._fix_mount_point(mount_point).removesuffix('/')
        return self.do_post(encode_url(f'/v1/sys/mounts/{mount_point}'), data, namespace)
        # See https://github.com/hashicorp/terraform-provider-vault/issues/677#issuecomment-609116328

    def read_mount(self, mount_point: str, namespace: str=None) -> Dict[str, Any]:
        mount_point = self._fix_mount_point(mount_point)
        return self.do_get(encode_url(f'/v1/sys/mounts/{mount_point}tune'), namespace)

    def update_mount(self, mount_point: str, config: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        mount_point = self._fix_mount_point(mount_point)
        return self.do_post(encode_url(f'/v1/sys/mounts/{mount_point}tune'), config, namespace)

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
                                "PUT", # That's what the docs say...
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
        mount_point = self._fix_mount_point(mount_point)
        return self.do_post(encode_url(f'/v1/{mount_point}library/{name}'), config, namespace)

    def read_ldap_library(self, mount_point: str, name: str, namespace: str=None) -> Dict[str, Any]:
        """
        Read an LDAP library definition.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_get(encode_url(f'/v1/{mount_point}library/{name}'), namespace)

    def update_ldap_library(self, mount_point: str, name: str, config: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        """
        Update an LDAP library (alias for create_ldap_library).
        """
        return self.create_ldap_library(mount_point, name, config, namespace)

    def delete_ldap_library(self, mount_point: str, name: str, namespace: str=None) -> Dict[str, Any]:
        """
        Delete an LDAP library.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_delete(encode_url(f'/v1/{mount_point}library/{name}'), namespace)

    def list_ldap_libraries(self, mount_point: str, namespace: str=None) -> Dict[str, Any]:
        """
        List LDAP libraries at the given mount point.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_list(encode_url(f'/v1/{mount_point}library'), namespace)

    def create_ldap_secret(self, mount_point: str, name: str, config: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        """
        Create or update an LDAP static role (secret).
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_post(encode_url(f'/v1/{mount_point}static-cred/{name}'), config, namespace)

    def read_ldap_secret(self, mount_point: str, name: str, namespace: str=None) -> Dict[str, Any]:
        """
        Read an LDAP static role (secret).
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_get(encode_url(f'/v1/{mount_point}static-cred/{name}'), namespace)

    def update_ldap_secret(self, mount_point: str, name: str, config: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        """
        Update an LDAP static role (secret) (alias for create_ldap_secret).
        """
        return self.create_ldap_secret(mount_point, name, config, namespace)

    def delete_ldap_secret(self, mount_point: str, name: str, namespace: str=None) -> Dict[str, Any]:
        """
        Delete an LDAP static role (secret).
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_delete(encode_url(f'/v1/{mount_point}static-cred/{name}'), namespace)

    def list_ldap_secrets(self, mount_point: str, namespace: str=None) -> Dict[str, Any]:
        """
        List LDAP static roles (secrets) at the given mount point.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_list(encode_url(f'/v1/{mount_point}static-cred'), namespace)

    def rotate_ldap_secret(self, mount_point: str, name: str, namespace: str=None) -> Dict[str, Any]:
        """
        Rotate credentials for an LDAP static role (secret).
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_post(encode_url(f'/v1/{mount_point}static-cred/{name}/rotate'), namespace=namespace)

    def read_database_config(self, mount_point: str, namespace: str=None) -> Dict[str, Any]:
        """
        Read the database secrets engine configuration for the given mount point.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_get(encode_url(f'/v1/{mount_point}config'), namespace)

    def update_database_config(self, mount_point: str, config: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        """
        Update the database secrets engine configuration for the given mount point.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_post(encode_url(f'/v1/{mount_point}config'), config, namespace)

    def delete_database_config(self, mount_point: str, namespace: str=None) -> Dict[str, Any]:
        """
        Delete the database secrets engine configuration for the given mount point.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_delete(encode_url(f'/v1/{mount_point}config'), namespace)

    def create_database_role(self, mount_point: str, role_name: str, config: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        """
        Create or update a database role.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_post(encode_url(f'/v1/{mount_point}roles/{role_name}'), config, namespace)

    def read_database_role(self, mount_point: str, role_name: str, namespace: str=None) -> Dict[str, Any]:
        """
        Read a database role definition.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_get(encode_url(f'/v1/{mount_point}roles/{role_name}'), namespace)

    def update_database_role(self, mount_point: str, role_name: str, config: Dict[str, Any], namespace: str=None) -> Dict[str, Any]:
        """
        Update a database role (alias for create_database_role).
        """
        return self.create_database_role(mount_point, role_name, config, namespace)

    def delete_database_role(self, mount_point: str, role_name: str, namespace: str=None) -> Dict[str, Any]:
        """
        Delete a database role.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_delete(encode_url(f'/v1/{mount_point}roles/{role_name}'), namespace)

    def list_database_roles(self, mount_point: str, namespace: str=None) -> Dict[str, Any]:
        """
        List database roles at the given mount point.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_list(encode_url(f'/v1/{mount_point}roles'), namespace)

    def generate_database_credentials(self, mount_point: str, role_name: str, namespace: str=None) -> Dict[str, Any]:
        """
        Generate credentials for the given database role.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_get(encode_url(f'/v1/{mount_point}creds/{role_name}'), namespace)

    def rotate_database_credentials(self, mount_point: str, role_name: str, namespace: str=None) -> Dict[str, Any]:
        """
        Rotate credentials for a static database role.
        """
        mount_point = self._fix_mount_point(mount_point)
        return self.do_post(encode_url(f'/v1/{mount_point}rotate-role/{role_name}'), namespace=namespace)

    def __enter__(self):
        return self.open()

    #pylint: disable=unused-argument
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    #pylint: enable=unused-argument

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
        # User has passed in something that might be round tripped...
        if _DATA_KEY in data:
            return data
        # We assume that the dictionary we got is the data itself
        return {_DATA_KEY: data}
    raise ValueError(f'Unexpected type {repr(type(data).__name__)} for data')

def _create_metadata(metadata: Any) -> Dict[str, Any]:
    """Create a custom_metadata dictionary that conforms to Vault's limits."""
    if not metadata:
        return {_CM_KEY: {}}
    if isinstance(metadata, dict):
        return {_CM_KEY: _validate_metadata(metadata.get(_CM_KEY, metadata))}
    raise ValueError(f'Unexpected type {repr(type(metadata).__name__)} for metadata')

def _validate_metadata(metadata: Dict[str, Any]) -> Dict[str, str]:
    """Validate and format metadata keys and values."""
    validated_metadata = {}
    for key, value in metadata.items():
        # Ensure the key is a string and no longer than MAX_KEY_LENGTH bytes
        key = str(key) if not isinstance(key, str) else key
        if len(key.encode('utf-8')) > _CM_KEY_MAX_LEN:
            raise ValueError(f"{_CM_KEY} key {repr(key)} exceeds {_CM_KEY_MAX_LEN} bytes")
        if value is not None:
            # Ensure the value is a string and no longer than MAX_VALUE_LENGTH bytes
            value = str(value) if not isinstance(value, str) else value
            if len(value.encode('utf-8')) > _CM_VALUE_MAX_LEN:
                raise ValueError(f"{_CM_KEY} value for {repr(key)} exceeds {_CM_VALUE_MAX_LEN} bytes")
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
    raise ValueError(f'Unexpected type {repr(type(data).__name__)}')
