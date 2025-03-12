#! /usr/bin/python3

import csv
import itertools
import json

from abc import ABC, abstractmethod
from io import FileIO, TextIOWrapper

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

class RecordLimiter(DelegatingRecordWriter):

    def __init__(self, delegate: RecordWriter):
        super().__init__(delegate)
        self._offset = None
        self._limit = None

    def set_limit(self, limit: int=0):
        self._limit = limit if self._is_pos(limit) else None
        return self

    def set_offset(self, offset: int=0):
        self._offset = offset if self._is_pos(offset) else None
        return self

    def _exhausted(self) -> bool:
        return self._limit is not None and self._limit <= 0

    def start(self) -> bool:
        # Deal with starting with a limit of <= 1
        if self._exhausted(): return False
        return False if self._exhausted() else self._delegate.start()

    def write(self, record: list[any]) -> bool:
        if self._exhausted(): return False
        if self._offset is not None and self._offset > 0:
            self._offset -= 1
            return True
        if self._limit is not None: self._limit -= 1
        return self._delegate.write(record)

    @classmethod
    def wrap(cls, output: RecordWriter, limit: int=0, offset: int=0) -> RecordWriter:
        """Wraps output if applicable"""
        return RecordLimiter(output).set_limit(limit).set_offset(offset) if cls._is_pos(limit) or cls._is_pos(offset) else output

    @classmethod
    def _is_pos(cls, v: int) -> bool : return (v is not None and v >= 1)

class RecordCartesianProduct(DelegatingRecordWriter):

    def __init__(self, delegate: RecordWriter, product: list[bool]):
        super().__init__(delegate)
        self._product = product

    def _row_product(self, record: list[any]):
        iterable_values: list = []
        for value, project in zip(record, self._product):
            if project:
                # Do NOT perform product on strings! (they are iterable character arrays)
                if not isinstance(value, str) and hasattr(value, '__iter__'):
                    if len(value) > 0:
                        # product of a 'collection': iterator should suffice
                        iterable_values.append(value)
                    else:
                        # product of an empty 'collection': needs to generate one row
                        iterable_values.append([None])
                else:
                    # product of an ordinal: treat as a list of one
                    iterable_values.append([value])
            else:
                # not a product: treat as a list of one regardless of type
                iterable_values.append([value])
        # itertools perform the product and we yeild multiple rows of data
        for x in itertools.product(*iterable_values): yield x

    def write(self, record: list[any]) -> bool:
        for row in self._row_product(record):
            if not self._delegate.write(row): return False
        return True

    @classmethod
    def wrap(cls, output: RecordWriter, projections: list[bool]) -> RecordWriter:
        """Wraps output if applicable"""
        return RecordCartesianProduct(output, projections) if any(projections) else output

class FileRecordWriter(RecordWriter):

    def __init__(self, file: FileIO):
        super().__init__()
        self._file = file
        self._output: TextIOWrapper = None
        self._encode_ascii = False
        self._headers = []

    def set_headers(self, headers: list[any]=[]):
        self._headers = headers
        return self

    def start(self) -> bool:
        if self._output is not None or self._file is None: raise ValueError() # SNO
        self._output = TextIOWrapper(self._file, encoding=self._output_encoding())
        if self._headers: self._write_headers()
        return True

    def finish(self):
        pass

    def close(self):
        try:
            if self._output is not None: self._output.close()
        finally:
            self._file = None
            self._output = None
            super().close()

    def _write_headers(self): pass

    def set_encode_ascii(self, enable: bool=True):
        self._encode_ascii = enable
        return self

    def set_encode_utf8(self, enable: bool=True):
        self._encode_ascii = not enable
        return self

    def _output_encoding(self) -> str:
        return "ascii" if self._encode_ascii else 'utf-8'

    def _encoding(self) -> str:
        return "ASCII" if self._encode_ascii else 'Unicode'

    def print(self, *args: any) -> None:
        # TODO
        print(*args, sep='', end='', file=self._output)
        #print(*args, sep='', end='')

    def println(self, *args: any) -> None:
        # TODO
        print(*args, sep='', file=self._output)
        #print(*args, sep='')

