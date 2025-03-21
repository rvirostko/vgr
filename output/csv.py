#! /usr/bin/env python3

import csv
import sys
from io import FileIO, StringIO
from .base import FileRecordWriter

class CSVRecordWriter(FileRecordWriter):

    __QUOTING = {
            'all': csv.QUOTE_ALL,
            'minimal': csv.QUOTE_MINIMAL,
            'nonnumeric': csv.QUOTE_NONNUMERIC,
            'none': csv.QUOTE_NONE
        }
    __DEFAULT_QUOTING = csv.QUOTE_NONNUMERIC

    def __init__(self, file: FileIO=sys.stdout.buffer):
        super().__init__(file)
        self._outstr = None
        self._writer = None
        self.set_delimiter()
        self.set_quotechar()
        self.set_escapechar()
        self.set_lineterminator()
        self.set_quoting()

    def set_delimiter(self, value: str=None):
        self._delimiter = self._sanitize_char(value, ',')
        return self

    def set_quotechar(self, value: str=None):
        self._quotechar = self._sanitize_char(value, '"')
        return self

    def set_escapechar(self, value: str=None):
        self._escapechar = self._sanitize_char(value, '\\')
        return self

    def set_lineterminator(self, value: str=None):
        self._lineterminator = value if value else "\n"
        return self

    def set_quoting(self, value: str=None):
        self._quoting = self.__QUOTING.get(value.strip().lower(), self.__DEFAULT_QUOTING) if value else self.__DEFAULT_QUOTING
        return self

    def _sanitize_char(self, value: str, default: str=None):
        if not value: value = default
        # Use only the first character
        return value[0] if value else None

    def start(self) -> bool:
        self._outstr = StringIO()
        self._writer = csv.writer(self._outstr,
                                    delimiter=self._delimiter,
                                    quotechar=self._quotechar,
                                    escapechar=self._escapechar,
                                    lineterminator=self._lineterminator,
                                    quoting=self._quoting)
        self._flush_str()
        # TODO asci/unicode/excel
        return super().start()

    def finish(self) -> None:
        try:
            if self._outstr: self._flush_str()
        finally:
            self._outstr = None
            self._writer = None
            super().finish()

    def write(self, record: list[any]) -> bool:
        self._writer.writerow(self.stringify(record))
        self._flush_str()
        return True

    def write_headers(self) -> bool:
        self._writer.writerow(self._headers)
        self._flush_str()
        return True

    def _flush_str(self) -> None:
        self.print(self._outstr.getvalue())
        # Clear the buffer and reset to start
        self._outstr.truncate(0)
        self._outstr.seek(0)
