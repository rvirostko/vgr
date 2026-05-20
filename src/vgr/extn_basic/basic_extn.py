"""
Define the BASIC extension
"""

from typing import Dict, Callable

from ..extn import VgrExtension
from .basic_stmts import (
    execute_continue_for,
    execute_continue_while,
    execute_exit_for,
    execute_exit_while,
)

_HANDLERS = {
    'basic_continue_for':   execute_continue_for,
    'basic_continue_while': execute_continue_while,
    'basic_exit_for':       execute_exit_for,
    'basic_exit_while':     execute_exit_while,
}

class BasicExtension(VgrExtension):

    def adds_statements(self):
        return True

    def grammar(self) -> str:
        return self.read_resource_text(__package__, 'basic.lark')

    def statement_handlers(self) -> Dict[str, Callable]:
        return _HANDLERS
