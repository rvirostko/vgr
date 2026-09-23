
from typing import Any
from .vpattern import VPattern

def as_str(value: Any) -> Any:
    if isinstance(value, (bool, int, float)): return str(value)
    if isinstance(value, VPattern): return value.pattern
    return value
