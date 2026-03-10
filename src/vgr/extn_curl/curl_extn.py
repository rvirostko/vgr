"""
Defines the Curl extension
"""

from typing import Dict, Callable

from ..extn import VgrExtension
from ..data_dict import DataDictionary

from .t import (
    curl_initialize,
    execute_connect,
    execute_disconnect,
    execute_request,
)

_HANDLERS = {
    'curl_connect'    : execute_connect,
    'curl_disconnect' : execute_disconnect,
    'curl_request'     : execute_request,
}

class CurlExtension(VgrExtension):
    def initialize(self, dd: DataDictionary) -> None:
        curl_initialize(dd)

    def adds_statements(self):
        return True

    def grammar(self) -> str:
        return self.read_resource_text(__package__, 'curl.lark')

    def statement_handlers(self) -> Dict[str, Callable]:
        return _HANDLERS
