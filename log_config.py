"""
Logging related config
"""

import logging
import datetime

_DEFAULT_LOG_FILE = 'vgr_log.txt'

_LEVEL_MAP = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}

class MillisecondFormatter(logging.Formatter):
    def formatTime(self, record, _=None): # datefmt ignored
        t = datetime.datetime.fromtimestamp(record.created)
        return t.strftime('%Y-%m-%dT%H:%M:%S.') + f'{int(record.msecs):03d}'

def init_logging(logfile: str):
    handler = logging.FileHandler(logfile or _DEFAULT_LOG_FILE)
    handler.setLevel(logging.NOTSET) # No filtering by the handler, only loggers
    handler.setFormatter(MillisecondFormatter('%(asctime)s %(levelname)-5s %(message)s'))
    logging.getLogger().handlers.clear()
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)

def set_logging_level(level_str: str):
    """
    Set the log level based on a user-provided string.
    Accepts: 'debug', 'info', 'warning', 'error', 'critical' (case-insensitive).
    """
    logging.getLogger().setLevel(_LEVEL_MAP.get(level_str.strip().lower(), logging.INFO))
