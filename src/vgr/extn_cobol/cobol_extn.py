"""
Defines the COBOL extension
"""

from typing import Dict, Callable

from ..extn import VgrExtension
from .cobol_stmts import (
    execute_exhibit,
    execute_move_to,
)

_HANDLERS = {
    'cobol_exhibit':            execute_exhibit,
    'cobol_move_to':            execute_move_to,
}

class CobolExtension(VgrExtension):

    def adds_statements(self):
        return True

    def grammar(self) -> str:
        return self.read_resource_text(__package__, 'cobol.lark')

    def statement_handlers(self) -> Dict[str, Callable]:
        return _HANDLERS
