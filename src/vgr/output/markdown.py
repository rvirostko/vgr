from typing import Any
import sys
from io import FileIO

from .base import FileRecordWriter

class MarkdownRecordWriter(FileRecordWriter):
    __BAR = '|'
    __ALIGN_LEFT =    "|:----"
    __ALIGN_CENTER =  "|:---:"
    __ALIGN_RIGHT =   "|----:"
    __ALIGN_DEFAULT = "|-----"

    def __init__(self, file: FileIO=sys.stdout, **kwargs):
        super().__init__(file)
        self._setattrs(**kwargs)

    def start(self) -> None:
        # Override base class because we interpret the "no headers" differently
        self.write_headers()

    def write(self, record: list[Any]) -> bool:
        for item in record: self.print(self.__BAR, self._encode_markdown(item))
        self.println(self.__BAR)
        return True

    def write_headers(self) -> bool:
        # Headers go through the same encoding logic as data
        headers = [self._encode_markdown(item) for item in self._headers]
        # but we remove the alignment encoding
        for header in headers: self.print(self.__BAR, self._strip_alignment(header))
        self.println(self.__BAR)
        # Now the bar that specifies the previous line is a table header
        # and any alignment if encoded in the header text
        for header in headers:  self.print(self._get_alignment(header))
        self.println(self.__BAR)
        return True

    def _strip_alignment(self, value: str) -> str:
        # When headers are off, we still need to include something
        # otherwise the Markdown table collapses into a non-table
        # So, when off, you get a blank label.
        if not self._include_headers: return ""
        if len(value) < 1 : return value
        if value[0] == ":": return value[1:-1] if len(value) > 1 and value[-1] == ":" else value[1:]
        return value[:-1] if value[-1] == ":" else value

    @classmethod
    def _get_alignment(cls, value: str) -> str:
        if len(value) < 1 : return cls.__ALIGN_DEFAULT
        if value[0] == ":": return cls.__ALIGN_CENTER if len(value) > 1 and value[-1] == ":" else cls.__ALIGN_LEFT
        return cls.__ALIGN_RIGHT if value[-1] == ":" else cls.__ALIGN_DEFAULT

    @classmethod
    def _encode_markdown(cls, value: Any) -> str:
        """Strips leading/trailing whitespace, escapes '|', deals with embedded line breaks etc"""
        value = cls.stringify(value).strip()
        # NB: We don't change </>/& as we assume the user has generated them intentionally
        # This is mostly handling code which would unintentionally break the table cell
        return value if len(value) == 0 else (
            value
            .replace(cls.__BAR, r'\|')
            .replace("\r", " ")
            .replace("\r\n", "<br>")
            .replace("\n", "<br>")
        )
