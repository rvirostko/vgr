# Transfer
__MIME_JSON: str = 'application/json'
__UTF_8: str = 'utf-8'

__VAULT_ADDR: str = ''
__VAULT_TOKEN: str = ''
VAULT_CONN: http.client.HTTPSConnection = None

def vault_get(url: str, namespace: str='') -> Dict[str, Any]:
    return vault_request(url, namespace, 'GET')

def vault_list(url: str, namespace: str='') -> Dict[str, Any]:
    return vault_request(url, namespace, 'LIST')

def vault_post(url: str, namespace: str='', data: Dict[str, Any]=None) -> Dict[str, Any]:
    return vault_request(url, namespace, 'POST', data)
  
def vault_request(url: str, namespace: str='', method: str='GET', data: Dict[str, Any]=None) -> Dict[str, Any]:
    """Call a Vault REST API and return the results"""
    if not url: raise Exception('Missing Vault operation URL')
    if not __VAULT_ADDR: raise Exception("Vault host address not defined")
    #url: str = f'{__VAULT_ADDR}{url}'
    LOG.info(f'{method} {__VAULT_ADDR}{url} (X-Vault-Namespace={namespace})')
    if not __VAULT_TOKEN: raise Exception("Vault token not defined")
    headers = {
        'X-Vault-Token': __VAULT_TOKEN,
        'X-Vault-Namespace': namespace,
        'Accept': f'{__MIME_JSON}; charset={__UTF_8}'
    }
    data_bytes = None
    if data is not None:
        headers['Content-Type'] = f'{__MIME_JSON}; charset={__UTF_8}'
        data_bytes = json.dumps(data).encode(__UTF_8)
    try:
        VAULT_CONN.request(url=url, method=method, headers=headers, body=data_bytes)
        text_response = VAULT_CONN.getresponse().read().decode(__UTF_8)
        if text_response:
            rc = json.loads(text_response)
        else:
            # Some operations return no text
            rc = {}
        return rc

    except HTTPError as e:
        LOG.dbg(f'{e.code} on {url}')
        # TODO - Should this only be true for LIST and/or GET?
        # 404s are passed directly to the caller as they are the way
        # Vault says a collection does not exist
        if e.code == HTTPStatus.NOT_FOUND: raise
        # See if Vault has a decent description of the problem besides just the HTTP error code
        err = json.loads(e.read().decode(__UTF_8))
        if not 'errors' in err: raise # Not present
        errors = err['errors']
        if not errors: raise # Empty
        raise Exception(f'{e.code} - {errors[0]}') from e

def normalize_path(path: str) -> str:
    """Strips, removes trailing slash and doubled slashes"""
    return re.sub(r'/+', '/', path.strip().strip('/'))

def encode_url(s: str) -> str:
    return urllib.parse.quote(s)
