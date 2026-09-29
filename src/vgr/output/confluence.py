from typing import Any
import sys
from io import FileIO

from .base import FileRecordWriter

class ConfluenceRecordWriter(FileRecordWriter):
    __BAR = '|'
    __DBAR = '||'

    def __init__(self, file: FileIO=sys.stdout, **kwargs):
        super().__init__(file)
        self._setattrs(**kwargs)

    def write(self, record: list[Any]) -> bool:
        for item in record: self.print(self.__BAR, self._encode_confluence(item))
        self.println(self.__BAR)
        return True

    def write_headers(self) -> bool:
        # Headers go through the same encoding logic as data but use a differenct separator
        for header in [self._encode_confluence(item) for item in self._headers]: self.print(self.__DBAR, header)
        self.println(self.__DBAR)
        return True

    @classmethod
    def _encode_confluence(cls, value: Any) -> str:
        """Strips leading/trailing whitespace, escapes '|', deals with embedded line breaks etc"""
        value = cls.stringify(value).strip()
        return value if len(value) == 0 else (
            value
            .replace(cls.__BAR, r'\|')
            .replace("\r", " ")
            .replace("\r\n", r"\\")
            .replace("\n", r"\\")
        )
