"""
Defines the Http extension
"""

from typing import Dict, Callable

from ..extn import VgrExtension
from ..data_dict import DataDictionary

from .http_stmts import (
    http_initialize,
    execute_connect,
    execute_disconnect,
    execute_request,
)

_HANDLERS = {
    'http_connect'    : execute_connect,
    'http_disconnect' : execute_disconnect,
    'http_request'     : execute_request,
}

class HttpExtension(VgrExtension):
    def initialize(self, dd: DataDictionary) -> None:
        http_initialize(dd)

    def adds_statements(self):
        return True

    def grammar(self) -> str:
        return self.read_resource_text(__package__, 'http.lark')

    def statement_handlers(self) -> Dict[str, Callable]:
        return _HANDLERS
