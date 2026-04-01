"""
The interface between the method of extracting data and the
filtering and output systems.
"""

from abc import ABC, abstractmethod
from typing import Any

class InfoOutput(ABC):
    @abstractmethod
    def print_debug(self, *args, **kwargs) -> None:
        """Extractors may call this to generate debugging information"""

    @abstractmethod
    def print_verbose(self, /, *args, **kwargs) -> None:
        """Extractors may call this to generate verbose information"""

class QueryFilter(ABC):
    """
    A query filter handles the filtering and output of data
    """
    @abstractmethod
    def filter_intermediate(self) -> bool:
        """
        Called to handle the filtering of intermediate
        steps in a hierarchical data model.
        Returns True if the data did not fail filtering
        and traversal of the model may proceede.
        """

    @abstractmethod
    def filter_target(self, data: Any) -> bool:
        """
        Called to handle the filtering and output of data.
        Returns True if the data passed filtering and was
        sent to the output.
        Extractors need not perform any actions regardless
        of the return value.
        """

    @abstractmethod
    def set_data(self, key: str, data: Any) -> None:
        """
        Used to set intermediate and target data items in the
        data dictionary prior to any filter call.
        The extractor is responsible for calling unset_data()
        once items in their data model go out of scope.
        """

    @abstractmethod
    def unset_data(self, key: str) -> None:
        """
        Used to remove intermediate and target data items in the
        data dictionary after filter calls.
        The extractor is responsible for calling this
        once items in their data model go out of scope.
        """

class DataExtractor(ABC):

    def __init__(self):
        super().__init__()
        self._attrs = []

    @property
    def attrs(self) -> list[str]:
        return self._attrs

    def start(self, io: InfoOutput) -> None:
        """Override if your class requires some activity before extracting"""

    @abstractmethod
    def extract(self, qfilter: QueryFilter, io: InfoOutput) -> None:
        pass

    def finish(self, io: InfoOutput) -> None:
        """Override if your class requires some activity after extracting"""

class EndExtractException(Exception):
    """
    This may be raised by an extractor or other mechanisms
    durring extraction. It causes a premature, but non-error,
    termination of the extraction.
    Mostly, handled internally, but if an extractor has particular
    conditions which force a normal end to the extraction, it can
    raise this exception.
    Extractors should not attempt to handle this exception, which
    includes logging.
    """
    def __init__(self, *args):
        super().__init__(*args)
