"""
Execution context
"""

from abc import ABC, abstractmethod
from typing import Any, Iterable

from lark import Lark, Tree

from data_dict import DataDictionary

class ExecContext(ABC):
    def __init__(self, parser: Lark, dd: DataDictionary):
        super().__init__()
        assert parser is not None
        self._parser = parser
        assert dd is not None
        self._dd = dd

    @property
    def parser(self) -> DataDictionary:
        return self._parser

    @property
    def dd(self) -> DataDictionary:
        return self._dd

    @abstractmethod
    def parse_expression(self, expr_text: str) -> Tree: pass

    @abstractmethod
    def execute_statements(self, statement_text: str, origin: str) -> None: pass

    @abstractmethod
    def dispatch_statements(self, statements: Iterable[Tree]) -> None: pass

    @abstractmethod
    def get_var(self, *path: str) -> Any: pass

    @abstractmethod
    def set_var(self, data: Any, /, *path: str) -> Any: pass

    @abstractmethod
    def get_var_user(self, *path: str) -> Any: pass

    @abstractmethod
    def set_var_user(self, data: Any, /, *path: str) -> Any: pass

    @abstractmethod
    def eval_expr(self, expr: Any) -> Any: pass

    @abstractmethod
    def eval_expr_or_const(self, expr: Any) -> Any: pass

    @abstractmethod
    def eval_to_str(self, expr: Tree, name: str, allow_none: bool=False) -> str: pass

    @abstractmethod
    def eval_filename_expr(self, expr: Any, allow_none: bool=False) -> str: pass

    @abstractmethod
    def echo_source(self, tree: Tree, end_tree: Tree=None) -> str: pass

    @abstractmethod
    def print_verbose(self, *args, **kwargs) -> None: pass
