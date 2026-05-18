"""
Defines the COBOL extension
"""

from typing import Dict, Callable

from ..extn import VgrExtension
from .cobol_stmts import (
    execute_accept,
    execute_add_giving,
    execute_add_to,
    execute_dec,
    execute_display_on,
    execute_div_by,
    execute_div_into,
    execute_evaluate,
    execute_exhibit,
    execute_exit_perform,
    execute_exit_program,
    execute_stop_run,
    execute_inc,
    execute_move_to,
    execute_mul_by,
    execute_perform_times,
    execute_perform_until,
    execute_perform_varying,
    execute_string,
    execute_sub_from,
    execute_sub_giving,
)

_HANDLERS = {
    'cobol_accept_date':        execute_accept,
    'cobol_accept_day':         execute_accept,
    'cobol_accept_dow':         execute_accept,
    'cobol_accept_input':       execute_accept,
    'cobol_accept_time':        execute_accept,
    'cobol_accept_yyyyddd':     execute_accept,
    'cobol_accept_yyyymmdd':    execute_accept,
    'cobol_add_giving':         execute_add_giving,
    'cobol_add_to':             execute_add_to,
    'cobol_dec':                execute_dec,
    'cobol_display_on':         execute_display_on,
    'cobol_div_by':             execute_div_by,
    'cobol_div_into':           execute_div_into,
    'cobol_evaluate':           execute_evaluate,
    'cobol_exhibit':            execute_exhibit,
    'cobol_exit_perform':       execute_exit_perform,
    'cobol_exit_perform_cycle': execute_exit_perform,
    'cobol_exit_program':       execute_exit_program,
    'cobol_inc':                execute_inc,
    'cobol_move_to':            execute_move_to,
    'cobol_mul_by':             execute_mul_by,
    'cobol_perform_times':      execute_perform_times,
    'cobol_perform_until':      execute_perform_until,
    'cobol_perform_varying':    execute_perform_varying,
    'cobol_stop_run':           execute_stop_run,
    'cobol_string':             execute_string,
    'cobol_sub_from':           execute_sub_from,
    'cobol_sub_giving':         execute_sub_giving,
}

class CobolExtension(VgrExtension):

    def adds_statements(self):
        return True

    def grammar(self) -> str:
        return self.read_resource_text(__package__, 'cobol.lark')

    def statement_handlers(self) -> Dict[str, Callable]:
        return _HANDLERS
