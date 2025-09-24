"""
Statistical functions
"""

from functools import cmp_to_key
from typing import Any, Iterable
import statistics

from .inequ import poly_lt, poly_gt
from .common import str_to_number, type_str

def poly_max(x: Any, *args: Any) -> Any:
    """
**Return the largest item in collection or an assembly of data**
"""
    if not args:
        if isinstance(x, (list, tuple)):
            return max(x, key=cmp_to_key(_cmp_to_key_asc), default=None)
        return x
    return max(_flatten((x, *args)), key=cmp_to_key(_cmp_to_key_asc), default=None)

def poly_min(x: Any, *args: Any) -> Any:
    """
**Return the smallest item in collection or an assembly of data**
"""
    if not args:
        if isinstance(x, (list, tuple)):
            return min(x, key=cmp_to_key(_cmp_to_key_asc), default=None)
        return x
    return min(_flatten((x, *args)), key=cmp_to_key(_cmp_to_key_asc), default=None)

def poly_mean(x: Any, *data: Any) -> Any:
    """
**Calculte the arithimethic mean in a collection or an assembly of data**
"""
    data = _coerce_to_numbers(_filter_none(_flatten((x, *data))))
    return statistics.mean(data) if data else None

def poly_median(x: Any, *data: Any) -> Any:
    """
**Return the median value in a collection or an assembly of data**
"""
    data = _coerce_to_numbers(_filter_none(_flatten((x, *data))))
    return statistics.median(data) if data else None

def poly_mode(x: Any, *data: Any) -> Any:
    """
**Return the mode of a collection or an assembly of data**
"""
    data = _coerce_to_numbers(_filter_none(_flatten((x, *data))))
    return statistics.mode(data) if data else None

#multimode(data)
def poly_multimode(x: Any, *data: Any) -> Any:
    """
**Return a list of modes of a collection or an assembly of data**
"""
    data = _coerce_to_numbers(_filter_none(_flatten((x, *data))))
    return statistics.multimode(data) if data else None

def poly_stdev(x: Any, *data: Any) -> Any:
    """
**Return the sample standard deviation for a collection or an assembly of data**
"""
    data = _coerce_to_numbers(_filter_none(_flatten((x, *data))))
    return statistics.stdev(data) if data else None

def poly_variance(x: Any, *data: Any) -> Any:
    """
**Return the sample variance for a collection or an assembly of data**
"""
    data = _coerce_to_numbers(_filter_none(_flatten((x, *data))))
    return statistics.variance(data) if data else None

def poly_pstdev(x: Any, *data: Any) -> Any:
    """
**Return the population standard deviation for a collection or an assembly of data**
"""
    data = _coerce_to_numbers(_filter_none(_flatten((x, *data))))
    return statistics.pstdev(data) if data else None

def poly_pvariance(x: Any, *data: Any) -> Any:
    """
**Return the population variance for a collection or an assembly of data**
"""
    data = _coerce_to_numbers(_filter_none(_flatten((x, *data))))
    return statistics.pvariance(data) if data else None

def _coerce_to_numbers(values):
    result = []
    for v in values:
        if isinstance(v, (int, float)):
            result.append(v)
        elif isinstance(v, str):
            result.append(str_to_number(v))
        else:
            raise ValueError(f'{type_str(v)} cannot be converted to a number')
    return result

def _cmp_to_key_asc(x: Any, y: Any):
    """For ascending comparisons; reverse x/y for descending"""
    return -1 if poly_lt(x, y) else (1 if poly_gt(x, y) else 0)

def _filter_none(iterable: Iterable[Any]) -> list:
    return [x for x in iterable if x is not None]

def _flatten(values):
    for item in values:
        if isinstance(item, (list, tuple)):
            yield from item
        else:
            yield item
