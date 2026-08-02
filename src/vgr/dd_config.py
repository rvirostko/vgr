
"""
Utility routines for working with the global Data Dictionary
"""

import getpass
import math
import os
import platform
import re
import socket
import string
import sys
import uuid

from . import __version__, __version_date__
from .builtins import (
    get_cwd,
    get_datetime,
    get_day_name,
    get_day_of_month,
    get_day_of_year,
    get_dow,
    get_hour,
    get_minute,
    get_month_name,
    get_month,
    get_second,
    get_week_of_year,
    get_year,
    poly_rnd,
    timezone,
    utc_offset,
)
from .data_dict import DataDictionary, DynamicValue, MAX_FRAMES
from .redir import _REDIRECTOR
from .stmt_include import (
    get_includes,
    get_is_included,
)
from .stmt_set import get_user_constants
from .stmt_funct import (
    DEFAULT_CACHE_SIZE,
    MAX_CACHE_SIZE,
)
from .user_callable import cache_keys

VGR_PREFIX = 'vgr'
VER_PATH = (VGR_PREFIX, 'version')
VER_DATE_PATH = (VGR_PREFIX, 'version_date')
EXEC_NAME_PATH = (VGR_PREFIX, 'python', 'executable')
EXEC_VER_PATH = (VGR_PREFIX, 'python', 'version')

_TIME_PREFIX = 'time'

OFS_PATH = ('env', 'OFS')
ORS_PATH = ('env', 'ORS')

_ENV_EXCLUDE = tuple(re.compile(pattern, re.IGNORECASE) for pattern in ('^VSCODE', '^_$', '^(OLD)?PWD$', '^__CF'))
_OS_CONSTS = ( 'defpath',  'devnull', 'extsep', 'linesep', 'name', 'pardir', 'pathsep', 'sep' )
_SYS_CONSTS = ( 'api_version', 'builtin_module_names', 'byteorder', 'exec_prefix', 'executable', 'maxsize',
    'maxunicode', 'platform', 'platlibdir', 'prefix', 'pycache_prefix', 'version',)

_RE_PREFIX = 're'
_RE_FLAGS = ('ASCII', 'DEBUG', 'IGNORECASE', 'MULTILINE', 'DOTALL', 'VERBOSE')

