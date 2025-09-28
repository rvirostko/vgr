"""
Implementation of Log statements
"""

import logging
from lark import Tree

from .dd_config import LOG_LEVEL_PATH
from .exec_context import ExecContext
from .mathpak import poly_format, bound_ops

_USER_LOGGER = logging.getLogger('vgr_user')
# TODO need to get level, then convert to a string to set in DD

_LOG_FUNCTION = {
    "Debug":   _USER_LOGGER.debug,
    "Info":    _USER_LOGGER.info,
    "Warn":    _USER_LOGGER.warning,
    "Warning": _USER_LOGGER.warning,
    "Error":   _USER_LOGGER.error,
}

_LEVEL_MAP = {
    "Debug":   logging.DEBUG,
    "Info":    logging.INFO,
    "Warn":    logging.WARNING,
    "Warning": logging.WARNING,
    "Error":   logging.ERROR,
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

* Log _level_ [;]
* Log _level_ _expression_ [, _expression_]... [;]
* Log Level _level_ [;]

The logging level must be one of _Debug_, _Info_, _Warn_, or _Error_

The first expression is resolved to a string and used to format the other values.
Formatting syntax is that used in [Python's str.format()](https://docs.python.org/3/library/string.html#formatstrings)

See `Printf` for formatting details.

"""
    log_level = statement.children[0].data.title()
    log_func = _LOG_FUNCTION.get(log_level)
    if log_func is None:
        raise ValueError(f'Unsupported log level {log_level!r}')
    value = ''
    if len(statement.children) > 1:
        format_string = ctx.eval_to_str(statement.children[1], 'Format string', True)
        value = poly_format(format_string, *tuple(ctx.eval_expr(expr) for expr in statement.children[2:]))
    log_func(value)
