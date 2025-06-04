"""
Define the BASIC extension
"""

from typing import Dict, Callable
from pathlib import Path

from extn import VgrExtension
from .stmts import (
    execute_continue,
    execute_do_until,
    execute_do_while,
    execute_exit,
    execute_for_next,
    execute_let,
    execute_troff,
    execute_tron,
)

_HANDLERS = {
    'basic_continue':    execute_continue,
    'basic_do_until':    execute_do_until,
    'basic_do_while':    execute_do_while,
    'basic_for_next_by': execute_for_next,
    'basic_for_next':    execute_for_next,
    'basic_exit':        execute_exit,
    'basic_let':         execute_let,
    'basic_troff':       execute_troff,
    'basic_tron':        execute_tron,
}

class BasicExtension(VgrExtension):

    def adds_statements(self):
        return True

    def grammar(self) -> str:
        extn_grammar = Path(__file__).parent / 'basic.ebnf'
        with extn_grammar.open('r', encoding='utf-8') as f:
            return f.read()

    def statement_handlers(self) -> Dict[str, Callable]:
        return _HANDLERS
