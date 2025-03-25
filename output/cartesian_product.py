import itertools
from .base import RecordWriter, DelegatingRecordWriter

class RecordCartesianProduct(DelegatingRecordWriter):

    def __init__(self, delegate: RecordWriter, **kwargs):
        """Use product: list[bool] to set columns to use in product"""
        super().__init__(delegate)
        self._product = None
        self._setattrs(**kwargs)

    @classmethod
    def wrap(cls, output: RecordWriter, **kwargs) -> RecordWriter:
        """
        Wraps output if applicable
        Use product: list[bool] to set columns to use in product
        """
        product: list[bool] = kwargs.get('product', None)
        if not isinstance(product, list): return output
        return RecordCartesianProduct(output, **kwargs) if any(product) else output

    @property
    def product(self) -> list[bool]:
        return self._product

    @product.setter
    def product(self, product: list[bool]):
        self._product = product if isinstance(product, list) and len(product) > 0 else None

    def write(self, record: list[any]) -> bool:
        for row in self._row_product(record):
            if not self._delegate.write(row): return False
        return True

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
        yield from itertools.product(*iterable_values)

    def _attrs(self) -> list:
        return super()._attrs() + ['product']
