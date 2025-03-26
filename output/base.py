"""
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from io import IOBase
from typing import Any
import json
import sys
import unicodedata

class RecordWriter(ABC):

    def __init__(self):
        self._debug = False
        self._verbose = False
        self._stderr = None

    @property
    def debug(self) -> bool:
        return self._debug

    @debug.setter
    def debug(self, enable: bool):
        self._debug = bool(enable)

    @property
    def verbose(self) -> bool:
        return self._verbose

    @verbose.setter
    def verbose(self, enable: bool):
        self._verbose = bool(enable)


    @property
    def stderr(self) -> bool:
        return self._stderr or sys.stderr

    @stderr.setter
    def stderr(self, out: IOBase):
        self._stderr = out if out is not None and isinstance(out, IOBase) else None

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

    def print_stderr(self, *args, **kwargs) -> None:
        """Same as print() except that it can redirect to an output file"""
        print(*args, file=self.stderr, **kwargs)

    def print_debug(self, *args, **kwargs) -> None:
        """If debug is on print to stderr"""
        if self.debug: self.print_stderr(*args, **kwargs)

    def print_verbose(self, *args, **kwargs) -> None:
        """If verbose is on print to stderr"""
        if self.verbose: self.print_stderr(*args, **kwargs)

    @abstractmethod
    def close(self):
        """Called to close/release resources"""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _attrs(self) -> list:
        """Return a list of attribute names to include in __repr__"""
        return ['debug', 'verbose', 'stderr']

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

class DelegatingRecordWriter(RecordWriter):

    def __init__(self, delegate: RecordWriter):
        self._delegate = delegate
        super().__init__()

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

    def __init__(self, file: IOBase=sys.stdout):
        self._file = file
        self._encode_ascii = False
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

    @property
    def encode_ascii(self) -> bool:
        return self._encode_ascii

    @encode_ascii.setter
    def encode_ascii(self, enable: bool):
        self._encode_ascii = bool(enable)

    def start(self) -> bool:
        if self._headers and self._include_headers: self.write_headers()
        return True

    def finish(self):
        self.flush()

    def close(self):
        try:
            self.flush()
        finally:
            self._file = None
            super().close()

    def write_headers(self):
        """This class doesn't write out headers at all"""

    def print(self, *args: any) -> None:
        """Utility method: does not add separator or line ending"""
        print(*args, sep='', end='', file=self._file)

    def println(self, *args: any) -> None:
        """Utility method: does not add separator"""
        print(*args, sep='', file=self._file)

    def flush(self) -> None:
        if self._file: self._file.flush()

    def objectify(self, record: list[any], include_nulls: bool=True) -> dict:
        """
        If the record is a dictionary, include all its attributes.
        Non dictionaries are turned into ones using the headers.
        Attributes that are None are optionally removed from both.
        """
        obj: dict = None
        if len(record) == 1 and isinstance(record[0], dict):
            obj = {k: v for k, v in record[0].items() if include_nulls or v is not None}
        else:
            obj = {k: v for k, v in zip(self._headers, record) if include_nulls or v is not None}
        return obj

    def _to_ascii(self, text: str) -> str:
        """
        If the underlying formatter cannot enforce ASCII on its own, call
        this method to convert it. Non-ASCII is converted to \\uNNNN escape sequences.
        Conversion will only be performed if required, but skip it if
        you know you can.
        """
        if text and self.encode_ascii:
            return unicodedata.normalize("NFKD", text).encode("ascii", "replace").decode("ascii")
        return text

    def _attrs(self) -> list:
        return super()._attrs() + ['encode_ascii', 'headers', 'include_headers']

    @classmethod
    def stringify(cls, obj: Any) -> str:
        """
        Primitive "to_string()" operation.
        scalars are just sent to str(obj).
        dict are converted to a single line output.
        Collections are converted to a  comma separated list.
        """
        if obj is None: return ''
        if not isinstance(obj, (str, int, float)):
            # Compact JSON format for dictionaries
            if isinstance(obj, dict): return json.dumps(obj, separators=(",", ":"))
            # Recursively stringify iterable elements (arrays, tuples, etc)
            if isinstance(obj, Iterable): return ", ".join(map(cls.stringify, obj))
        return str(obj)
