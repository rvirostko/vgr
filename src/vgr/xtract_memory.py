"""
A DataExtractor that iterates over items store in a list
"""

from .data_xtract import (
    DataExtractor,
    InfoOutput,
    QueryFilter,
)
from .mathpak import poly_list

class InMemoryExtractor(DataExtractor):
    """
    An extractor that works from data read into memory
    """
    def __init__(self, data: list, target: str):
        super().__init__()
        self._data = poly_list(data)
        self._target = target

    def __repr__(self):
        return "InMemoryExtractor(target=" + repr(self._target) + ", data_len=" + str(len(self._data) if self._data else 0) + ")"

    def start(self, io: InfoOutput):
        """Nothing"""

    def finish(self, io: InfoOutput):
        """Nothing"""

    def extract(self, qfilter: QueryFilter, io: InfoOutput):
        """
        Because this is a flat data model we simply iterate
        over the data adding it to the data dictionary, then
        telling the query filter to test is as a target.
        """
        for obj in self._data:
            if obj is not None:
                try:
                    qfilter.set_data(self._target, obj)
                    qfilter.filter_target(obj)
                finally:
                    qfilter.unset_data(self._target)
