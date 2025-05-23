"""
Define the COBOL extension
"""

from typing import Dict, Callable
from pathlib import Path

from extn import VgrExtension
from .stmts import execute_add_giving, execute_add_to, execute_dec, execute_display_on, execute_div_by
from .stmts import execute_div_into, execute_exhibit, execute_inc, execute_move_to, execute_mul_by
from .stmts import execute_sub_from, execute_sub_giving, execute_perform_times, execute_perform_varying
from .stmts import execute_compute, execute_exit, execute_next_sentence, execute_if, execute_perform_until
from .stmts import execute_accept_date, execute_accept_day, execute_accept_dow, execute_accept_time
from .stmts import execute_accept_yyyyddd, execute_accept_yyyymmdd, execute_accept_epoch

_HANDLERS = {
    'cobol_accept_date':     execute_accept_date,
    'cobol_accept_yyyymmdd': execute_accept_yyyymmdd,
    'cobol_accept_day':      execute_accept_day,
    'cobol_accept_yyyyddd':  execute_accept_yyyyddd,
    'cobol_accept_dow':      execute_accept_dow,
    'cobol_accept_time':     execute_accept_time,
    'cobol_accept_epoch':    execute_accept_epoch,
    'cobol_add_giving':      execute_add_giving,
    'cobol_add_to':          execute_add_to,
    'cobol_compute':         execute_compute,
    'cobol_dec':             execute_dec,
    'cobol_display_on':      execute_display_on,
    'cobol_div_by':          execute_div_by,
    'cobol_div_into':        execute_div_into,
    'cobol_exhibit':         execute_exhibit,
    'cobol_exit':            execute_exit,
    'cobol_if':              execute_if,
    'cobol_inc':             execute_inc,
    'cobol_move_to':         execute_move_to,
    'cobol_mul_by':          execute_mul_by,
    'cobol_next_sentence':   execute_next_sentence,
    'cobol_perform_times':   execute_perform_times,
    'cobol_perform_until':   execute_perform_until,
    'cobol_perform_varying': execute_perform_varying,
    'cobol_sub_from':        execute_sub_from,
    'cobol_sub_giving':      execute_sub_giving,
}

class CobolExtension(VgrExtension):

    def adds_statements(self):
        return True

    def grammar(self) -> str:
        extn_grammar = Path(__file__).parent / 'cobol.ebnf'
        with extn_grammar.open('r', encoding='utf-8') as f:
            return f.read()

    def statement_handlers(self) -> Dict[str, Callable]:
        return _HANDLERS
