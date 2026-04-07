"""
Prototype for an extension system
"""

from typing import Dict, Callable
import configparser
import importlib
import pathlib
import re
import zipfile
from importlib import resources

from .data_dict import DataDictionary

class VgrExtension:

    #pylint: disable=unused-argument
    def initialize(self, dd: DataDictionary) -> None:
        """
        Perform any kind of initialization action
        """
        return
    #pylint: enable=unused-argument

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

    @staticmethod
    def read_resource_text(package: str, resource_name: str) -> str:
        """Reads in the resource as a text file"""
        resource = resources.files(package).joinpath(resource_name)
        # This exists because under macOS Python 3.9
        # reading from a PYZ was failing to find the resources
        # Something on the file system
        if isinstance(resource, (pathlib.PosixPath, pathlib.PurePosixPath)):
            return resource.read_text('utf-8')
        if isinstance(resource, (pathlib.WindowsPath, pathlib.PureWindowsPath)):
            return resource.read_text('utf-8')
        # Something inside a zip-like file
        if isinstance(resource, zipfile.Path):
            path, internal_path = VgrExtension._split_archive_path(str(resource))
            with zipfile.ZipFile(path) as zf:
                return zf.read(internal_path).decode("utf-8")
        raise TypeError(f'Don\'t know how to read resource {str(resource)!r} of type {type(resource)!r}')

    @staticmethod
    def _split_archive_path(path: str):
        m = re.search(r'(.+\.(?:whl|pyz|zip))/+(.*)', path)
        if not m: return None, None
        return m.group(1).rstrip('/'), m.group(2)

class VgrExtensionRegistry:
    """
    Reads extensions from ini files and creates and manages
    instances.
    """
    def __init__(self):
        self._registry = {}

    def load(self, dd: DataDictionary, package: str, resource_name: str) -> None:
        config = configparser.ConfigParser()
        config.read_string(VgrExtension.read_resource_text(package, resource_name), resource_name)
        for section in config.sections():
            class_path = config[section].get('class')
            if not class_path:
                raise ValueError(f'Missing class in section [{section}]')
            module_name, _, class_name = class_path.rpartition('.')
            if not module_name or not class_name:
                raise ValueError(f'Invalid class path {class_path!r} in section [{section}]')
            try:
                module = importlib.import_module(module_name)
                cls = getattr(module, class_name)
                if not issubclass(cls, VgrExtension):
                    raise TypeError(f'{class_name} does not extend VgrExtension')
                extn: VgrExtension = cls()
                extn.initialize(dd)
                self._registry[section] = extn
            except (ImportError, AttributeError) as e:
                raise ImportError(f'Failed to load class {class_path!r} in section [{section}]') from e

    def get(self, name):
        return self._registry.get(name)

    def __iter__(self):
        return iter(self._registry.items())

    def __contains__(self, name):
        return name in self._registry

    def __getitem__(self, name):
        return self._registry[name]

VER = VgrExtensionRegistry()
