"""
A simple text output
"""

import sys
from io import FileIO
from .base import FileRecordWriter

class TextRecordWriter(FileRecordWriter):
    """A simple printing output

    - headers : headers for the data values. No default.
    - include_headers : should the headers be written before the data values. Defaults to False.
    - include_nulls : should null fields be written or skipped. Defaults to True.
    - header_sep : text to appear between the header name and value. Defaults to ":"
    - field_sep : text to appear between fields. Default to space.
    - record_sep : text to appear between records. Default to new line.

    If a record consits of all null values, the record separator is not output
    """

    def __init__(self, file: FileIO=sys.stdout, **kwargs):
        super().__init__(file)
        self._setattrs(**kwargs)
        self._header_sep = ':'
        self._field_sep = ' '
        self._record_sep = '\n'
        self._include_nulls = True
        self.include_headers = False

    def _attrs(self) -> list:
        return super()._attrs() + ['include_nulls', 'header_sep', 'field_sep', 'record_sep']

    @property
    def include_nulls(self) -> bool:
        return self._include_nulls

    @include_nulls.setter
    def include_nulls(self, enable: bool):
        self._include_nulls = bool(enable)

    @property
    def header_sep(self) -> bool:
        return self._header_sep

    @header_sep.setter
    def header_sep(self, value: str):
        self._header_sep = '' if value is None else str(value)

    @property
    def field_sep(self) -> bool:
        return self._field_sep

    @field_sep.setter
    def field_sep(self, value: str):
        self._field_sep = '' if value is None else str(value)

    @property
    def record_sep(self) -> bool:
        return self._record_sep

    @record_sep.setter
    def record_sep(self, value: str):
        self._record_sep = '' if value is None else str(value)

    def write(self, record: list[any]) -> bool:
        first = True
        if self.include_headers:
            for header, item in zip(self.headers, record):
                if self.include_nulls or item is not None:
                    if first:
                        self._print(header, self._header_sep, item)
                        first = False
                    else:
                        self._print(self._field_sep, header, self._header_sep, item)
        else:
            for item in record:
                if self.include_nulls or item is not None:
                    if first:
                        self._print(item)
                        first = False
                    else:
                        self._print(self._field_sep, item)
        # Only print a record sep if we printed anything
        if not first: self._print(self.record_sep)
        return True

    def _print(self, *args: any) -> None:
        """Apply to_ascii() to all args if applicable"""
        for arg in args:
            if self.encode_ascii:
                super().print(self._to_ascii(arg))
            else:
                super().print(arg)
