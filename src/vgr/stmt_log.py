"""
Implementation of Log statements
"""

import logging
from lark import Tree

from .app_exceptions import VgrRuntimeError
from .builtins import poly_format, bound_ops
from .dd_config import VGR_PREFIX
from .exec_context import ExecContext
from .log_config import LOG_LEVEL_MAP

_USER_LOGGER = logging.getLogger('vgr_user')

_LOG_FILE_PATH = (VGR_PREFIX, 'log', 'file')
_LOG_LEVEL_PATH = (VGR_PREFIX, 'log', 'level')
_DEFAULT_LOG_LEVEL = "Info"

_LOG_FUNCTION = {
    "Debug":    _USER_LOGGER.debug,
    "Info":     _USER_LOGGER.info,
    "Warn":     _USER_LOGGER.warning,
    "Warning":  _USER_LOGGER.warning,
    "Error":    _USER_LOGGER.error,
    "Critical": _USER_LOGGER.critical,
}

# Doc combined with execute_log
def execute_log_setlevel(ctx: ExecContext, statement: Tree) -> None:
    level_name = statement.children[0].data.title()
    level = LOG_LEVEL_MAP.get(level_name)
    if level is None:
        raise ValueError(f'Unsupported log level {level_name!r}')
    _set_log_level(ctx, level, level_name)

@bound_ops("Log")
def execute_log(ctx: ExecContext, statement: Tree) -> None:
    """
**Send a message to the log or set the logging level**

* Log *level*
* Log *level* *expression*[, *expression*]&hellip;
* Log Level *level*

The logging level must be one of `Debug`, `Info`, `Warn`, `Error`, or `Critical`.
Additionally, you can use `Log Level Off` to turn off all logging.
The current logging level is available in `vgr.log_level`.

The first expression is resolved to a string and used to format the other values in
a manner similar to `Printf`.

Formatting syntax is that used in `Printf` and `Format()`


```vgr
# Set the logging level
Log Level Info

# Log a simple informational message
Log Info "Application started"

# Log a formatted debug message with multiple values
Log Debug "User {} has {} unread messages", username, unread_count

# Log an error with a calculation and its result
Log Error "Unexpected value : {!r}", result
```

Also see `Print` and `Format()` for formatting details

"""
    log_level = statement.children[0].data.title()
    log_func = _LOG_FUNCTION.get(log_level)
    if log_func is None:
        raise VgrRuntimeError(statement.children[0], ValueError(f'Unsupported log level {log_level!r}'))
    value = ''
    if len(statement.children) > 1:
        format_string = ctx.eval_to_str(statement.children[1], 'Format string', True)
        value = poly_format(format_string, *list(ctx.eval_expr(expr) for expr in statement.children[2:]))
    log_func(value)

def init_app_log(ctx: ExecContext, logname: str) -> None:
    """Updates the DD with the name and sets the initial log level"""
    ctx.print_verbose('Log file is', logname)
    ctx.set_var(logname, *_LOG_FILE_PATH)
    _set_log_level(ctx, LOG_LEVEL_MAP.get(_DEFAULT_LOG_LEVEL), _DEFAULT_LOG_LEVEL)

def _set_log_level(ctx: ExecContext, level: int, level_name: str) -> None:
    """Updates the user's logger and the DD"""
    _USER_LOGGER.setLevel(level)
    ctx.set_var(level_name, *_LOG_LEVEL_PATH)
    ctx.print_verbose('Log Level set to', level_name)
