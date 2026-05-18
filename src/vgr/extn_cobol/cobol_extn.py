"""
Defines the COBOL extension
"""

from typing import Dict, Callable

from ..extn import VgrExtension
from .cobol_stmts import (
    execute_accept,
    execute_display_on,
    execute_exhibit,
    execute_exit_perform,
    execute_move_to,
    execute_perform_times,
    execute_perform_until,
    execute_perform_varying,
    execute_string,
)

_HANDLERS = {
    'cobol_accept_date':        execute_accept,
    'cobol_accept_day':         execute_accept,
    'cobol_accept_dow':         execute_accept,
    'cobol_accept_input':       execute_accept,
    'cobol_accept_time':        execute_accept,
    'cobol_accept_yyyyddd':     execute_accept,
    'cobol_accept_yyyymmdd':    execute_accept,
    'cobol_display_on':         execute_display_on,
    'cobol_exhibit':            execute_exhibit,
    'cobol_exit_perform':       execute_exit_perform,
    'cobol_move_to':            execute_move_to,
    'cobol_perform_times':      execute_perform_times,
    'cobol_perform_until':      execute_perform_until,
    'cobol_perform_varying':    execute_perform_varying,
    'cobol_string':             execute_string,
}

class CobolExtension(VgrExtension):

    def adds_statements(self):
        return True

    def grammar(self) -> str:
        return self.read_resource_text(__package__, 'cobol.lark')

    def statement_handlers(self) -> Dict[str, Callable]:
        return _HANDLERS
