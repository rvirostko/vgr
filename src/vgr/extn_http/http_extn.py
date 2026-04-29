"""
Defines the Http extension
"""

from typing import Dict, Callable

from lark import Tree

from ..builtins import bound_ops
from ..data_dict import DataDictionary
from ..exec_context import ExecContext
from ..extn import VgrExtension

from .http_stmts import (
    http_initialize,
    execute_connect,
    execute_disconnect,
    execute_request,
)

@bound_ops("Http")
def _http_help(_ctx: ExecContext, _statement: Tree) -> None:
    """
**Execute HTTP operations with or without session management**

* Http Connect - Establish a reusable connection
* Http Disconnect - Close connections
* Http *method* - Execute arbitrary HTTP operations

Also see `Http Connect`, `Http Request`, and `Http Disconnect`
"""
    # pass

_HANDLERS = {
    'http_help'       : _http_help,
    'http_connect'    : execute_connect,
    'http_disconnect' : execute_disconnect,
    'http_request'    : execute_request,
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
