"""
Utility methods
"""

import re
import urllib

def vault_normalize_path(path: str) -> str:
    """Strips, removes trailing slash and doubled slashes"""
    return re.sub(r'/+', '/', path.strip().strip('/'))

def encode_url(s: str) -> str:
    return urllib.parse.quote(s)
