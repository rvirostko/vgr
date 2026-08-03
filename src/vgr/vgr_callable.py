from abc import ABC, abstractmethod
from typing import Any

class VgrCallable(ABC):

    def __init__(self, name: str, source_file: str, source_line: int, source_column: int):
        self._name = name
        self._source_file = source_file
        self._source_line = source_line
        self._source_column = source_column

    @abstractmethod
    def evaluate(self, ctx, arg_values: list[Any]) -> Any:
        """Execute the operation with the given context and evaluated arguments"""
        raise NotImplementedError

    @property
    def name(self) -> str: return self._name

    @property
    def source_file(self) -> str: return self._source_file

    @property
    def source_line(self) -> int: return self._source_line

    @property
    def source_column(self) -> int: return self._source_column
