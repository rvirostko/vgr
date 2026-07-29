"""
Logging related config
"""

from datetime import datetime
import logging
import os
import re

from .builtins import verify_relative_path, expand_filename

_LEVEL_MAP = {
    'debug':    logging.DEBUG,
    'info':     logging.INFO,
    'warn':     logging.WARNING,
    'warning':  logging.WARNING,
    'error':    logging.ERROR,
    'critical': logging.CRITICAL,
    'off':      logging.CRITICAL + 1,
}

# remove leading/trailing carriage control characters
_CTRL_STRIP = re.compile(r'^[\r\n\x0b\x0c\x1c-\x1f]+|[\r\n\x0b\x0c\x1c-\x1f]+$')

class VgrLogFormatter(logging.Formatter):

    def format(self, record):
        if record.levelname == 'WARNING':
            record.levelname = 'WARN'
        elif record.levelname == 'CRITICAL':
            record.levelname = 'CRIT'
        if isinstance(record.msg, str):
            record.msg = _CTRL_STRIP.sub('', record.msg)
        return super().format(record)

    def formatTime(self, record, _=None): # datefmt ignored
        t = datetime.fromtimestamp(record.created)
        return t.strftime('%Y-%m-%dT%H:%M:%S.') + f'{int(record.msecs):03d}'

def init_logging(logfile: str, append: bool=True):
    if logfile is None:
        logfile = f'{datetime.now().strftime("%Y-%m-%d")} - vgr_log.txt'
    try:
        logfile_path = expand_filename(verify_relative_path(logfile))
    except OSError as e:
        raise ValueError(f'Log file {logfile} not relative to {os.getcwd()}') from e
    # Ensure parent directory exists
    log_dir = os.path.dirname(logfile_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    handler = logging.FileHandler(
                logfile,
                mode='a' if append else 'w',
                encoding='utf-8', errors='backslashreplace'
                )
    handler.setLevel(logging.NOTSET) # No filtering by the handler, only loggers
    handler.setFormatter(VgrLogFormatter('%(asctime)s %(levelname)-5s %(message)s'))
    logging.getLogger().handlers.clear()
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)

def set_logging_level(level_str: str):
    """
    Set the log level based on a user-provided string.
    Accepts: 'off', 'debug', 'info', 'warning', 'error', 'critical' (case-insensitive).
    """
    logging.getLogger().setLevel(_LEVEL_MAP.get(level_str.strip().lower(), logging.INFO))
