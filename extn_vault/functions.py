"""
Functions applicable to Vault data types.
"""

from typing import Any
import re

from mathpak import type_str, poly_floor

# Used in str -> ms
_DURATION_STR_PATTERN = re.compile(r'(-?\d+\.?\d*)(ns|us|µs|ms|s|m|h|d)?', re.IGNORECASE)
_TIME_UNITS_LOOKUP = {
    'ns': 1 / 1_000_000,
    'us': 1 / 1_000,
    'µs': 1 / 1_000,
    'ms': 1,
    's': 1_000,
    'm': 60 * 1_000,
    'h': 60 * 60 * 1_000,
    'd': 24 * 60 * 60 * 1_000
}

# Used in ms -> str
_TIME_UNITS_FACTOR = [
    ('d', 24 * 60 * 60 * 1000),
    ('h', 60 * 60 * 1000),
    ('m', 60 * 1000),
    ('s', 1000),
    ('ms', 1),
    ('us', 1 / 1000),
    ('ns', 1 / 1_000_000)
]

def duration_to_ms(duration: Any) -> int:
    """
**Convert a Vault duration value to milliseconds**

Numeric values are assumed to be in seconds.
String values are converted as per the Vault specification for duration strings.
"""
    if duration is None:
        return None
    # Numeric values are assumed to be in seconds
    if isinstance(duration, (int, float)):
        return int(duration * 1_000)
    if not isinstance(duration, str):
        raise ValueError(f'Unsupported duration type {type_str(duration)}')
    total_milliseconds = 0
    position = 0
    while position < len(duration):
        match = _DURATION_STR_PATTERN.match(duration, position)
        if not match:
            raise ValueError(f'Invalid duration format at {position}: {repr(duration)}')
        value, unit = match.groups()
        value = float(value)
        if unit is None:
            # No unit implies seconds
            unit = 's'
        else:
            unit = unit.lower()
        if unit not in _TIME_UNITS_LOOKUP:
            raise ValueError(f'Invalid time unit {repr(unit)} in duration string {repr(duration)}')
        total_milliseconds += value * _TIME_UNITS_LOOKUP[unit]
        position = match.end()
    return int(total_milliseconds)

def ms_to_duration(ms: Any) -> str:
    """
**Converts a duration in milliseconds into a Vault duration string**
"""
    if ms is None:
        return None
    if not isinstance(ms, (int, float)):
        raise ValueError(f'Unsupported duration type {type_str(ms)}')
    if ms == 0:
        return "0"
    result = []
    remaining_ms = float(ms)
    for unit, factor in _TIME_UNITS_FACTOR:
        if remaining_ms >= factor:
            # NB: his is the only place where "precission" is used with floor()
            value = poly_floor(remaining_ms / factor, .25)
            result.append(f'{value}{unit}')
            remaining_ms -= value * factor
            if remaining_ms <= 0: break
    return ''.join(result)

def _get_path_dict(obj, path):
    for key in path:
        if not isinstance(obj, dict) or key not in obj:
            return None
        obj = obj[key]
    return obj if isinstance(obj, dict) else None

def _is_flat_dict(obj) -> bool:
    """
    Is the object a dictionary, and if so, are all its items
    ordinal objects.
    """
    return isinstance(obj, dict) and all(
        not isinstance(v, (dict, list, tuple)) for v in obj.values()
    )

def _find_flat_data(obj, *full_path) -> dict:
    """
    Looks through the path of keys in a dictionary to find
    the best match for a "flat" data object.
    Used to ferret out likely candidate data from Vault return structures
    or "squishy" user extracted/modified/created dictionaries.
    """
    for i in range(len(full_path)):
        candidate = _get_path_dict(obj, full_path[i:])
        if candidate is not None and _is_flat_dict(candidate):
            return candidate
    if _is_flat_dict(obj):
        return obj
    return {}

def extract_kv_data(obj) -> dict:
    """
    Try to find a _data_ entry in the object
    for use with a Vault call.
    """
    return _find_flat_data(obj, "data", "data")

def extract_kv_metadata(obj) -> dict:
    """
    Try to find a _metadata_ or _custom_metadata_ entry in the
    object for use with a Vault call.
    """
    return _find_flat_data(obj, "data", "data", "metadata", "custom_metadata")

def add_kv_cas(obj: dict, cas: int) -> dict:
    """
    If cas is set, add the correct options to the object:
        **"options": { "cas": _value_ }**
    """
    if cas is not None:
        opts = obj.get('options', {})
        opts = {} if not isinstance(opts, dict) else opts
        opts['cas'] = int(cas)
        obj['options'] = opts
    return obj
