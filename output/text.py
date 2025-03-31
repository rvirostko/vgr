"""
A simple text output
"""

import sys
from io import FileIO
from .base import FileRecordWriter

class TextRecordWriter(FileRecordWriter):

    def __init__(self, file: FileIO=sys.stdout, **kwargs):
        super().__init__(file)
        self._setattrs(**kwargs)

    def write(self, record: list[any]) -> bool:
        for item in record:
            if item is not None:
                if self.encode_ascii:
                    super().println(self._to_ascii(item))
                else:
                    super().println(item)
        return True
