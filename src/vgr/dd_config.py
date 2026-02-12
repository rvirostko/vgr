
"""
Utility routines for working with the global Data Dictionary
"""

from datetime import datetime
import getpass
import math
import os
import platform
import random
import re
import socket
import string
import sys
import time
import uuid

from .data_dict import DataDictionary, DynamicValue, MAX_FRAMES
from .exec_context import ExecContext
from . import __version__, __version_date__

VGR_PREFIX = 'vgr'
INCLUDED_PATH = (VGR_PREFIX, 'included')
VER_PATH = (VGR_PREFIX, 'version')
VER_DATE_PATH = (VGR_PREFIX, 'version_date')
LOG_LEVEL_PATH = (VGR_PREFIX, 'log_level')
EXEC_NAME_PATH = (VGR_PREFIX, 'python', 'executable')
EXEC_VER_PATH = (VGR_PREFIX, 'python', 'version')
MAX_FRAMES_PATH = (VGR_PREFIX, 'max_frames')

_TIME_PREFIX = 'time'

_USER_ARGS = 'args'

OFS_PATH = ('env', 'OFS')
ORS_PATH = ('env', 'ORS')

_ENV_EXCLUDE = tuple(re.compile(pattern, re.IGNORECASE) for pattern in ('^VSCODE', '^_$', '^(OLD)?PWD$', '^__CF'))
_OS_CONSTS = ( 'defpath',  'devnull', 'extsep', 'linesep', 'name', 'pardir', 'pathsep', 'sep' )
_SYS_CONSTS = ( 'api_version', 'builtin_module_names', 'byteorder', 'exec_prefix', 'executable', 'maxsize',
    'maxunicode', 'platform', 'platlibdir', 'prefix', 'pycache_prefix', 'version',)

_RE_PREFIX = 're'
_RE_FLAGS = ('ASCII', 'IGNORECASE', 'LOCALE', 'MULTILINE', 'DOTALL', 'UNICODE', 'VERBOSE')

_COMPACT = "compact"
_FORMAT = "format"
_TODAY = "today"
_TIME_ENTRIES = {
    ("dst",):                       DynamicValue(lambda: bool(datetime.now().astimezone().dst())),
    ("now",):                       DynamicValue(lambda: int(time.time())), # Unix Epoch time
    ("sec_per_day",):               60 * 60 * 24,
    ("sec_per_hr",):                60 * 60,
    ("tz_name", ):                  DynamicValue(lambda: datetime.now().astimezone().tzname()),
    ("utc_offset",):                DynamicValue(lambda: int(datetime.now().astimezone().utcoffset().total_seconds())),
    # "today" is a composite object
    (_TODAY, "day"):                DynamicValue(lambda: datetime.now().day),                 # 21
    (_TODAY, "dow_abbr"):           DynamicValue(lambda: datetime.now().strftime("%a")),      # Sat
    (_TODAY, "dow"):                DynamicValue(lambda: datetime.now().strftime("%A")),      # Saturday
    (_TODAY, "hour"):               DynamicValue(lambda: datetime.now().hour),                # 14
    (_TODAY, "minute"):             DynamicValue(lambda: datetime.now().minute),              # 23
    (_TODAY, "month"):              DynamicValue(lambda: datetime.now().month),               # 6
    (_TODAY, "second"):             DynamicValue(lambda: datetime.now().second),              # 45
    (_TODAY, "weekday"):            DynamicValue(lambda: datetime.now().weekday()),           # 5 (Monday=0)
    (_TODAY, "yday"):               DynamicValue(lambda: datetime.now().timetuple().tm_yday), # 172
    (_TODAY, "year"):               DynamicValue(lambda: datetime.now().year),                # 2025
    # Formats for timestamps et al
    (_FORMAT, "dmy"):               "%d-%m-%Y",                  # 21-06-2025
    (_FORMAT, "dt"):                "%Y-%m-%d %H:%M:%S",         # 2025-06-21 14:23:45
    (_FORMAT, "hm"):                "%H:%M",                     # 14:23
    (_FORMAT, "hms"):               "%H:%M:%S",                  # 14:23:45
    (_FORMAT, "mdy"):               "%m/%d/%Y",                  # 06/21/2025
    (_FORMAT, "ymd"):               "%Y-%m-%d",                  # 2025-06-21
    # Compact variants
    (_FORMAT, _COMPACT, "dmy"):     "%d%m%Y",                    # 21062025
    (_FORMAT, _COMPACT, "dt"):      "%Y%m%d_%H%M%S",             # 20250621_142345
    (_FORMAT, _COMPACT, "hm"):      "%H%M",                      # 1423
    (_FORMAT, _COMPACT, "hms"):     "%H%M%S",                    # 142345
    (_FORMAT, _COMPACT, "mdy"):     "%m%d%Y",                    # 06212025
    (_FORMAT, _COMPACT, "ymd"):     "%Y%m%d",                    # 20250621
    # Standards
    (_FORMAT, "iso8601_ms_offset"): "%Y-%m-%dT%H:%M:%S.%f%z",    # 2025-06-21T14:23:45.123456+0000
    (_FORMAT, "iso8601_offset"):    "%Y-%m-%dT%H:%M:%S%z",       # 2025-06-21T14:23:45+0000
    (_FORMAT, "iso8601_z"):         "%Y-%m-%dT%H:%M:%SZ",        # 2025-06-21T14:23:45Z
    (_FORMAT, "iso8601"):           "%Y-%m-%dT%H:%M:%S",         # 2025-06-21T14:23:45
    (_FORMAT, "rfc1123"):           "%a, %d %b %Y %H:%M:%S GMT", # Sat, 21 Jun 2025 14:23:45 GMT
    (_FORMAT, "rfc2822"):           "%a, %d %b %Y %H:%M:%S %z",  # Sat, 21 Jun 2025 14:23:45 +0000
    # Other standards
    (_FORMAT, "eu_full"):           "%d %B %Y",                  # 21 June 2025
    (_FORMAT, "log4j"):             "%Y-%m-%d %H:%M:%S,%f",      # 2025-06-21 14:23:45,123456
    (_FORMAT, "ordinal_date"):      "%Y-%j",                     # 2025-172
    (_FORMAT, "short_md"):          "%b %d",                     # Jun 21
    (_FORMAT, "sql_ms"):            "%Y-%m-%d %H:%M:%S.%f",      # 2025-06-21 14:23:45.123456
    (_FORMAT, "sql"):               "%Y-%m-%d %H:%M:%S",         # 2025-06-21 14:23:45
    (_FORMAT, "time_12h"):          "%I:%M %p",                  # 02:23 PM
    (_FORMAT, "us_full"):           "%B %d, %Y",                 # June 21, 2025
    (_FORMAT, "week_date"):         "%G-W%V-%u",                 # 2025-W25-6
}

