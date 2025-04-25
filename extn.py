"""
Prototype for an extension system
"""

from typing import Dict, Callable
import configparser
import importlib
from pathlib import Path

from data_dict import DataDictionary

class VgrExtension:

    #pylint: disable=unused-argument
    def initialize(self, dd: DataDictionary) -> None:
        """
        Perform any kind of initialization action
        """
        return
    #pylint: enable=unused-argument

    def extends_select(self) -> bool:
        """
        Does the extension extend the select statement
        that, does it provide an extractor.
        """
        return False

    def adds_statements(self) -> bool:
        """
        Does the extension add statements to the grammar?
        """
        return False

    def grammar(self) -> str:
        """
        Return additional grammar provided by the extension
        """
        return ''

    #pylint: disable=unused-argument
    def statement_handlers(self) -> Dict[str, Callable]:
        """
        Return a dispatch table for statements provided by the extension
        """
        return {}
    #pylint: enable=unused-argument

    #pylint: disable=unused-argument
    def functions(self) -> Dict[str, Callable]:
        """
        Return functions added by the extension
        """
        return {}
    #pylint: enable=unused-argument

class VgrExtensionRegistry:
    """
    Reads extensions from ini files and creates and manages
    instances.
    """
    def __init__(self):
        self._registry = {}

    def load(self, dd: DataDictionary, extn_file: str) -> None:
        if extn_file is None or extn_file.isspace():
            return
        if not isinstance(extn_file, Path):
            extn_file = Path(extn_file)
        if not extn_file.exists():
            print(f'Warning: {repr(extn_file)} does not exist')
            return
        config = configparser.ConfigParser()
        config.read(extn_file)
        for section in config.sections():
            class_path = config[section].get('class')
            if not class_path:
                raise ValueError(f'Missing class in section [{section}]')
            module_name, _, class_name = class_path.rpartition('.')
            if not module_name or not class_name:
                raise ValueError(f'Invalid class path {repr(class_path)} in section [{section}]')
            try:
                module = importlib.import_module(module_name)
                cls = getattr(module, class_name)
                if not issubclass(cls, VgrExtension):
                    raise TypeError(f'{class_name} does not extend VgrExtension')
                extn: VgrExtension = cls()
                extn.initialize(dd)
                self._registry[section] = extn
            except (ImportError, AttributeError) as e:
                raise ImportError(f'Failed to load class {repr(class_path)} in section [{section}]') from e

    def get(self, name):
        return self._registry.get(name)

    def __iter__(self):
        return iter(self._registry.items())

    def __contains__(self, name):
        return name in self._registry

    def __getitem__(self, name):
        return self._registry[name]

VER = VgrExtensionRegistry()
