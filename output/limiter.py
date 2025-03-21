#! /usr/bin/env python3

from .base import RecordWriter, DelegatingRecordWriter

class RecordLimiter(DelegatingRecordWriter):

    def __init__(self, delegate: RecordWriter, **kwargs):
        super().__init__(delegate)
        self._offset = None
        self._limit = None
        self._setattrs(**kwargs)

    @classmethod
    def wrap(cls, output: RecordWriter, **kwargs) -> RecordWriter:
        """
        Wraps output if applicable
        If the arguments contain either 'limit' or 'offset' and
        either one has a value greater than zero, the output writer
        will be wrapped with a limiter.
        """
        limit = kwargs.get('limit', None)
        offset = kwargs.get('offset', None)
        if not cls._is_gt_zero(limit) and not cls._is_gt_zero(offset): return output
        return RecordLimiter(output, **kwargs)

    @property
    def limit(self) -> int:
        return self._limit

    @limit.setter
    def limit(self, limit: int):
        self._limit = limit if self._is_gt_zero(limit) else None

    @property
    def offset(self) -> int:
        return self._offset

    @offset.setter
    def offset(self, offset: int):
        self._offset = offset if self._is_gt_zero(offset) else None

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
    def _is_gt_zero(cls, v: int) -> bool:
        return v is not None and v >= 1

    def _attrs(self) -> list:
        return super()._attrs() + ['offset', 'limit']