class MarkdownRecordWriter(FileRecordWriter):
    __BAR = '|'
    __ESC_BAR = '\\|'
    __WS = [ '\t', '\n', '\r' ]

    def __init__(self, file: FileIO):
        super().__init__(file)

    @classmethod
    def _clean_text(cls, value: any) -> str:
        """Strips leading/trailing whitespace, escapes '|', deals with embedded tabs/line breaks"""
        if value is None: return ''
        if not isinstance(value, str): value = str(value)
        value = value.strip()
        if not value: return value
        for c in cls.__WS: value = value.replace(c, ' ')
        return value.replace(cls.__BAR, cls.__ESC_BAR)

    def write(self, record: list[any]) -> bool:
        if record:
            for item in record: self.print(self.__BAR, self._clean_text(item))
            self.println(self.__BAR)
        return True

    def _write_headers(self):
        if self.write(self._headers):
            for _ in self._headers:  self.print('|-')
            self.println(self.__BAR)

class CSVRecordWriter(FileRecordWriter):
    def __init__(self, file: FileIO):
        super().__init__(file)
        self._delimiter = ','
        self._quotechar = '"'
        self._escapechar = None
        self._lineterminator = '\n'
        self._quoting = csv.QUOTE_MINIMAL

    def set_delimiter(self, value: str):
        self._delimiter = self._sanitize_char(value, ',')
        return self

    def set_quotechar(self, value: str):
        self._quotechar = self._sanitize_char(value, '"')
        return self

    def set_escapechar(self, value: str):
        self._escapechar = self._sanitize_char(value)
        return self

    def set_lineterminator(self, value: str):
        self._lineterminator = value if value else "\n"
        return self

    # TODO probably all wrong...
    __VALID_QUOTING = [csv.QUOTE_ALL, csv.QUOTE_MINIMAL, csv.QUOTE_NONNUMERIC, csv.QUOTE_NONE]
    def set_quoting(self, value):
        self._quoting = value if self.__VALID_QUOTING else csv.QUOTE_ALL
        return self

    def _sanitize_char(cls, value: str, default: str=None):
        if not value: value = default
        # Use only the first character
        return value[0] if value else None

    def start(self) -> bool:
        self._writer = csv.writer(self._output,
                                    delimiter=self._delimiter,
                                    quotechar=self._quotechar,
                                    escapechar=self._escapechar,
                                    lineterminator=self._lineterminator,
                                    quoting=self._quoting)
        # TODO asci/unicode/excel
        return super().start()

    def finish(self) -> None:
        self._writer = None
        super().finish()

    def write(self, record: list[any]) -> bool:
        # TODO anything "special" for handling None columns?
        self._writer.writerow(record)
        return True

    def _write_headers(self) -> bool:
        return super()._write_headers()