_MATH_ENTRIES = {
    ("neg_inf",):     -math.inf,
    ("float", "max"): sys.float_info.max,
    ("float", "min"): sys.float_info.min,
    ("random",):      DynamicValue(random.random),
    ("random100",):   DynamicValue(lambda: random.randrange(1, 100))
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

# The files that have been "@Include"d rather than "Source"d
# NB: Files can look at INCLUDED_PATH to see if they
#     are being included vs sourced
_INCLUDES_PATH = (VGR_PREFIX, 'includes')
_INCLUDED_FILES = []

def dd_init(dd: DataDictionary) -> None:
    # Clear the whole thing out and have it set its defaults
    dd.reset()
    # Set up app area
    dd.add_immutable_prefix(VGR_PREFIX)
    dd.set_var(False, *INCLUDED_PATH)
    dd.set_var(DynamicValue(lambda: _INCLUDED_FILES), *_INCLUDES_PATH)
    dd.set_var(__version__, *VER_PATH)
    dd.set_var(__version_date__, *VER_DATE_PATH)
    dd.set_var(sys.executable, *EXEC_NAME_PATH)
    dd.set_var(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}',
               *EXEC_VER_PATH)
    dd.set_var(MAX_FRAMES, *MAX_FRAMES_PATH)
    # ... reg ex values
    dd.add_immutable_prefix(_RE_PREFIX)
    for flag in _RE_FLAGS:
        dd.set_var(getattr(re, flag), _RE_PREFIX, flag)
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

def set_user_args(ctx: ExecContext, data: list) -> None:
    assert data is None or isinstance(data, list)
    ctx.set_var(data or [], _USER_ARGS)

def get_user_args(ctx: ExecContext) -> list:
    return ctx.get_var(_USER_ARGS)

def clear_includes() -> None:
    _INCLUDED_FILES.clear()

def add_include(path) -> None:
    _INCLUDED_FILES.append(str(path))

def is_included(path) -> bool:
    return str(path) in _INCLUDED_FILES

def _get_os_consts() -> dict:
    rc = { key: value for key, value in _get_consts(os).items() if key in _OS_CONSTS }
    rc['login'] = DynamicValue(lambda: getpass.getuser() or 'unknown')
    rc['pid'] = DynamicValue(os.getpid)
    rc['cwd'] = DynamicValue(os.getcwd)
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
