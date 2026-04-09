"""
Winows console functions
"""
import logging

_LOG = logging.getLogger(__name__)

_FIRST_ERR = True

def win_get_cursor_pos() -> list:
    try:
        from blessed import Terminal
        cursor_y_pos, cursor_x_pos = Terminal().get_location()
        return [cursor_y_pos + 1, cursor_x_pos + 1]
    except Exception as e:
        global _FIRST_ERR
        if _FIRST_ERR:
            _LOG.error("Can't load blessed - %s", e)
            _FIRST_ERR = False
        return None