_COMPACT = "compact"
_FORMAT = "format"
_TODAY = "today"
_TIME_ENTRIES = {
    ("now",):                       DynamicValue(get_datetime), # Unix Epoch time
    ("sec_per_day",):               60 * 60 * 24,
    ("sec_per_hr",):                60 * 60,
    ("tz_name", ):                  DynamicValue(timezone),
    ("utc_offset",):                DynamicValue(utc_offset),
    # "today" is a composite object
    (_TODAY, "day_name"):           DynamicValue(get_day_name),     # Saturday
    (_TODAY, "day_of_week"):        DynamicValue(get_dow),          # 5 (Sunday=0)
    (_TODAY, "day_of_year"):        DynamicValue(get_day_of_year),  # 172
    (_TODAY, "day"):                DynamicValue(get_day_of_month), # 21
    (_TODAY, "hour"):               DynamicValue(get_hour),         # 14
    (_TODAY, "minute"):             DynamicValue(get_minute),       # 23
    (_TODAY, "month"):              DynamicValue(get_month),        # 6
    (_TODAY, "month_name"):         DynamicValue(get_month_name),   # June
    (_TODAY, "second"):             DynamicValue(get_second),       # 45
    (_TODAY, "week_of_year"):       DynamicValue(get_week_of_year), # 21
    (_TODAY, "year"):               DynamicValue(get_year),         # 2025
    # Formats for datetime value
    (_FORMAT, "dmy"):               r"%d-%m-%Y",                    # 21-06-2025
    (_FORMAT, "dt"):                r"%Y-%m-%d %H:%M:%S",           # 2025-06-21 14:23:45
    (_FORMAT, "hm"):                r"%H:%M",                       # 14:23
    (_FORMAT, "hms"):               r"%H:%M:%S",                    # 14:23:45
    (_FORMAT, "mdy"):               r"%m/%d/%Y",                    # 06/21/2025
    (_FORMAT, "ymd"):               r"%Y-%m-%d",                    # 2025-06-21
    # Compact variants
    (_FORMAT, _COMPACT, "dmy"):     r"%d%m%Y",                      # 21062025
    (_FORMAT, _COMPACT, "dt"):      r"%Y%m%d_%H%M%S",               # 20250621_142345
    (_FORMAT, _COMPACT, "hm"):      r"%H%M",                        # 1423
    (_FORMAT, _COMPACT, "hms"):     r"%H%M%S",                      # 142345
    (_FORMAT, _COMPACT, "mdy"):     r"%m%d%Y",                      # 06212025
    (_FORMAT, _COMPACT, "ymd"):     r"%Y%m%d",                      # 20250621
    # Standards
    (_FORMAT, "iso8601_ms_offset"): r"%Y-%m-%dT%H:%M:%S.%f%z",      # 2025-06-21T14:23:45.123456+0000
    (_FORMAT, "iso8601_offset"):    r"%Y-%m-%dT%H:%M:%S%z",         # 2025-06-21T14:23:45+0000
    (_FORMAT, "iso8601_z"):         r"%Y-%m-%dT%H:%M:%SZ",          # 2025-06-21T14:23:45Z
    (_FORMAT, "iso8601"):           r"%Y-%m-%dT%H:%M:%S",           # 2025-06-21T14:23:45
    (_FORMAT, "rfc1123"):           r"%a, %d %b %Y %H:%M:%S GMT",   # Sat, 21 Jun 2025 14:23:45 GMT
    (_FORMAT, "rfc2822"):           r"%a, %d %b %Y %H:%M:%S %z",    # Sat, 21 Jun 2025 14:23:45 +0000
    # Other standards
    (_FORMAT, "eu_full"):           r"%d %B %Y",                    # 21 June 2025
    (_FORMAT, "log4j"):             r"%Y-%m-%d %H:%M:%S,%f",        # 2025-06-21 14:23:45,123456
    (_FORMAT, "ordinal_date"):      r"%Y-%j",                       # 2025-172
    (_FORMAT, "short_md"):          r"%b %d",                       # Jun 21
    (_FORMAT, "sql_ms"):            r"%Y-%m-%d %H:%M:%S.%f",        # 2025-06-21 14:23:45.123456
    (_FORMAT, "sql"):               r"%Y-%m-%d %H:%M:%S",           # 2025-06-21 14:23:45
    (_FORMAT, "time_12h"):          r"%I:%M %p",                    # 02:23 PM
    (_FORMAT, "us_full"):           r"%B %d, %Y",                   # June 21, 2025
    (_FORMAT, "week_date"):         r"%G-W%V-%u",                   # 2025-W25-6
}

_MATH_ENTRIES = {
    ("neg_inf",):     -math.inf,
    ("float", "max"): sys.float_info.max,
    ("float", "min"): sys.float_info.min,
    ("random",):      DynamicValue(poly_rnd),
    ("random100",):   DynamicValue(lambda: poly_rnd(1, 100))
}

def _get_machine_uuid() -> str:
    try:
        hostname = socket.gethostname()
        ip_addr = socket.gethostbyname(hostname)
    except (socket.gaierror, OSError):
        hostname = "unknown"
        ip_addr = "unknown"
    try:
        mac_int = uuid.getnode()
        mac_hex = f"{mac_int:012x}"
    except (ValueError, AttributeError):
        mac_hex = "unknown"
    machine_id_string = f"{hostname}-{ip_addr}-{mac_hex}"
    # Use DNS namespace
    namespace = uuid.NAMESPACE_DNS
    return str(uuid.uuid5(namespace, machine_id_string))

_UUID_PREFIX = 'uuid'

_UUID_ENTRIES = {
    ("machine",):     _get_machine_uuid(),
    ("random_time",): DynamicValue(lambda: str(uuid.uuid1())),
    ("random",):      DynamicValue(lambda: str(uuid.uuid4())),
}

