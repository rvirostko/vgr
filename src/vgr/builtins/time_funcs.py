"""
Time related functions
"""

from datetime import datetime
from typing import Any
import time

from .common import int_arg, str_arg, dist_x
from .type import poly_type
from .registry import builtin

_DEFAULT_TS_FORMAT = '%FT%T'

@builtin("GetDateTime")
def get_datetime() -> int:
    """
**Return the Unix Epoch time in seconds**

* GetDateTime()

```vgr
Printf "{} is {}\n", GetDateTime(), FormatDateTime()
 → "1779586384 is 2026-05-23T21:33:04"
```

Also see `FormatDateTime()` and the `time.now` variable
"""
    return int(time.time()) # Unix Epoch time

@builtin("FormatDuration")
def format_duration(x: Any=None, y: Any=None) -> Any:
    """
**Format the duration between two date-time values**

* FormatDuration(*value*)
* FormatDuration(*start*, *end*)
* FormatDuration(*end*, *start*)
* *value*.FormatDuration()
* *start*.FormatDuration(*end*)
* *end*.FormatDuration(*start*)

Returns a string in the form of *n***d** *n***h** *n***m** *n***s** using the shortest
possible representation.

```vgr
Set now To time.now
None.FormatDuration() → "0s"
now.FormatDuration(now + time.sec_per_hr) → "1h"
now.FormatDuration(now + time.sec_per_day) → "1d"
now.FormatDuration(now + 1_024) → "17m 4s"
now.FormatDuration(now + 8_192) → "2h 16m 32s"
(now + 32_768).FormatDuration(now) → "9h 6m 8s"
```

Also see `GetDateTime()` and the `time.now` variable
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
    if isinstance(x, list): return dist_x(format_duration, x, y)
    raise TypeError(f'Unsupported type for FormatDuration: {poly_type(x)!r}')

@builtin("FormatDateTime")
def format_datetime(x: Any=None, y: Any=None) -> Any:
    """
**Format the value for a point in time as a string**

* FormatDateTime()
* FormatDateTime(*value*)
* FormatDateTime(*value*, *format*)
* *value*.FormatDateTime()
* *value*.FormatDateTime(*format*)

If *value* is omitted or `None` then the current date and time are used.
If *format* is omitted or `None`, the results is a ISO 8601 extended format, using a 4-digit year.
Time is separated by a **T** and uses a 24-hour format, with resolution down to the second.

The *format* follows Python's **strftime()** directives

| Directive | Meaning                                 | Example.   |
|-----------|-----------------------------------------|------------|
| `%%`      | Literal `%` character                   | `%`        |
| `%a`      | Weekday abbreviated name                | `Mon`      |
| `%A`      | Weekday full name                       | `Monday`   |
| `%b`      | Month abbreviated name                  | `May`      |
| `%B`      | Month full name                         | `Feb`      |
| `%c`      | Locale appropriate date and time representation | `Sat May 23 14:45:30 2026` |
| `%d`      | Day of month zero-padded [01,31]        | `07`       |
| `%-d`     | Day of month [1,31] (no padding)        | `7`        |
| `%G`      | ISO 8601 year with century [0001,9999]  | `2026`     |
| `%H`      | Hour (24-hour) zero-padded [00,23]      | `04`       |
| `%-H`     | Hour (24-hour) [0,23] (no padding)      | `4`        |
| `%I`      | Hour (12-hour) zero-padded [01,12]      | `02`       |
| `%-I`     | Hour (12-hour) [1,12] (no padding)      | `2`        |
| `%j`      | Day of year zero-padded [001,366]       | `143`      |
| `%M`      | Minute zero-padded [00,59]              | `05`       |
| `%-M`     | Minute [0,59] (no padding)              | `5`        |
| `%m`      | Month zero-padded [01,12]               | `05`       |
| `%-m`     | Month [1,12] (no padding)               | `5`        |
| `%p`      | Locale appropriate AM or PM             | `AM`       |
| `%S`      | Second zero-padded [00,61]              | `05`       |
| `%-S`     | Second [0,61] (no padding)              | `5`        |
| `%u`      | ISO 8601 weekday [1,7], Monday=1        | `6`        |
| `%U`      | Week number zero-padded [00,53], Sunday start | `21` |
| `%V`      | ISO 8601 week number [01,53]            | `21`       |
| `%W`      | Week number zero-padded [00,53], Monday start | `21` |
| `%w`      | Weekday decimal number [0,6]            | `1`        |
| `%x`      | Locale appropriate date representation  | `05/23/26` |
| `%X`      | Locale appropriate time representation  | `14:45:30` |
| `%Y`      | Year with century                       | `2026`     |
| `%y`      | Year without century [00,99]            | `26`       |
| `%Z`      | Time zone name (empty if naive)         | `UTC`      |
| `%z`      | UTC offset in form ±HHMM[SS[.ffffff]]   | `+0000`    |

