#! /usr/bin/env python3

from .base import RecordWriter, DelegatingRecordWriter

class RecordLimiter(DelegatingRecordWriter):

    def __init__(self, delegate: RecordWriter):
        super().__init__(delegate)
        self._offset = None
        self._limit = None

    @classmethod
    def wrap(cls, output: RecordWriter, limit: int=0, offset: int=0) -> RecordWriter:
        """Wraps output if applicable"""
        if not cls._is_pos(limit) and not cls._is_pos(offset): return output
        return RecordLimiter(output).set_limit(limit).set_offset(offset)

    def set_limit(self, limit: int=0):
        self._limit = limit if self._is_pos(limit) else None
        return self

    def set_offset(self, offset: int=0):
        self._offset = offset if self._is_pos(offset) else None
        return self

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

    def _exhausted(self) -> bool:
        return self._limit is not None and self._limit <= 0

    @classmethod
    def _is_pos(cls, v: int) -> bool : return (v is not None and v >= 1)
