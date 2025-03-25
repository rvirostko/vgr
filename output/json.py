import json
import sys
from io import FileIO
from .base import FileRecordWriter

class JSONRecordWriter(FileRecordWriter):

    def __init__(self, file: FileIO=sys.stdout, **kwargs):
        super().__init__(file)
        self._formater = None
        self._root = None
        self._indent = None
        self._compact = False
        self._include_nulls = True
        self._sort_keys = False
        self._array_wrapper = True
        self._setattrs(**kwargs)

    def _attrs(self) -> list:
        return super()._attrs() + ['root', 'indent', 'compact', 'include_nulls', 'sort_keys', 'array_wrapper' ]

    @property
    def root(self) -> str:
        return self._root

    @root.setter
    def root(self, name: str):
        self._root = None if name is None else name.strip()

    @property
    def indent(self) -> int:
        return self._indent

    @indent.setter
    def indent(self, value) -> None:
        self._indent = None if value is None else min(max(0, value), 64)

    @property
    def compact(self) -> bool:
        return self._compact

    @compact.setter
    def compact(self, enable: bool):
        self._compact = bool(enable)
        if enable: self.indent = None

    @property
    def include_nulls(self) -> bool:
        return self._include_nulls

    @include_nulls.setter
    def include_nulls(self, enable: bool):
        self._include_nulls = bool(enable)

    @property
    def sort_keys(self) -> bool:
        return self._sort_keys

    @sort_keys.setter
    def sort_keys(self, enable: bool):
        self._sort_keys = bool(enable)

    @property
    def array_wrapper(self):
        return not self._array_wrapper

    @array_wrapper.setter
    def array_wrapper(self, enable: bool):
        self._array_wrapper = bool(enable)

    def start(self) -> bool:
        if not super().start(): return False
        if self.root:
            # "object mode" : entire output is an object with <root> as an array
            self._formater = JSONRecordWriter.ObjectModeFormater(self)
        else:
            if self._array_wrapper:
                # "array mode" : output is a array of all the rows
                self._formater = JSONRecordWriter.ArrayModeFormater(self)
            else:
                # "list mode" : output is a series of lines, each a json object
                self._formater = JSONRecordWriter.ListModeFormater(self)
        self._formater.start()
        return True

    def write(self, record: list[any]) -> bool:
        self._formater.write(self.objectify(record, self._include_nulls))
        return True

    def finish(self) -> None:
        try:
            if self._formater: self._formater.finish()
        finally:
            self._formater = None
            super().finish()

    class JFormater():

        def __init__(self, writer: "JSONRecordWriter"):
            self._writer = writer
            self._separators = (',', ':') if writer.compact else (', ', ': ')
            self._sp = '' if writer.compact else ' '

        def start(self) -> None: pass
        def finish(self) -> None: pass
        def write(self, obj: dict) -> None: pass

        def print(self, *args: any) -> None:
            self._writer.print(*args)

        def println(self, *args: any) -> None:
            self._writer.println(*args)

        def flush(self) -> None: self._writer.flush()

    class ArrayModeFormater(JFormater):
        def __init__(self, writer):
            super().__init__(writer)
            self._first = False

        def start(self) -> None:
            self.print('[')
            self._first = True
            self.flush()

        def finish(self) -> None:
            self.println()
            self.println(']')
            self.flush()

        def write(self, obj: dict) -> None:
            if self._first:
                self._first = False
            else:
                self.print(',')
            self.println()
            self.print(json.dumps(obj,
                        indent=self._writer.indent,
                        sort_keys=self._writer.sort_keys,
                        ensure_ascii=self._writer.encode_ascii,
                        separators=self._separators))
            self.flush()

    class ObjectModeFormater(JFormater):
        def __init__(self, writer):
            super().__init__(writer)
            self._first = False

        def start(self) -> None:
            self.print('{', self._sp, '"', self._writer.root, '":', self._sp, '[')
            self._first = True
            self.flush()

        def finish(self) -> None:
            self.println()
            self.println(']', self._sp, '}')
            self.flush()

        def write(self, obj: dict) -> None:
            if self._first:
                self._first = False
            else:
                self.print(',')
            self.println()
            self.print(json.dumps(obj,
                        indent=self._writer.indent,
                        sort_keys=self._writer.sort_keys,
                        ensure_ascii=self._writer.encode_ascii,
                        separators=self._separators))
            self.flush()

    class ListModeFormater(JFormater):
        def write(self, obj: dict) -> None:
            self.println(json.dumps(obj,
                        indent=None,
                        sort_keys=self._writer.sort_keys,
                        ensure_ascii=self._writer.encode_ascii,
                        separators=self._separators))
            self.flush()

        def finish(self) -> None:
            self.flush()
