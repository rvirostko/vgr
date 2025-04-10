import csv
import sys
from io import FileIO, StringIO
from .base import FileRecordWriter

NoneType = type(None)

class CSVRecordWriter(FileRecordWriter):

    __QUOTING = {
            'all': csv.QUOTE_ALL,
            'minimal': csv.QUOTE_MINIMAL,
            'nonnumeric': csv.QUOTE_NONNUMERIC,
            'none': csv.QUOTE_NONE
        }
    __DEFAULT_QUOTING = csv.QUOTE_NONNUMERIC
    __DEFAULT_DELIMITER = ','
    __DEFAULT_QUOTE_CHAR = '"'
    __DEFAULT_ESCAPE_CHAR = '\\'
    __DEFAULT_LINE_TERMINATOR = '\n'

    def __init__(self, file: FileIO=sys.stdout, **kwargs):
        super().__init__(file)
        self._outstr = None
        self._writer = None
        self._delimiter = self.__DEFAULT_DELIMITER
        self._quotechar = self.__DEFAULT_QUOTE_CHAR
        self._escapechar = self.__DEFAULT_ESCAPE_CHAR
        self._lineterminator = self.__DEFAULT_LINE_TERMINATOR
        self._quoting = self.__DEFAULT_QUOTING
        self._setattrs(**kwargs)

    def _attrs(self) -> list:
        return super()._attrs() + ['delimiter', 'quotechar', 'escapechar', 'lineterminator', 'quoting']

    @property
    def delimiter(self) -> str:
        return self._delimiter

    @delimiter.setter
    def delimiter(self, value: str):
        self._delimiter = self._sanitize_char(value, self.__DEFAULT_DELIMITER)

    @property
    def quotechar(self) -> str:
        return self._quotechar

    @quotechar.setter
    def quotechar(self, value: str):
        self._quotechar = self._sanitize_char(value, self.__DEFAULT_QUOTE_CHAR)

    @property
    def escapechar(self) -> str:
        return self._escapechar

    @escapechar.setter
    def escapechar(self, value: str):
        self._escapechar = self._sanitize_char(value, self.__DEFAULT_ESCAPE_CHAR)

    @property
    def lineterminator(self) -> str:
        return self._lineterminator

    @lineterminator.setter
    def lineterminator(self, value: str):
        self._lineterminator = value if value is not None else self.__DEFAULT_LINE_TERMINATOR

    @property
    def quoting(self) -> str:
        s = [k for k, v in self.__QUOTING.items() if v == self._quoting]
        return s[0] if s else self.__DEFAULT_QUOTING

    @quoting.setter
    def quoting(self, value: str=None):
        if value is None:
            self._quoting = self.__DEFAULT_QUOTING
        else:
            self._quoting = self.__QUOTING.get(value.strip().lower(), self.__DEFAULT_QUOTING)
            # TODO need another none check

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
                                  quoting=self._quoting,
                                )
        self._flush_str()
        return super().start()

    def finish(self) -> None:
        try:
            if self._outstr: self._flush_str()
        finally:
            self._outstr = None
            self._writer = None
            super().finish()

    def write(self, record: list[any]) -> bool:
        # We don't want to change numbers to strings
        self._writer.writerow([item if isinstance(item, (NoneType, int, float)) else self.stringify(item) for item in record])
        self._flush_str()
        return True

    def write_headers(self) -> bool:
        self._writer.writerow(self._headers)
        self._flush_str()
        return True

    def _flush_str(self) -> None:
        self.print(self._to_ascii(self._outstr.getvalue()))
        # Clear the buffer and reset to start
        self._outstr.truncate(0)
        self._outstr.seek(0)
