
from typing import Any
from re import Pattern

def as_str(value: Any) -> Any:
    if isinstance(value, (bool, int, float)): return str(value)
    if isinstance(value, Pattern): return value.pattern
    return value
