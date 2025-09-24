import sys
from io import FileIO

from .base import FileRecordWriter

class MarkdownRecordWriter(FileRecordWriter):
    __BAR = '|'
    __ESC_BAR = '\\|'
    __WS = [ '\t', '\n', '\r' ]

    def __init__(self, file: FileIO=sys.stdout, **kwargs):
        super().__init__(file)
        self._setattrs(**kwargs)

    def write(self, record: list[any]) -> bool:
        for item in record:
            self.print(self.__BAR, self._clean_text(self.stringify(item)))
        self.println(self.__BAR)
        return True

    def print(self, *args):
        if self.encode_ascii:
            super().print(self._to_ascii(a) for a in args)
        else:
            super().print(*args)

    def write_headers(self):
        if self.write(self._headers):
            for _ in self._headers:  self.print('|-')
            self.println(self.__BAR)

    @classmethod
    def _clean_text(cls, value: any) -> str:
        """Strips leading/trailing whitespace, escapes '|', deals with embedded tabs/line breaks"""
        if value is None: return ''
        if not isinstance(value, str): value = str(value)
        value = value.strip()
        if not value: return value
        for c in cls.__WS: value = value.replace(c, ' ')
        return value.replace(cls.__BAR, cls.__ESC_BAR)
