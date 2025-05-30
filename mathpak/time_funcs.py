"""
Time related functions
"""

from datetime import datetime
from typing import Any

from .common import int_arg, str_arg, dist_x, type_str

def format_duration(x: Any, y: Any=0) -> Any:
    """
**Format the duration between two timestamps**

* _start_.FormatDuration(_end_)
* _end_.FormatDuration(_start_)
* _value_.FormatDuration()

Returns a string in the form of _n**d** _n**h** n**m** n**s**_ using the shortest
possible representation.
"""
    if x is None: x = 0
    if y is None: y = 0
    y = int(y.timestamp()) if isinstance(y, datetime) else int_arg(y, "End Time")
    if isinstance(x, (int, float, str)):
        x = int(x.timestamp()) if isinstance(x, datetime) else int_arg(x, "Start Time")
        delta = abs(x - y)
        d, rem = divmod(delta, 86400)
        h, rem = divmod(rem, 3600)
        m, s = divmod(rem, 60)
        parts = []
        if d: parts.append(f'{d}d')
        if h: parts.append(f'{h}h')
        if m: parts.append(f'{m}m')
        if s or not parts: parts.append(f'{s}s')
        return " ".join(parts)
    if isinstance(x, (list, tuple)): return dist_x(format_duration, x, y)
    raise TypeError(f'Unsupported type for timestamp: {type_str(x)}')

_DEFAULT_TS_FORMAT = '%FT%T'

def format_timestamp(x: Any, y: Any=None) -> Any:
    """
**Format a timestamp value**

* _timestamp_.FormatTimestamp()
* _timestamp_.FormatTimestamp(_format_)

If the timestamp is _none_ then the current date and time are used.
If the _format_ is omitted, the results is a ISO 8601 extended format, using a 4-digit year.
Time is separated by a **T** and uses a 24-hour format, with resolution down to the second.

The format follows Python's
[strftime() format codes](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes).

"""
    if x is None: x = datetime.now()
    if y is None: y = _DEFAULT_TS_FORMAT
    y = str_arg(y, "Timestamp Format")
    if isinstance(x, (list, tuple)): return dist_x(format_timestamp, x, y)
    if isinstance(x, (int, float, str)): x = datetime.fromtimestamp(int_arg(x, "Timestamp"))
    if isinstance(x, datetime): return x.strftime(y)
    raise TypeError(f'Unsupported type for timestamp: {type_str(x)}')
