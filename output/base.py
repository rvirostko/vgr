#! /usr/bin/env python3

import json
import sys
from abc import ABC, abstractmethod
from io import FileIO, TextIOWrapper
from collections.abc import Iterable

class RecordWriter(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def start(self) -> bool:
        """Returns True if writing can continue"""
        pass

    @abstractmethod
    def finish(self):
        pass

    @abstractmethod
    def write(self, record: list[any]) -> bool:
        """Write a single record to the output
        Returns True if writing can continue"""
        pass

    @abstractmethod
    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class DelegatingRecordWriter(RecordWriter):

    def __init__(self, delegate: RecordWriter):
        self._delegate = delegate

    def start(self) -> bool:
        return self._delegate.start()

    def finish(self):
        self._delegate.finish()

    def write(self, record: list[any]) -> bool:
        return self._delegate.write(record)

    def close(self):
        self._delegate.close()

class FileRecordWriter(RecordWriter):

    def __init__(self, file: FileIO=sys.stdout.buffer):
        super().__init__()
        self._file = file
        self._output: TextIOWrapper = None
        self._encode_ascii = False
        self._headers = []
        self._omit_headers = False

    def set_headers(self, headers: list[any]=[]):
        self._headers = headers
        return self

    def set_omit_headers(self, enable: bool=True):
        self._omit_headers = enable
        return self

    def start(self) -> bool:
        self._output = FileRecordWriter.NoCloseTextIOWrapper(self._file, encoding=self.output_encoding())
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

    def set_encode_ascii(self, enable: bool=True):
        self._encode_ascii = enable
        return self

    def set_encode_utf8(self, enable: bool=True):
        self._encode_ascii = not enable
        return self

    def write_headers(self): pass

    def output_encoding(self) -> str:
        return "ascii" if self._encode_ascii else 'utf-8'

    def print(self, *args: any) -> None:
        print(*args, sep='', end='', file=self._output)

    def println(self, *args: any) -> None:
        print(*args, sep='', file=self._output)

    def flush(self) -> None: self._output.flush()

    def stringify(self, record: list[any]) -> list[any]: return [_stringify(item) for item in record]

    def objectify(self, record: list[any], include_null: bool=True) -> dict:
        obj: dict = None
        if len(record) == 1 and isinstance(record[0], dict):
            obj = {k: v for k, v in record[0].items() if include_null or v is not None}
        else:
            obj = {k: v for k, v in zip(self._headers, record) if include_null or v is not None}
        return obj

    class NoCloseTextIOWrapper(TextIOWrapper):
        def close(self):
            # Override the close method to prevent closing the underlying buffer
            self.flush()

def _stringify(obj: any) -> str:
    # Scalars, including str, are returned as-is
    if isinstance(obj, (str, int, float, bool, type(None))): return str(obj)
    # Compact JSON format for dictionaries
    if isinstance(obj, dict): return json.dumps(obj, separators=(",", ":"))
    # Recursively stringify iterable elements (arrays, tuples, etc)
    if isinstance(obj, Iterable): return ", ".join(map(_stringify, obj))
    # Fallback for unknown types
    return str(obj)
