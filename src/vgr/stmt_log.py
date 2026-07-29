"""
Implementation of Log statements
"""

import logging
from lark import Tree

from .builtins import poly_format, bound_ops
from .dd_config import LOG_LEVEL_PATH
from .exec_context import ExecContext

_USER_LOGGER = logging.getLogger('vgr_user')

_LOG_FUNCTION = {
    "Debug":    _USER_LOGGER.debug,
    "Info":     _USER_LOGGER.info,
    "Warn":     _USER_LOGGER.warning,
    "Warning":  _USER_LOGGER.warning,
    "Error":    _USER_LOGGER.error,
    "Critical": _USER_LOGGER.critical,
}

_LEVEL_MAP = {
    "Debug":    logging.DEBUG,
    "Info":     logging.INFO,
    "Warn":     logging.WARNING,
    "Warning":  logging.WARNING,
    "Error":    logging.ERROR,
    "Critical": logging.CRITICAL,
    "Off":      logging.CRITICAL + 1,
}

# Doc combined with execute_log
def execute_log_setlevel(ctx: ExecContext, statement: Tree) -> None:
    log_level = statement.children[0].data.title()
    level = _LEVEL_MAP.get(log_level)
    if level is None:
        raise ValueError(f'Unsupported log level {log_level!r}')
    _USER_LOGGER.setLevel(level)
    ctx.set_var(log_level, *LOG_LEVEL_PATH)
    ctx.print_verbose('Log Level set to', log_level)

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
    from .app_exceptions import VgrRuntimeError
    log_level = statement.children[0].data.title()
    log_func = _LOG_FUNCTION.get(log_level)
    if log_func is None:
        raise VgrRuntimeError(statement.children[0], ValueError(f'Unsupported log level {log_level!r}'))
    value = ''
    if len(statement.children) > 1:
        format_string = ctx.eval_to_str(statement.children[1], 'Format string', True)
        value = poly_format(format_string, *list(ctx.eval_expr(expr) for expr in statement.children[2:]))
    log_func(value)
