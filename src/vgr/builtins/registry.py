"""
Automatic registration of built-in functions
"""

from pathlib import Path
from typing import Any, Callable
import importlib
import pkgutil

class BuiltinRegistry:
    _LOADED = False
    _BUILTINS: dict[str, Callable[..., Any]] = {}
    @staticmethod
    def register(function_name: str, function: Callable[..., Any]) -> None:
        BuiltinRegistry._BUILTINS[function_name] = function
    @staticmethod
    def items():
        # Load everything in our module to trigger the decorators registering
        if not BuiltinRegistry._LOADED:
            parent_module = __name__.rpartition('.')[0]
            for _, module_name, _ in pkgutil.iter_modules([str(Path(__file__).parent.absolute())]):
                importlib.import_module(f"{parent_module}.{module_name}")
            BuiltinRegistry._LOADED = True
        return BuiltinRegistry._BUILTINS.items()

def builtin(*args):
    def decorator(function: Callable[..., Any]):
        for function_name in args: BuiltinRegistry.register(function_name, function)
        return function
    return decorator
