"""
Defines the Term(inal) extension
"""

from typing import Dict, Callable
from pathlib import Path

from extn import VgrExtension
from data_dict import DataDictionary

from .stmts import (
    execute_term_statement,
    add_dd_constants
)

_FUNCTIONS = {
    #    Future
}

_HANDLERS = {
    'term_statement': execute_term_statement
}

_TERM_PREFIX = 'term'

class TermExtension(VgrExtension):
    def initialize(self, dd: DataDictionary) -> None:
        dd.add_immutable_prefix(_TERM_PREFIX)
        add_dd_constants(dd, _TERM_PREFIX)

    def adds_statements(self):
        return True

    def grammar(self) -> str:
        extn_grammar = Path(__file__).parent / 'term.ebnf'
        with extn_grammar.open('r', encoding='utf-8') as f:
            return f.read()

    def functions(self) -> Dict[str, Callable]:
        return _FUNCTIONS

    def statement_handlers(self) -> Dict[str, Callable]:
        return _HANDLERS
