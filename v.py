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
  
