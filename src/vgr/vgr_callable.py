from abc import ABC, abstractmethod
from typing import Any

class VgrCallable(ABC):

    @abstractmethod
    def evaluate(self, ctx, arg_values: list[Any]) -> Any:
        """Execute the operation with the given context and evaluated arguments"""
        raise NotImplementedError
