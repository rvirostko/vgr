"""
Automatic registration of built-in functions
"""

from pathlib import Path
from typing import Any, Callable
import importlib
import pkgutil

class BuiltinRegistry:
    _BUILTINS: dict[str, Callable[..., Any]] = {}
    @staticmethod
    def register(function_name: str, function: Callable[..., Any]) -> Callable[..., Any]:
        BuiltinRegistry._BUILTINS[function_name] = function
        return function
    @staticmethod
    def items():
        # TODO : when/why do we need this?
        # related to reference in _init_?
        # Load everything in our module to trigger
        # the decorators registering
#        if not BuiltinRegistry._BUILTINS is None:
#            parent_module = __name__.rpartition('.')[0]
#            for _, module_name, _ in pkgutil.iter_modules([str(Path(__file__).parent.absolute())]):
#                importlib.import_module(f"{parent_module}.{module_name}")
        return BuiltinRegistry._BUILTINS.items()

def builtin(function_name:str):
    def decorator(function: Callable[..., Any]):
        return BuiltinRegistry.register(function_name, function)
    return decorator
