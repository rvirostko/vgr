"""
Execution context
"""

from abc import ABC, abstractmethod
from typing import Any, Iterable

from lark import Lark, Tree

from .data_dict import DataDictionary

class ExecContext(ABC):

    def __init__(self, parser: Lark, dd: DataDictionary):
        super().__init__()
        assert parser is not None
        self._parser = parser
        assert dd is not None
        self._dd = dd
        self._debug = False
        self._echo = False
        self._verbose = False

    @property
    def parser(self) -> DataDictionary:
        return self._parser

    @property
    def dd(self) -> DataDictionary:
        return self._dd

    @abstractmethod
    def parse_expression(self, expr_text: str) -> Tree: pass

    @abstractmethod
    def execute_statements(self, statement_text: str, origin: str, start: str=None) -> None: pass

    @abstractmethod
    def dispatch_statements(self, statements: Iterable[Tree]) -> None: pass

    @abstractmethod
    def get_var(self, *path: str) -> Any: pass

    @abstractmethod
    def set_var(self, data: Any, /, *path: str) -> Any: pass

    @abstractmethod
    def var_exists(self, *path: str) -> tuple[bool, str, Any]: pass

    @abstractmethod
    def set_var_user(self, data: Any, /, *path: str) -> Any:
        """Deprecated: should make sure path is checked before calling set_var()"""

    @abstractmethod
    def eval_expr(self, expr: Any) -> Any: pass

    @abstractmethod
    def eval_expr_or_const(self, expr: Any) -> Any: pass

    @abstractmethod
    def eval_to_str(self, expr: Tree, name: str, allow_none: bool=False) -> str: pass

    @abstractmethod
    def eval_filename_expr(self, expr: Any, allow_none: bool=False) -> str: pass

    @abstractmethod
    def eval_to_int(self, expr: Tree, name: str, allow_none: bool=False) -> int: pass

    @abstractmethod
    def eval_to_number(self, expr: Tree, name: str, allow_none: bool=False): pass

    @abstractmethod
    def get_source(self, tree, end_tree = None) -> str: pass

    @property
    def echo(self) -> None: return self._echo

    @echo.setter
    def echo(self, v: bool) -> None: self._echo = bool(v)

    @abstractmethod
    def echo_source(self, tree: Tree, end_tree: Tree=None) -> None: pass

    @property
    def debug(self) -> None:
        """Has the user requested debugging output"""
        return self._debug

    @debug.setter
    def debug(self, v: bool) -> None:
        """Turn debug mode on or off"""
        self._debug = bool(v)

    @abstractmethod
    def print_debug(self, *args, **kwargs) -> None:
        """
        Although this checks for debug, check debug before calling
        if the arguments are not simple constants
        """

    @property
    def verbose(self) -> None:
        """Has the user requested detailed output"""
        return self._verbose

    @verbose.setter
    def verbose(self, v: bool) -> None:
        """Turn verbose mode on or off"""
        self._verbose = bool(v)

    @abstractmethod
    def print_verbose(self, *args, **kwargs) -> None:
        """
        Although this checks for verbose, check verbose before calling
        if the arguments are not simple constants
        """

    @abstractmethod
    def print_tree(self, item: Any) -> None: pass
