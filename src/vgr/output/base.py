"""
Base classes for writing structured records
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from io import IOBase
from typing import Any
import sys

from ..builtins import (
    json_dumps,
    poly_to_string,
)
from ..builtins.vpattern import VPattern

class RecordWriter(ABC):

    @abstractmethod
    def start(self) -> None:
        """Called at the start of writing"""

    @abstractmethod
    def finish(self) -> None:
        """Called when writing is complete"""

    @abstractmethod
    def write(self, record: list[Any]) -> bool:
        """
        Write a single record to the output
        Returns True if writing can continue
        """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finish()

    def _attrs(self) -> list:
        """Return a list of attribute names to include in __repr__"""
        return []

    def __repr__(self):
        attr_repr = []
        for attr in self._attrs():
            if not hasattr(self, attr): raise ValueError(f'{attr}=<missing>') #pragma no cover
            attr_repr.append(f'{attr}={getattr(self, attr)!r}')
        return f'{self.__class__.__name__}({", ".join(attr_repr)})'

    def _setattrs(self, **kwargs) -> None:
        """
        Handles kwargs in subclass __init__s.
        Call only after all the attributes are set up.
        Unknown attrs are ignored.
        """
        defined_attrs = self._attrs()
        for key, value in kwargs.items():
            if key in defined_attrs and hasattr(self, key):
                setattr(self, key, value)

class DelegatingRecordWriter(RecordWriter):

    def __init__(self, delegate: RecordWriter):
        self._delegate = delegate
        super().__init__()

    def start(self) -> None:
        self._delegate.start()

    def finish(self):
        self._delegate.finish()

    def write(self, record: list[Any]) -> bool:
        return self._delegate.write(record)

    def _attrs(self) -> list:
        return super()._attrs() + ['_delegate']

class FileRecordWriter(RecordWriter):

    def __init__(self, file: IOBase=sys.stdout):
        self._file = file
        self._headers = []
        self._include_headers = True
        super().__init__()

    @property
    def headers(self) -> list:
        return list(self._headers)

    @headers.setter
    def headers(self, headers: list):
        self._headers = headers or []

    @property
    def include_headers(self) -> bool:
        return self._include_headers

    @include_headers.setter
    def include_headers(self, enable: bool):
        self._include_headers = bool(enable)

    def start(self) -> None:
        if self._headers and self._include_headers: self.write_headers()

    def finish(self):
        super().finish()
        self._file = None

    @abstractmethod
    def write_headers(self) -> bool:
        """
        Write out headers for the data.
        Abstact at base class as the concept of headers if format specific
        """

    def print(self, *args: any) -> None: # TODO
        """Utility method: does not add separator or line ending"""
        print(*args, sep='', end='', file=self._file)

    def println(self, *args: any) -> None: # TODO
        """Utility method: does not add separator"""
        print(*args, sep='', file=self._file)

    def flush(self) -> None:
        if self._file: self._file.flush()

    def _attrs(self) -> list:
        return super()._attrs() + ['headers', 'include_headers']

    @classmethod
    def stringify(cls, obj: Any) -> str:
        """
        Primitive "to_string()" operation.
        scalars are just sent to str(obj).
        dict are converted to a single line output.
        Collections are converted to a  comma separated list.
        """
        if obj is None: return ''
        # Compact JSON format for dictionaries
        if isinstance(obj, dict): return json_dumps(obj, separators=(",", ":"), allow_nan=False)
        # Recursively stringify to comma separated elements, but NO square brackets
        if isinstance(obj, list): return ", ".join(map(cls.stringify, obj))
        if isinstance(obj, VPattern): return repr(obj)
        return poly_to_string(obj)
