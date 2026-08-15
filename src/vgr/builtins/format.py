import string
from re import Pattern

from .as_str import as_str
from .registry import builtin
from .type import poly_type

class SafeFormatter(string.Formatter):
    def get_value(self, key, args, kwargs):
        try:
            return self._filter_types(super().get_value(key, args, kwargs))
        except (KeyError, IndexError):
            # Missing keys are treated as None
            return None

    def get_field(self, field_name, args, kwargs):
        try:
            obj, arg_used = super().get_field(field_name, args, kwargs)
            return self._filter_types(obj), arg_used
        except (KeyError, IndexError, AttributeError, TypeError):
            # Missing fields etc treated as None
            return None, field_name

    def format_field(self, value, format_spec):
        try :
            return 'None' if value is None else super().format_field(value, format_spec)
        except ValueError as e:
            raise ValueError(f"Unknown or unsupported format {format_spec!r} for {poly_type(value)} argument") from e

    def _filter_types(self, value):
        # Filter out unsupported types
        return value if isinstance(value, (bool, int, float, str, list, dict, Pattern)) else None

@builtin("Format")
def poly_format(*args) -> str:
    """
**Format values into a string**

* Format(*format*, *expression*&hellip;)
* Format(*format*, *expression*&hellip;)
* *format*.Format(*expression*&hellip;)
* *format*.Format(*expression*&hellip;)

Formatting syntax is that used in [Python's str.format()](https://docs.python.org/3/library/string.html#formatstrings)

**Formatting Cheat Sheet**

***Basic usage***

```vgr
"Hello, {}".Format("world")    → "Hello, world"
"{0} + {0} = {1}".Format(2, 4) → "2 + 2 = 4"
```

***Number formatting***

```vgr
"{:d}".Format(42)       → "42" // decimal
"{:b}".Format(42)       → "101010" // binary
"{:x}".Format(42)       → "2a" // hex, lowercase
"{:X}".Format(42)       → "2A" // hex, uppercase
"{:o}".Format(42)       → "52" // octal
"{:e}".Format(3.14)     → "3.140000e+00" // scientific
"{:.2f}".Format(3.1415) → "3.14" // fixed-point, 2 decimals
```

***Alignment & width***

```vgr
"{:<10}".Format("hi")  →  "hi        " // left align
"{:>10}".Format("hi")  →  "        hi" // right align
"{:^10}".Format("hi")  →  "    hi    " // center
"{:*^10}".Format("hi") →  "****hi****" // custom fill
```

***Signs & numbers***

```vgr
"{:+d}".Format(42)     → "+42"
"{:+d}".Format(-42)    → "-42"
"{: d}".Format(42)     → " 42" // space for positive
"{:,}".Format(1234567) → "1,234,567" // thousands sep
"{:_}".Format(1234567) → "1_234_567"
```

***Accessing elements***

```vgr
Set person To {"name": "Alice", "age": 25}
"{0[name]} is {0[age]}".Format(person) → "Alice is 25"
```

***Format control***

```vgr
"{0} {0!r} {0!s}".Format("hi") → "hi 'hi' hi" // raw vs str formatting
"{0:.{1}f}".Format(3.14159, 2) → "3.14" // precision via argument
```
"""
    # NOTE: the syntax {0.x} is also defined but refers to object fields/properties
    # print("{0.upper}".format(s))
    # print("{0.__class__}".format(s))
    # The intrinsics dont have very many useful things, so we filter out
    # types of objects we don't support
    if not args: return None
    format_string, *args = args
    if format_string is None: return None
    format_string = as_str(format_string)
    if isinstance(format_string, str):
        return SafeFormatter().format(format_string, *args)
    if isinstance(format_string, list):
        return list(poly_format(f, *args) for f in format_string)
    raise TypeError(f'Format with {poly_type(format_string)!r} not supported')
