#! /usr/bin/env python3

import json
import sys
from io import FileIO
from .base import FileRecordWriter

class JSONRecordWriter(FileRecordWriter):

    def __init__(self, file: FileIO=sys.stdout.buffer):
        super().__init__(file)
        self._root = None
        self._indent = 2
        self._compact = False
        self._include_null = True
        self._sort_keys = False
        self._array_wrapper = True

    def set_root(self, name: str):
        self._root = None if name is None else name.strip()
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
        self._formater.write(self.objectify(record, self._include_null))
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

        def flush(self) -> None: self._writer.flush()

    class ObjectModeFormater(JFormater):
        def __init__(self, writer):
            super().__init__(writer)

        def start(self) -> None:
            self.print('{', self._sp, '"', self._writer._root, '":', self._sp, '[')
            self._first = True
            self.flush()

        def finish(self) -> None:
            self.opt_nl()
            self.println(']', self._sp, '}')
            self.flush()

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
            self.flush()

    class ListModeFormater(JFormater):
        def __init__(self, writer):
            super().__init__(writer)

        def write(self, obj: dict) -> None:
            self.println(json.dumps(obj,
                        indent=None,
                        sort_keys=self._writer._sort_keys,
                        ensure_ascii=self._writer._encode_ascii,
                        separators=self._separators))
            self.flush()

        def finish(self) -> None: self.flush()