***Notes***

- `%-d`, `%-m`, etc. (with `-` modifier) are not zero-padded;
  platform-dependent support
- `%U` and `%W` treat January 1 as part of week 0/1 depending
  on which day of the week it is
- `%V` is part of ISO 8601; use with `%G` and `%u` for ISO week dates

Use `Exhibit time.format` for predefined formats.

```vgr
Set now To time.now
Set earlier To now - time.sec_per_hr
Set later To now + time.sec_per_hr
None.FormatDateTime() → "2025-09-30T17:01:22"
now.FormatDateTime() → "2025-09-30T17:01:22"
now.FormatDateTime(time.format.hms) → "17:01:22"
[earlier, now].FormatDateTime(time.format.hms) → ["16:01:22", "17:01:22"]
later.FormatDateTime(time.format.compact.hm) → "1801"
```
"""
    if x is None: x = datetime.now()
    if y is None: y = _DEFAULT_TS_FORMAT
    y = str_arg(y, "Format")
    if isinstance(x, list): return dist_x(format_datetime, x, y)
    if isinstance(x, (int, float, str)): x = datetime.fromtimestamp(int_arg(x, "DateTime"))
    if isinstance(x, datetime): return x.strftime(y)
    raise TypeError(f'Unsupported type for FormatDateTime: {poly_type(x)!r}')

@builtin("GetTimeZone")
def get_timezone(x: Any=None) -> str:
    """
**Return the local timezone name for a point in time**

* *value*.GetTimeZone()
* GetTimeZone()
* GetTimeZone(*value*)

If *value* is omitted or `None` then the current date and time are used.

```vgr
Printf "{}, {} {}, {} {:02d}:{:02d}:{:02d} {} (UTC{}{})\n",
    GetDayName(), GetMonthName(), GetDay(), GetYear(),
    GetHour(), GetMinute(), GetSecond(),
    GetTimeZone(),
    GetUtcOffset() Is Negative ? "-" : "+",
    GetUtcOffset().FormatDuration().Upper()
 → "Saturday, May 23, 2026 19:55:38 EDT (UTC-4H)"
```

Use `Exhibit time` for equivalent variables
"""
    return _generic_ts_func("GetTimeZone", get_timezone, lambda ts: ts.astimezone().tzname(), x)

@builtin("GetUtcOffset")
def get_utc_offset(x: Any=None) -> int:
    """
**Return the UTC offset for the local timezone in seconds for a point in time**

* *value*.GetUtcOffset()
* GetUtcOffset()
* GetUtcOffset(*value*)

If *value* is omitted or `None` then the current date and time are used.

```vgr
Printf "{}, {} {}, {} {:02d}:{:02d}:{:02d} {} (UTC{}{})\n",
    GetDayName(), GetMonthName(), GetDay(), GetYear(),
    GetHour(), GetMinute(), GetSecond(),
    GetTimeZone(),
    GetUtcOffset() Is Negative ? "-" : "+",
    GetUtcOffset().FormatDuration().Upper()
 → "Saturday, May 23, 2026 19:55:38 EDT (UTC-4H)"
```

Use `Exhibit time` for equivalent variables
"""
    return _generic_ts_func("UtcOffset", get_utc_offset, lambda ts: int(ts.astimezone().utcoffset().total_seconds()), x)

@builtin("GetDay")
def get_day(x: Any=None) -> int:
    """
**Return the day number within the month for a point in time**

If *value* is omitted or `None` then the current date and time are used.

* *value*.GetDay()
* GetDay()
* GetDay(*value*)

If *value* is omitted or `None` then the current date and time are used.

```vgr
Printf "{}, {} {}, {} {:02d}:{:02d}:{:02d} {} (UTC{}{})\n",
    GetDayName(), GetMonthName(), GetDay(), GetYear(),
    GetHour(), GetMinute(), GetSecond(),
    GetTimeZone(),
    GetUtcOffset() Is Negative ? "-" : "+",
    GetUtcOffset().FormatDuration().Upper()
 → "Saturday, May 23, 2026 19:55:38 EDT (UTC-4H)"
```

