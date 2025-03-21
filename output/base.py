#! /usr/bin/env python3

from abc import ABC, abstractmethod
from collections.abc import Iterable
from io import FileIO, TextIOWrapper
from typing import Any
import json
import sys

class RecordWriter(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def start(self) -> bool:
        """Returns True if writing can continue"""

    @abstractmethod
    def finish(self):
        """Called when writing is complete"""

    @abstractmethod
    def write(self, record: list[Any]) -> bool:
        """
        Write a single record to the output
        Returns True if writing can continue
        """

    @abstractmethod
    def close(self):
        """Called to close/release resources"""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _attrs(self) -> list:
        """Return a list of attribute names to include in __repr__"""
        return []

    def __repr__(self):
        attr_repr = []
        for attr in self._attrs():
            if hasattr(self, attr):
                attr_repr.append(f'{attr}={repr(getattr(self, attr))}')
            else:
                attr_repr.append(f'{attr}=<missing>')
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
            else:
                print(key)


class DelegatingRecordWriter(RecordWriter):

    def __init__(self, delegate: RecordWriter):
        self._delegate = delegate

    def start(self) -> bool:
        return self._delegate.start()

    def finish(self):
        self._delegate.finish()

    def write(self, record: list[Any]) -> bool:
        return self._delegate.write(record)

    def close(self):
        self._delegate.close()

    def _attrs(self) -> list:
        return super()._attrs() + ['_delegate']

class FileRecordWriter(RecordWriter):

    def __init__(self, file: FileIO=sys.stdout.buffer):
        super().__init__()
        self._file = file
        self._output: TextIOWrapper = None
        self._encode_ascii = False
        self._headers = []
        self._omit_headers = False

    @property
    def headers(self) -> list:
        return list(self._headers)

    @headers.setter
    def headers(self, headers: list):
        self._headers = headers or []

    @property
    def omit_headers(self) -> bool:
        return self._omit_headers

    @omit_headers.setter
    def omit_headers(self, enable: bool):
        self._omit_headers = bool(enable)

    @property
    def encode_ascii(self) -> bool:
        return self._encode_ascii

    @encode_ascii.setter
    def encode_ascii(self, enable: bool):
        self._encode_ascii = bool(enable)

    @property
    def encode_utf8(self) -> bool:
        return not self._encode_ascii

    @encode_utf8.setter
    def encode_utf8(self, enable: bool):
        self._encode_ascii = not bool(enable)

    @property
    def encoding(self) -> str:
        return 'ascii' if self._encode_ascii else 'utf-8'

    @encoding.setter
    def encoding(self, encoding: str):
        """ascii for ascii; anything else for utf-8"""
        self.encode_ascii = encoding and encoding.strip().lower == 'ascii'

    def start(self) -> bool:
        self._output = FileRecordWriter.NoCloseTextIOWrapper(self._file, encoding=self.encoding)
        if self._headers and not self._omit_headers: self.write_headers()
        return True

    def finish(self):
        if self._output: self._output.flush()

    def close(self):
        try:
            if self._output is not None: self._output.close()
        finally:
            self._file = None
            self._output = None
            super().close()

    def write_headers(self):
        """This class doesn't write out headers at all"""

    def print(self, *args: any) -> None:
        """Utility method: does not add separator or line ending"""
        print(*args, sep='', end='', file=self._output)

    def println(self, *args: any) -> None:
        """Utility method: does not add separator"""
        print(*args, sep='', file=self._output)

    def flush(self) -> None:
        self._output.flush()

    def stringify(self, record: list[any]) -> list[any]:
        """Converts all the items to strings"""
        return [_stringify(item) for item in record]

    def objectify(self, record: list[any], include_null: bool=True) -> dict:
        """
        If the record is a dictionary, include all its attributes.
        Non dictionaries are turned into ones using the headers.
        Attributes that are None are optionally removed from both.
        """
        obj: dict = None
        if len(record) == 1 and isinstance(record[0], dict):
            obj = {k: v for k, v in record[0].items() if include_null or v is not None}
        else:
            obj = {k: v for k, v in zip(self._headers, record) if include_null or v is not None}
        return obj

    def _to_ascii(self, text: str) -> str:
        """
        If the underlying formatter cannot enforce ASCII on its own, call
        this method to convert it. Non-ASCII is converted to \\uNNNN escape sequences.
        Conversion will only be performed if required, but skip it if
        you know you can.
        """
        if self._encode_ascii: return ''.join(f"\\u{ord(c):04x}" if ord(c) > 127 else c for c in text)
        return text

    def _attrs(self) -> list:
        return super()._attrs() + ['encoding', 'encode_ascii', 'encode_utf8', 'headers', 'omit_headers']

    class NoCloseTextIOWrapper(TextIOWrapper):
        """Wrap the output so that we flush, but don't close when told to close.
        Use this when the stream was pre"""
        def close(self):
            # Override the close method to prevent closing the underlying buffer
            self.flush()

def _stringify(obj: Any) -> str:
    """
    Primitive "to_string()" operation.
    scalars are just sent to str(obj).
    dict are converted to a single line output.
    Collections are converted to a  comma separated list.
    """
    # Scalars, including str, are returned as-is
    if isinstance(obj, (str, int, float, bool, type(None))): return str(obj)
    # Compact JSON format for dictionaries
    if isinstance(obj, dict): return json.dumps(obj, separators=(",", ":"))
    # Recursively stringify iterable elements (arrays, tuples, etc)
    if isinstance(obj, Iterable): return ", ".join(map(_stringify, obj))
    # Fallback for unknown types
    return str(obj)
