"""
Statistical functions
"""

from functools import cmp_to_key
from typing import Any, Iterable
import statistics

from .common import str_to_number
from .inequ import poly_lt, poly_gt
from .type import poly_type

def poly_max(*args: Any) -> Any:
    """
**Return the largest item in collection or an assembly of data**

```vgr
**TODO**
```
"""
    return max(_flatten(args), key=cmp_to_key(_cmp_to_key_asc), default=None) if args else None

def poly_min(*args: Any) -> Any:
    """
**Return the smallest item in collection or an assembly of data**

```vgr
**TODO**
```
"""
    return min(_flatten(args), key=cmp_to_key(_cmp_to_key_asc), default=None) if args else None

def poly_mean(*args: Any) -> Any:
    """
**Calculte the arithimethic mean in a collection or an assembly of data**

```vgr
**TODO**
```
"""
    args = _coerce_to_numbers(_filter_none(_flatten(args))) if args else None
    return statistics.mean(args) if args else None

def poly_median(*args: Any) -> Any:
    """
**Return the median value in a collection or an assembly of data**

```vgr
**TODO**
```
"""
    args = _coerce_to_numbers(_filter_none(_flatten(args))) if args else None
    return statistics.median(args) if args else None

def poly_mode(*args: Any) -> Any:
    """
**Return the mode of a collection or an assembly of data**

```vgr
**TODO**
```
"""
    args = _coerce_to_numbers(_filter_none(_flatten(args))) if args else None
    return statistics.mode(args) if args else None

def poly_multimode(*args: Any) -> Any:
    """
**Return a list of modes of a collection or an assembly of data**

```vgr
**TODO**
```
"""
    args = _coerce_to_numbers(_filter_none(_flatten(args))) if args else None
    return statistics.multimode(args) if args else None

def poly_stdev(*args: Any) -> Any:
    """
**Return the sample standard deviation for a collection or an assembly of data**

```vgr
**TODO**
```
"""
    args = _coerce_to_numbers(_filter_none(_flatten(args))) if args else None
    return statistics.stdev(args) if args and len(args) > 1 else None

def poly_variance(*args: Any) -> Any:
    """
**Return the sample variance for a collection or an assembly of data**

```vgr
**TODO**
```
"""
    args = _coerce_to_numbers(_filter_none(_flatten(args))) if args else None
    return statistics.variance(args) if args and len(args) > 1 else None

def poly_pstdev(*args: Any) -> Any:
    """
**Return the population standard deviation for a collection or an assembly of data**

```vgr
**TODO**
```
"""
    args = _coerce_to_numbers(_filter_none(_flatten(args))) if args else None
    return statistics.pstdev(args) if args else None

def poly_pvariance(*args: Any) -> Any:
    """
**Return the population variance for a collection or an assembly of data**

```vgr
**TODO**
```
"""
    args = _coerce_to_numbers(_filter_none(_flatten(args))) if args else None
    return statistics.pvariance(args) if args else None

def _coerce_to_numbers(values):
    result = []
    for v in values:
        if isinstance(v, (int, float)):
            result.append(v)
        elif isinstance(v, str):
            result.append(str_to_number(v))
        else:
            raise ValueError(f'{poly_type(v)!r} cannot be converted to a number')
    return result

def _cmp_to_key_asc(x: Any, y: Any):
    """For ascending comparisons; reverse x/y for descending"""
    return -1 if poly_lt(x, y) else (1 if poly_gt(x, y) else 0)

def _filter_none(iterable: Iterable[Any]) -> list:
    return [x for x in iterable if x is not None]

def _flatten(values):
    for item in values:
        if isinstance(item, list):
            yield from item
        else:
            yield item