Use `Exhibit time` for equivalent variables
"""
    return _generic_ts_func("GetDay", get_day, lambda ts: ts.day, x)

@builtin("GetDayName")
def get_day_name(x: Any=None) -> str:
    """
**Return the name of the day of the week for a point in time**

If *value* is omitted or `None` then the current date and time are used.

* *value*.GetDayName()
* GetDayName()
* GetDayName(*value*)

```vgr
Printf "{}, {} {}, {} {:02d}:{:02d}:{:02d} {} (UTC{}{})\n",
    GetDayName(), GetMonthName(), GetDay(), GetYear(),
    GetHour(), GetMinute(), GetSecond(),
    GetTimeZone(),
    GetUtcOffset() Is Negative ? "-" : "+",
    GetUtcOffset().FormatDuration().Upper()
 → "Saturday, May 23, 2026 19:55:38 EDT (UTC-4H)"
```

Use `Exhibit time` for equivalent variables
"""
    return _generic_ts_func("GetDayName", get_day_name, lambda ts: ts.strftime("%A"), x)

@builtin("GetMonthName")
def get_month_name(x: Any=None) -> str:
    """
**Return the name of the month for a point in time**

* *value*.GetMonthName()
* GetMonthName()
* GetMonth(*value*)

If *value* is omitted or `None` then the current date and time are used.

```vgr
Printf "{}, {} {}, {} {:02d}:{:02d}:{:02d} {} (UTC{}{})\n",
    GetDayName(), GetMonthName(), GetDay(), GetYear(),
    GetHour(), GetMinute(), GetSecond(),
    GetTimeZone(),
    GetUtcOffset() Is Negative ? "-" : "+",
    GetUtcOffset().FormatDuration().Upper()
 → "Saturday, May 23, 2026 19:55:38 EDT (UTC-4H)"
```

Use `Exhibit time` for equivalent variables
"""
    return _generic_ts_func("GetMonthName", get_day_name, lambda ts: ts.strftime("%B"), x)

@builtin("GetHour")
def get_hour(x: Any=None) -> int:
    """
**Return the hour of the day (0-23) for a point in time**

* *value*.GetHour()
* GetHour()
* GetHour(*value*)

If *value* is omitted or `None` then the current date and time are used.

```vgr
Printf "{}, {} {}, {} {:02d}:{:02d}:{:02d} {} (UTC{}{})\n",
    GetDayName(), GetMonthName(), GetDay(), GetYear(),
    GetHour(), GetMinute(), GetSecond(),
    GetTimeZone(),
    GetUtcOffset() Is Negative ? "-" : "+",
    GetUtcOffset().FormatDuration().Upper()
 → "Saturday, May 23, 2026 19:55:38 EDT (UTC-4H)"
```

Use `Exhibit time` for equivalent variables
"""
    return _generic_ts_func("GetHour", get_hour, lambda ts: ts.hour, x)

@builtin("GetMinute")
def get_minute(x: Any=None) -> int:
    """
**Return the minute within the hour for a point in time**

* *value*.GetMinute()
* GetMinute()
* GetMinute(*value*)

If *value* is omitted or `None` then the current date and time are used.

```vgr
Printf "{}, {} {}, {} {:02d}:{:02d}:{:02d} {} (UTC{}{})\n",
    GetDayName(), GetMonthName(), GetDay(), GetYear(),
    GetHour(), GetMinute(), GetSecond(),
    GetTimeZone(),
    GetUtcOffset() Is Negative ? "-" : "+",
    GetUtcOffset().FormatDuration().Upper()
 → "Saturday, May 23, 2026 19:55:38 EDT (UTC-4H)"
```

Use `Exhibit time` for equivalent variables
"""
    return _generic_ts_func("GetMinute", get_minute, lambda ts: ts.minute, x)

@builtin("GetMonth")
def get_month(x: Any=None) -> int:
    """
**Return the month within the year for a point in time**

* *value*.GetMonth()
* GetMonth()
* GetMonth(*value*)

If *value* is omitted or `None` then the current date and time are used.

```vgr
Printf "{} is month number {}\n",
    GetMonthName(), GetMonth()
 → "May is month number 5"
```

