"""
Define the BASIC extension
"""

from typing import Dict, Callable

from ..extn import VgrExtension
from .basic_stmts import (
    execute_continue_do,
    execute_continue_for,
    execute_continue_while,
    execute_do_until,
    execute_do_while,
    execute_exit_do,
    execute_exit_for,
    execute_exit_while,
    execute_for_next,
    execute_troff,
    execute_tron,
)

_HANDLERS = {
    'basic_continue_do':    execute_continue_do,
    'basic_continue_for':   execute_continue_for,
    'basic_continue_while': execute_continue_while,
    'basic_do_until':       execute_do_until,
    'basic_do_while':       execute_do_while,
    'basic_for_next_by':    execute_for_next,
    'basic_for_next':       execute_for_next,
    'basic_exit_do':        execute_exit_do,
    'basic_exit_for':       execute_exit_for,
    'basic_exit_while':     execute_exit_while,
    'basic_troff':          execute_troff,
    'basic_tron':           execute_tron,
}

class BasicExtension(VgrExtension):

    def adds_statements(self):
        return True

    def grammar(self) -> str:
        return self.read_resource_text(__package__, 'basic.lark')

    def statement_handlers(self) -> Dict[str, Callable]:
        return _HANDLERS
