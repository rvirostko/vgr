"""
Defines the Term(inal) extension
"""

from typing import Dict, Callable

from ..extn import VgrExtension
from ..data_dict import DataDictionary

from .term_stmts import (
    add_dd_constants,
    execute_term_statement,
    init_data,
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
        init_data()
        dd.add_immutable_prefix(_TERM_PREFIX)
        add_dd_constants(dd, _TERM_PREFIX)


    def adds_statements(self):
        return True

    def grammar(self) -> str:
        return self.read_resource_text(__package__, 'term.lark')

    def functions(self) -> Dict[str, Callable]:
        return _FUNCTIONS

    def statement_handlers(self) -> Dict[str, Callable]:
        return _HANDLERS