Use `Exhibit time` for equivalent variables
"""
    return _generic_ts_func("GetMonth", get_month, lambda ts: ts.month, x)

@builtin("GetSecond")
def get_second(x: Any=None) -> int:
    """
**Return the second within the hour for a point in time**

* *value*.GetSecond()
* GetSecond()
* GetSecond(*value*)

If *value* is omitted or `None` then the current date and time are used.

```vgr
Printf "{}, {} {}, {} {:02d}:{:02d}:{:02d} {} (UTC{}{})\n",
    GetDayName(), GetMonthName(), GetDay(), GetYear(),
    GetHour(), GetMinute(), GetSecond(),
    GetTimeZone(),
    GetUtcOffset() Is Negative ? "-" : "+",
    GetUtcOffset().FormatDuration().Upper()
 → "Saturday, May 23, 2026 19:55:38 EDT (UTC-4H)"
```

Use `Exhibit time` for equivalent variables
"""
    return _generic_ts_func("GetSecond", get_second, lambda ts: ts.second, x)

@builtin("GetDayOfWeek")
def get_day_of_week(x: Any=None) -> int:
    """
**Return the number (0-6) for the day of the week for a point in time**

* *value*.GetDayOfWeek()
* GetDayOfWeek()
* GetDayOfWeek(*value*)

If *value* is omitted or `None` then the current date and time are used.

```vgr
Printf "{} is {}\n", GetDayName(), GetDayOfWeek()
 → "Saturday is 6"
```

Use `Exhibit time` for equivalent variables
"""
    return _generic_ts_func("GetDayOfWeek", get_day_of_week, lambda ts: (ts.weekday() + 1) % 7, x)

@builtin("GetDayOfYear")
def get_day_of_year(x: Any=None) -> int:
    """
**Return the number of the day within the year for a point in time**

* *value*.GetDayOfYear()
* GetDayOfYear()
* GetDayOfYear(*value*)

If *value* is omitted or `None` then the current date and time are used.

```vgr
Printf "Day {} of {} is {} {}\n",
    GetDayOfYear(), GetYear(),
    GetMonthName(), GetDay()
 → "Day 143 of 2026 is May 23:
```

Use `Exhibit time` for equivalent variables
"""
    return _generic_ts_func("GetDayOfYear", get_day_of_year, lambda ts: ts.timetuple().tm_yday, x)

@builtin("GetYear")
def get_year(x: Any=None) -> int:
    """
**Return the year for a point in time**

* *value*.GetYear()
* GetYear()
* GetYear(*value*)

If *value* is omitted or `None` then the current date and time are used.

```vgr
Printf "{}, {} {}, {} {:02d}:{:02d}:{:02d} {} (UTC{}{})\n",
    GetDayName(), GetMonthName(), GetDay(), GetYear(),
    GetHour(), GetMinute(), GetSecond(),
    GetTimeZone(),
    GetUtcOffset() Is Negative ? "-" : "+",
    GetUtcOffset().FormatDuration().Upper()
 → "Saturday, May 23, 2026 19:55:38 EDT (UTC-4H)"
```

Use `Exhibit time` for equivalent variables
"""
    return _generic_ts_func("GetYear", get_year, lambda ts: ts.year, x)

@builtin("GetWeekOfYear")
def get_week_of_year(x: Any=None) -> int:
    """
**Return the week within the year for a point in time**

* *value*.GetWeekOfYear()
* GetWeekOfYear()
* GetWeekOfYear(*value*)

If *value* is omitted or `None` then the current date and time are used.

```vgr
Printf "{} {} is in week {} of {}\n",
    GetMonthName(), GetDay(),
    GetWeekOfYear(), GetYear()
 → "May 23 is in week 20 of 2026"
```

Use `Exhibit time` for equivalent variables
"""
    return _generic_ts_func("GetWeekOfYear", get_week_of_year, lambda ts: int(ts.strftime("%W")), x)

def _generic_ts_func(name: str, func, impl, x: Any) -> Any:
    if x is None: return impl(datetime.now())
    if isinstance(x, datetime): return impl(x)
    if isinstance(x, list): return list(func(x1) for x1 in x)
    if isinstance(x, (int, float, str)): return impl(datetime.fromtimestamp(int_arg(x, "DateTime")))
    raise TypeError(f'Unsupported type for {name}: {poly_type(x)!r}')
