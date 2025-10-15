"""
A DataExtractor that iterates over items store in a list
"""

from .data_xtract import (
    DataExtractor,
    InfoOutput,
    QueryFilter,
)

class InMemoryExtractor(DataExtractor):
    """
    An extractor that works from a list of data read into memory
    """
    def __init__(self, data: list, target: str):
        super().__init__()
        self._data = [] if data is None else data if isinstance(data, list) else [data]
        self._target = target

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
