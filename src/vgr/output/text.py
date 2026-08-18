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
        self._header_sep = ':'
        self._field_sep = ' '
        self._record_sep = '\n'
        self.include_headers = False
        self._setattrs(**kwargs)

    def _attrs(self) -> list:
        return super()._attrs() + ['header_sep', 'field_sep', 'record_sep']

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

    def write_headers(self):
        if self.include_headers:
            first = True
            for header in self.headers:
                if first:
                    self.print(header)
                    first = False
                else:
                    self.print(self._header_sep, header)
            self.print(self.record_sep)

    def write(self, record: list[any]) -> bool:
        first = True
        for item in record:
            if first:
                self.print(self.stringify(item))
                first = False
            else:
                self.print(self._field_sep, self.stringify(item))
        self.print(self.record_sep)
        return True
