"""
A DataExtractor that iterates over items store in memory
"""

from typing import Any

from .builtins import (
    poly_getkeys,
    poly_list,
)
from .data_xtract import (
    DataExtractor,
    InfoOutput,
    QueryFilter,
)

class InMemoryExtractor(DataExtractor):
    """
    An extractor that works from data read into memory
    """
    def __init__(self, target: str, data: Any):
        super().__init__()
        self._target = target
        self._data = poly_list(data)
        self._as_kv = False
        if isinstance(data, list):
            self._attrs = poly_getkeys(self._data)
        elif isinstance(data, dict):
            # NB: if data is a dict, we are going to iterate over its keys and values
            #     because of the way poly_list() (called above) works
            self._attrs = [ "key", "value" ]
            self._as_kv = True
        else:
            # data was either None or an ordinal
            # so there is no attribute to work with,
            # just the thing itself
            self._attrs = [ target ]

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return "InMemoryExtractor(" + \
            "target=" + repr(self._target) + ", " + \
            "data_len=" + str(len(self)) + ", " + \
            "attrs=" + repr(self.attrs) + ")"

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
            try:
                if self._as_kv: obj = { "key": obj[0], "value": obj[1] }
                qfilter.set_data(self._target, obj)
                qfilter.filter_target(obj)
            finally:
                qfilter.unset_data(self._target)