_STREAM_FILE = "file"
_STREAM_ISATTY = "isatty"
_VGR_ENTRIES = {
    ("version",):                __version__,
    ("version_date",):           __version_date__,
    ("included",):               DynamicValue(get_is_included),
    ("includes",):               DynamicValue(get_includes),
    ("constants",):              DynamicValue(get_user_constants),
    ("stdin", _STREAM_FILE,):    DynamicValue(_REDIRECTOR.stdin().filename),
    ("stdin", _STREAM_ISATTY,):  DynamicValue(_REDIRECTOR.stdin().isatty),
    ("stdout", _STREAM_FILE,):   DynamicValue(_REDIRECTOR.stdout().filename),
    ("stdout", _STREAM_ISATTY,): DynamicValue(_REDIRECTOR.stdout().isatty),
    ("stderr", _STREAM_FILE,):   DynamicValue(_REDIRECTOR.stderr().filename),
    ("stderr", _STREAM_ISATTY,): DynamicValue(_REDIRECTOR.stderr().isatty),
    ("repl",):                   False, # may be changed later...
    ('max_frames',):             MAX_FRAMES,
    ('default_cache_size',):     DEFAULT_CACHE_SIZE,
    ('max_cache_size',):         MAX_CACHE_SIZE,
    ('caches',):                 DynamicValue(cache_keys)
}

def dd_init(dd: DataDictionary) -> None:
    # Clear the whole thing out and have it set its defaults
    dd.reset()
    # Set up app area
    dd.add_immutable_prefix(VGR_PREFIX)
    for path, value in _VGR_ENTRIES.items():
        dd.set_var(value, VGR_PREFIX, *path)
    dd.set_var(sys.executable, *EXEC_NAME_PATH)
    dd.set_var(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}',
               *EXEC_VER_PATH)
    # ... reg ex values
    dd.add_immutable_prefix(_RE_PREFIX)
    for flag in _RE_FLAGS:
        dd.set_var(getattr(re, flag), _RE_PREFIX, flag)
    _add_re_patterns(_RE_PREFIX, dd)
    # ... math and string values
    for mod in (math, string):
        name = mod.__name__
        dd.add_immutable_prefix(name)
        dd.set_var(_get_consts(mod), name)
    for path, value in _MATH_ENTRIES.items():
        dd.set_var(value, math.__name__, *path)
    # ... time values
    dd.add_immutable_prefix(_TIME_PREFIX)
    for path, value in _TIME_ENTRIES.items():
        dd.set_var(value, _TIME_PREFIX, *path)
    # ... UUID values
    dd.add_immutable_prefix(_UUID_PREFIX)
    for path, value in _UUID_ENTRIES.items():
        dd.set_var(value, _UUID_PREFIX, *path)
    # .. and OS and Sys
    for func, name in ((_get_os_consts, 'os'), (_get_sys_consts, 'sys')):
        dd.add_immutable_prefix(name)
        dd.set_var(func(), name)
    # env as a mutable dict
    dd.set_var(_get_environment(), 'env')
    dd.set_var(os.getenv('OFS', ' '), *OFS_PATH)
    dd.set_var(os.getenv('ORS', '\n'), *ORS_PATH)

def _get_os_consts() -> dict:
    rc = { key: value for key, value in _get_consts(os).items() if key in _OS_CONSTS }
    rc['login'] = DynamicValue(lambda: getpass.getuser() or 'unknown')
    rc['pid'] = DynamicValue(os.getpid)
    rc['cwd'] = DynamicValue(get_cwd)
    rc['system'] = platform.system()
    rc['node'] = platform.node()
    rc['hostname'] = socket.gethostname()
    return rc

def _get_sys_consts() -> dict:
    rc = { key: value for key, value in _get_consts(sys).items() if key in _SYS_CONSTS}
    return rc

def _get_environment() -> dict:
    rc = {
            name: value for name, value in os.environ.items()
                if not any(pattern.search(name) for pattern in _ENV_EXCLUDE)
        }
    for name, value in rc.items():
        if isinstance(value, str) and re.search(r'(_)?PATH$', name, re.IGNORECASE):
            rc[name] = value.split(os.pathsep)
    return rc

def _get_consts(source_mod) -> dict:
    return { key: value for key, value in vars(source_mod).items()
                if isinstance(value, (int, float, str, dict, list)) and not key.startswith("_")
            }

from .extn import VgrExtension
from .builtins import parse_json, compile_pattern
def _add_re_patterns(pfx: str, dd: DataDictionary) -> None:
    for item in parse_json(VgrExtension.read_resource_text(__package__, 're_patterns.json')).items():
        name = item[0]
        if name[0] != '#': # "commented out" in the key
            dd.set_var(compile_pattern(item[1]), _RE_PREFIX, "pattern", item[0])