class JSONRecordWriter(FileRecordWriter):

    __DEFAULT_ROOT = 'results'

    def __init__(self, file: FileIO):
        super().__init__(file)
        self._root = self.__DEFAULT_ROOT
        self._indent = 2
        self._compact = False
        self._include_null = True
        self._sort_keys = False
        self._array_wrapper = True

    def set_root(self, name: str):
        self._root = name
        if name is None: self._array_wrapper = False
        return self

    def set_indent(self, value: int=0):
        self._indent = None if value is None else min(max(0, value), 64)
        return self

    def set_compact(self, enable: bool=True):
        self._compact = enable
        if enable: self._indent = 0
        return self

    def set_include_null(self, enable: bool=True):
        self._include_null = enable
        return self

    def set_sort_keys(self, enable: bool=True):
        self._sort_keys = enable
        return self

    def set_exclude_array_wrapper(self, enable: bool=True):
        self._array_wrapper = not enable
        return self

    def start(self) -> bool:
        if not super().start(): return False
        if self._array_wrapper:
            # "object mode" : entire output is an object with <root> as an array
            self._root = self._root or JSONRecordWriter.__DEFAULT_ROOT
            self._formater = JSONRecordWriter.ObjectModeFormater(self)
        else:
            # "list mode" : output is a series of lines, each a json object
            self._formater = JSONRecordWriter.ListModeFormater(self)
        self._formater.start()
        return True

    def write(self, record: list[any]) -> bool:
        obj: dict = None
        if len(record) == 1 and isinstance(record[0], dict):
            obj = {k: v for k, v in record[0].items() if self._include_null or v is not None}
        else:
            obj = {k: v for k, v in zip(self._headers, record) if self._include_null or v is not None}
        self._formater.write(obj)
        return True

    def finish(self) -> None:
        self._formater.finish()
        super().finish()

    class JFormater():

        def __init__(self, writer: "JSONRecordWriter"):
            self._writer = writer
            self._separators = (',', ':') if writer._compact else (', ', ': ')
            self._sp = '' if writer._compact else ' '

        def start(self) -> None: pass
        def finish(self) -> None: pass
        def write(self, obj: dict) -> None: pass

        def opt_nl(self) -> None:
            if self._writer._indent is not None: self.println()

        def print(self, *args: any) -> None:
            self._writer.print(*args)

        def println(self, *args: any) -> None:
            self._writer.println(*args)

    class ObjectModeFormater(JFormater):
        def __init__(self, writer):
            super().__init__(writer)

        def start(self) -> None:
            self.print('{', self._sp, '"', self._writer._root, '":', self._sp, '[')
            self._first = True

        def finish(self) -> None:
            self.opt_nl()
            self.println(']', self._sp, '}')

        def write(self, obj: dict) -> None:
            if self._first:
                self._first = False
            else:
                self.print(',')
            self.opt_nl()
            self.print(json.dumps(obj,
                        indent=self._writer._indent,
                        sort_keys=self._writer._sort_keys,
                        ensure_ascii=self._writer._encode_ascii,
                        separators=self._separators))

    class ListModeFormater(JFormater):
        def __init__(self, writer):
            super().__init__(writer)

        def write(self, obj: dict) -> None:
            self.println(json.dumps(obj,
                        indent=None,
                        sort_keys=self._writer._sort_keys,
                        ensure_ascii=self._writer._encode_ascii,
                        separators=self._separators))

###################################
import sys
def main():

    # These would be in the data from the select statement's parse tree
    offset = 0#4
    limit = None#4
    #output_type = "markdown"
    output_type = "csv"
    #output_type = "json"
    ascii = False#True
    include_null = False#True
    root = None#'people'
    compact = True
    indent = 2
    sort_keys = True


    # The data that would come back from the query
    # TODO need to test output with single dict
    headers = [ "name", "age", "pos" ]
    product = [False, False, False]
    data = [
        ["Alice", 25, "Engineer"],
        ["Bob", 30, "Doctor"],
        ["Carol", 28, "Data || Analyst"],
        ["Dave", 35, "Data | Engineer"],
        ["Jimbo", 22, ["Hobo", "Jerk"]],
        ["Limbo", None, ["Hobo", "♠"]]
    ]

    out: RecordWriter = None
    if output_type == 'markdown':
        out = MarkdownRecordWriter(sys.stdout)
    elif output_type == 'csv':
        out = CSVRecordWriter(sys.stdout)
    elif output_type == 'json':
        out = JSONRecordWriter(sys.stdout)
        out.set_compact(compact)
        out.set_root(root)
        out.set_include_null(include_null)
        out.set_indent(indent)
        out.set_sort_keys(sort_keys)
    else:
        raise ValueError(output_type)
    # common options
    out.set_headers(headers).set_encode_ascii(ascii)
    # Order is important since projections can generate more than one row
    # It depends upon how you want to interpret the limit/offset, and that is TBD
    out = RecordLimiter.wrap(out, limit, offset)
    out = RecordCartesianProduct.wrap(out, product)
    if out.start():
        for row in data:
            if not out.write(row): break
        out.finish()

if __name__ == "__main__":
    main()
#    data = {"key1": "value1", "key2": 42, "key3": None, "nested": {"a": 1, "b": 2}}
#
#    json_string = json.dumps(data, indent=None, separators=(",", ":"))
#    print(json_string)
