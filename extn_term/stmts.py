"""
Term(inal) Statements
"""

from typing import Any
import base64
import os
import re
import shutil
import sys
import termios
import tty

from lark import Tree

from app_exceptions import VgrRuntimeError
from evaluate import eval_expr
from data_dict import DataDictionary
from redir import stdout

class TermConsts:
    """
    Reference material:
        https://vt100.net/docs/vt220-rm/contents.html
        https://www.xfree86.org/current/ctlseqs.html
        https://invisible-island.net/xterm/ctlseqs/ctlseqs.html
    """

    BSTYLES = ("Empty", "ASCII", "Single", "Double", "SingleDouble", "DoubleSingle", "Brackets", "Parens")

    # Box style constants
    BSTYLE_BLANK = 0
    BSTYLE_ASCII = 1
    BSTYLE_SINGLE = 2
    BSTYLE_DOUBLE = 3
    BSTYLE_SINGLEDOUBLE = 4
    BSTYLE_DOUBLESINGLE = 5
    BSTYLE_BRACKETS = 6
    BSTYLE_PARENS = 7

    # Box parts
    I_HBAR  = 0
    I_VBAR  = 1
    I_TL    = 2
    I_TR    = 3
    I_BL    = 4
    I_BR    = 5
    I_LT    = 6  # Left tee
    I_RT    = 7  # Right tee
    I_TT    = 8  # Top tee
    I_BT    = 9  # Bottom tee
    I_CC    = 10  # Center cross
    I_RVBAR = 11 # Alternate VBAR for righthand side

    SP      = ' ' # Space char

    # Graphics names:
    #  TL     HBAR    TT    HBAR     TR
    #  VBAR          VBAR          VBAR
    #  LT     HBAR    CC    HBAR     RT
    #  VBAR          VBAR          VBAR
    #  BL     HBAR    BT    HBAR     BL
    #
    # Prefixes:
    # <none> : single line
    # D_ : double line
    # SD_ : single horz, double vert
    # DS_ : double horz, single vert
    # BR_ : brackets
    # PR_ : parens

    # Single line graphics
    HBAR = '─'
    VBAR = '│'
    TL   = '┌'
    TR   = '┐'
    BL   = '└'
    BR   = '┘'
    LT   = '├'  # Left tee
    RT   = '┤'  # Right tee
    TT   = '┬'  # Top tee
    BT   = '┴'  # Bottom tee
    CC   = '┼'  # Center cross

    # Double line graphics
    D_HBAR = '═'
    D_VBAR = '║'
    D_TL =   '╔'
    D_TR =   '╗'
    D_BL =   '╚'
    D_BR =   '╝'
    D_LT =   '╠'
    D_RT =   '╣'
    D_TT =   '╦'
    D_BT =   '╩'
    D_CC =   '╬'

    # Single horz, double vert
    SD_HBAR = '─'
    SD_VBAR = '║'
    SD_TL   = '╓'
    SD_TR   = '╖'
    SD_BL   = '╙'
    SD_BR   = '╜'
    SD_LT   = '╟'
    SD_RT   = '╢'
    SD_TT   = '╥'
    SD_BT   = '╨'
    SD_CC   = '╫'

    # Double horz, single vert
    DS_HBAR = '═'
    DS_VBAR = '│'
    DS_TL   = '╒'
    DS_TR   = '╕'
    DS_BL   = '╘'
    DS_BR   = '╛'
    DS_LT   = '╞'
    DS_RT   = '╡'
    DS_TT   = '╤'
    DS_BT   = '╧'
    DS_CC   = '╪'


    BOX_BLANK = (SP, SP, SP, SP, SP, SP, SP, SP, SP, SP, SP, SP)
    BOX_ASCII = ('-', '|', '+', '+', '+', '+', '+', '+', '+', '+', '+', '|')
    BOX_SINGLE = (HBAR, VBAR, TL, TR, BL, BR, LT, RT, TT, BT, CC, VBAR)
    BOX_DOUBLE = (D_HBAR, D_VBAR, D_TL, D_TR, D_BL, D_BR, D_LT, D_RT, D_TT, D_BT, D_CC, D_VBAR)
    BOX_SINGLEDOUBLE = (SD_HBAR, SD_VBAR, SD_TL, SD_TR, SD_BL, SD_BR, SD_LT, SD_RT, SD_TT, SD_BT, SD_CC, SD_VBAR)
    BOX_DOUBLESINGLE = (DS_HBAR, DS_VBAR, DS_TL, DS_TR, DS_BL, DS_BR, DS_LT, DS_RT, DS_TT, DS_BT, DS_CC, DS_VBAR)
    BOX_BRACKETS = (SP, '⎢', '⎡', '⎤', '⎣', '⎦', SP, SP, SP, SP, SP, '⎥' ) #VBARS are (U+23A2) and (U+23A5)
    BOX_PARENS = (SP, '⎜', '⎛', '⎞', '⎝', '⎠', SP, SP, SP, SP, SP, '⎟' ) # VBARs are (U+239C) and (U+239F)
    # NB: See https://unicodeplus.com/category/Sm/4 for details on multi part characters

    BOXES = (BOX_BLANK, BOX_ASCII, BOX_SINGLE, BOX_DOUBLE, BOX_SINGLEDOUBLE, BOX_DOUBLESINGLE, BOX_BRACKETS, BOX_PARENS)

    SOS = "\x1bX" # Start of String (SOS  is 0x98)
    CSI = "\x1b[" # Control Sequence Introducer (CSI  is 0x9b)
    ST = "\x1b\\" # String Terminator (ST  is 0x9c)
    OSC = "\x1b]" # Operating System Command (OSC  is 0x9d)

    # "Select Graphic Rendition"
    SGR_RESET =          "\x1b[0m"
    SGR_BOLD_ON =        "\x1b[1m"
    SGR_BOLD_OFF =       "\x1b[22m"
    SGR_DIM_ON =         "\x1b[2m"
    SGR_DIM_OFF =        "\x1b[22m"
    SGR_ITALIC_ON =      "\x1b[3m"
    SGR_ITALIC_OFF =     "\x1b[23m"
    SGR_UNDERLINE_ON =   "\x1b[4m"
    SGR_UNDERLINE_OFF =  "\x1b[24m"
    SGR_BLINK_ON =       "\x1b[5m"
    SGR_BLINK_OFF =      "\x1b[25m"
    SGR_REVERSE_ON =     "\x1b[7m"
    SGR_REVERSE_OFF =    "\x1b[27m"
    SGR_HIDDEN_ON =      "\x1b[8m"
    SGR_HIDDEN_OFF =     "\x1b[28m"
    SGR_STRIKETHRU_ON =  "\x1b[9m"
    SGR_STRIKETHRU_OFF = "\x1b[29m"
    SGR_RESET_FG =       "\x1b[39m"
    SGR_RESET_BG =       "\x1b[49m"
    SGR_FG =             "\x1b[38;5;{}m"
    SGR_BG =             "\x1b[48;5;{}m"

    # Double width/height
    DECDHL_TOP =     "\x1b#3" # Double height, top
    DECDHL_BOT =     "\x1b#4" # Double height, bottom
    DECSWL =         "\x1b#5" # Single width, single height
    DECDWL =         "\x1b#6" # Double width line

    # Scroll Mode
    DECSCLM_SET =    "\x1b[?3h" # Smooth scroll
    DECSCLM_RESET =  "\x1b[?3l"

    # Insert/Replace Mode
    IRM_SET =         "\x1b[4h" # Insert
    IRM_RESET =       "\x1b[4l" # Replace

    # Screen Mode
    DECSCNM_SET =    "\x1b[?5h" # Reverse video
    DECSCNM_RESET =  "\x1b[?5l"

    # Origin Mode
    DECOM_SET =      "\x1b[?6h" # Home is in scroll region
    DECOM_RESET =    "\x1b[?6l"

    # Auto wrap
    DECAWM_SET =     "\x1b[?7h"
    DECAWM_RESET =   "\x1b[?7l" # Don't wrap at right margin

    # Cursor
    CUP =            "\x1b[{};{}H" # Cursor position
    CUP_HOME =       "\x1b[H" # Cursor to 0,0
    DECTCEM_SET =    "\x1b[?25h" # Cursor on
    DECTCEM_RESET =  "\x1b[?25l" # Cursor hidden
    CUU =            "\x1b[{}A" # Cursor Up
    CUD =            "\x1b[{}B" # Cursor Down
    CUF =            "\x1b[{}C" # Cursor Forward
    CUB =            "\x1b[{}D" # Cursor Backwards
    IND =            "\x1bD" # Cursor Down, same column
    RI =             "\x1bM" # Cursor Up, same column
    NEL =            "\x1bE" # Next line
    DECSC =          "\x1b7" # DEC save cursor (and other values)
    DECRC =          "\x1b8" # DEC restore cursor (see above)

    # Tabs
    HTS =            "\x1bH" # Set tab at current column
    TBC =            "\x1b[g" # Clear at current column
    TBC_ALL =        "\x1b[3g" # Clear all

    # Editing
    IL =             "\x1b[{}L" # Insert line
    DL =             "\x1b[{}M" # Delete line
    ICH =            "\x1b[{}@" # Insert characters
    DCH =            "\x1b[{}P" # Delete characters
    ECH =            "\x1b[{}X" # Erase characters
    EL =             "\x1b[{}K" # Erase in line
    EL_EOL =         "\x1b[K" # To end of line
    EL_BOL =         "\x1b[1K" # To begining of line
    EL_ALL =         "\x1b[2K" # The entire line

    ED_FWD =         "\x1b[0J" # Cursor to end of display
    ED_BCK =         "\x1b[1J" # Start of display to cursor
    ED_ALL =         "\x1b[2J" # Erase entire display

    # Scrolling margins
    SECSTBM =        "\x1b[{};{}r" # top and bottom lines

    # Reports
    DA_PRIMARY =     "\x1b[c" # Reply- CSI ? 62; [code;]* c
    DA_SECONDARY =   "\x1b[>c" # Reply- CSI > 1; Pv; Po c
    DSR_STATUS =     "\x1b[5n" # Reply- CSI [0|3] n
    DSR_CURSOR =     "\x1b[6n" # Reply- CSI Pv; Ph R

    # Resets and Adjustments
    DECSTR =         "\x1b[!p" # Soft reset
    RIS =            "\x1bc" # Hard Terminal Reset
    DECALN =         "\x1b#8" # Alignment test (fill with 'E')
    S7C1T =          "\x1b[?42l"  # Use 7-bit C1 controls (reset 42)
    S8C1T =          "\x1b[?42h"  # Use 8-bit C1 controls (set 42)

    # ANSI X3.64 / ECMA-48 / Xterm
    REP = "\x1b[{}b" # Repeat last character N times (only works with ASCII?)
    HPA = "\x1b[{}`"  # Character Position Absolute [column]
    VPA = "\x1b[{}d"  # Line Position Absolute [row]
    DEICONIFY = "\x1b[1t" # De-iconify window
    RAISE_WINDOW = "\x1b[5t" # Raise window to the front of the stacking order
    ICON_NAME = OSC + "1;{}" + ST # Change Icon Name
    WINDOW_TITLE = OSC + "2;{}" + ST # Change Window Title

    # "Pretty" names for the colors
    # Index is the color number
    COLOR_NAMES = [
        "Black",
        "Red",
        "Green",
        "Yellow",
        "Blue",
        "Magenta",
        "Cyan",
        "White",
        "Gray",
        "Bright Red",
        "Bright Green",
        "Bright Yellow",
        "Bright Blue",
        "Bright Magenta",
        "Bright Cyan",
        "Bright White"
    ]

_COLOR_NAME_MAP = { }
_DUMB_TERM = os.getenv("TERM", "").lower() == "dumb"
_NO_COLOR = bool(os.getenv("NO_COLOR"))

def add_dd_constants(dd: DataDictionary, prefix: str) -> None:
    for name, value in vars(TermConsts).items():
        if not name.startswith("__"): dd.set_var(value, prefix, name.lower())
    for val, name in enumerate(TermConsts.COLOR_NAMES):
        _COLOR_NAME_MAP[_canonical_color_name(name)] = val
    # Add numbered grays: 232 to 255
    for i in range(1, 25): _COLOR_NAME_MAP[f'gray{i}'] = 231 + i
    dd.set_var(_DUMB_TERM, prefix, 'dumb_term')
    dd.set_var(_NO_COLOR, prefix, 'no_color')

def _print(*args: Any) -> None:
    if not _DUMB_TERM:
        out = stdout()
        if out.isatty():
            print(*args, file=out, sep='', end='', flush=True)

def _term_cursor_moveto(dd: DataDictionary, cmd: Tree) -> None:
    # TODO scarf common func from elsewhere
    line = eval_expr(dd, cmd.children[0])
    col = eval_expr(dd, cmd.children[1])
    _print(TermConsts.CUP.format(line, col))

def _resolve_ansi_color(val: Any) -> int:
    if isinstance(val, (int, float)):
        val = round(val)
        return val if 0 <= val <= 255 else None
    if not isinstance(val, str): return None
    val = val.strip()
    try:
        val = round(float(val))
        return val if 0 <= val <= 255 else None
    except ValueError:
        pass
    return _COLOR_NAME_MAP.get(_canonical_color_name(val))

def _resolve_box_style(val: Any) -> int:
    if val is None: return TermConsts.BSTYLE_ASCII
    if isinstance(val, (int, float)):
        return max(0, min(len(TermConsts.BSTYLES) - 1, int(val)))
    if isinstance(val, str):
        s = re.sub(r'[^a-z0-9]', '', val.casefold()).removeprefix('bstyle')
        if s in ('empty', 'none', 'blank', str(TermConsts.BSTYLE_BLANK)):
            return TermConsts.BSTYLE_BLANK
        if s in ('a', 'ascii', str(TermConsts.BSTYLE_ASCII)):
            return TermConsts.BSTYLE_ASCII
        if s in ('', 's', 'single', str(TermConsts.BSTYLE_SINGLE)):
            return TermConsts.BSTYLE_SINGLE
        if s in ('d', 'double', str(TermConsts.BSTYLE_DOUBLE)):
            return TermConsts.BSTYLE_DOUBLE
        if s in ('sd', 'singledouble', str(TermConsts.BSTYLE_DOUBLE)):
            return TermConsts.BSTYLE_SINGLEDOUBLE
        if s in ('ds', 'doublesingle', str(TermConsts.BSTYLE_DOUBLESINGLE)):
            return TermConsts.BSTYLE_DOUBLESINGLE
        if s in ('br', 'bracket', 'brackets', str(TermConsts.BSTYLE_BRACKETS)):
            return TermConsts.BSTYLE_BRACKETS
        if s in ('pr', 'paren', 'parens', str(TermConsts.BSTYLE_PARENS)):
            return TermConsts.BSTYLE_PARENS
    return TermConsts.BSTYLE_BLANK

def _canonical_color_name(val: str) -> str:
    return re.sub(r'[^a-z0-9]', '', val.casefold())

# Everything except colors
_SGR_ALL_OFF = (
    TermConsts.SGR_BOLD_OFF, TermConsts.SGR_DIM_OFF, TermConsts.SGR_BLINK_OFF,
    TermConsts.SGR_ITALIC_OFF, TermConsts.SGR_UNDERLINE_OFF, TermConsts.SGR_REVERSE_OFF,
    TermConsts.SGR_HIDDEN_OFF, TermConsts.SGR_STRIKETHRU_OFF
)

def _term_sgr_style(dd: DataDictionary, cmd: Tree) -> None:
    reqs = str(eval_expr(dd, cmd.children[0])).strip() if len(cmd.children) > 0 else ''
    if not reqs: return
    _print(*_SGR_ALL_OFF)
    for s in re.split(r'[^a-z0-9_+-]', reqs.casefold()):
        if s.isdigit():
            c = _resolve_ansi_color(s)
            if c and not _NO_COLOR: _print(TermConsts.SGR_FG.format(c))
            continue
        if s in ("reset",):
            # This resets FG color and "wide"...
            _print(TermConsts.SGR_RESET_FG, TermConsts.DECSWL)
            # INTENTIONAL FALL-THRU
        if s in ("reset", "normal", "default"):
            # This resets everything else...
            _print(*_SGR_ALL_OFF)
            continue
        # prefix of '+' means on, but that's the default of using the world
        s = s.removeprefix('+')
        # prefix of '-' means off
        # If you combine them your command is likely to be ignored
        negate = s[0] == '-'
        s = s.removeprefix('-')
        if s in ("bold", ):
            _print(TermConsts.SGR_BOLD_OFF if negate else TermConsts.SGR_BOLD_ON)
            continue
        if s in ("dim",):
            _print(TermConsts.SGR_DIM_OFF if negate else TermConsts.SGR_DIM_ON)
            continue
        if s in ("blink",):
            _print(TermConsts.SGR_BLINK_OFF if negate else TermConsts.SGR_BLINK_ON)
            continue
        if s in ("italic", "italics"):
            _print(TermConsts.SGR_ITALIC_OFF if negate else TermConsts.SGR_ITALIC_ON)
            continue
        if s in ("underline", "ul"):
            _print(TermConsts.SGR_UNDERLINE_OFF if negate else TermConsts.SGR_UNDERLINE_ON)
            continue
        if s in ("reverse", "rev"):
            _print(TermConsts.SGR_REVERSE_OFF if negate else TermConsts.SGR_REVERSE_ON)
            continue
        if s in ("hidden", "hide"):
            _print(TermConsts.SGR_HIDDEN_OFF if negate else TermConsts.SGR_HIDDEN_ON)
            continue
        if s in ("strikethrough", "strikethru", "strikeout"):
            _print(TermConsts.SGR_STRIKETHRU_OFF if negate else TermConsts.SGR_STRIKETHRU_ON)
            continue
        if s in ("double", "wide"):
            _print(TermConsts.DECSWL if negate else TermConsts.DECDWL)
            continue
        if s in ("single",):
            _print(TermConsts.DECDWL if negate else TermConsts.DECSWL)
            continue
        # Failed all the keyword tests; see if it is a named
        # color for the foreground
        c = _resolve_ansi_color(s)
        if c and not _NO_COLOR: _print(TermConsts.SGR_FG.format(c))
        # errors ignored

def _term_set_clipboard(dd: DataDictionary, cmd: Tree) -> None:
    text = str(eval_expr(dd, cmd.children[0])).strip() if len(cmd.children) > 0 else ''
    try:
        import pyperclip
        pyperclip.copy(text)
    except ImportError:
        # Does not work with many terminals
        _print('\x1b]52;c;',
            base64.b64encode(text.encode('utf-8')).decode('ascii') if text else '',
            '\a')

_CUU_1 = TermConsts.CUU.format('')
_CUD_1 = TermConsts.CUD.format('')
_CUB_1 = TermConsts.CUB.format('')

def _term_draw_hline(dd: DataDictionary, cmd: Tree) -> None:
    style = TermConsts.BSTYLE_SINGLE
    arg_ind = 0
    args = _eval_all(dd, cmd)
    if len(args) > 1:
        style = _resolve_box_style(args[0])
        arg_ind = 1
    _draw_hline(style, max(0, int(args[arg_ind])))

def _draw_hline(style: int, cols: int) -> None:
    if cols:
        _print(TermConsts.BOXES[style][TermConsts.I_HBAR] * cols)

def _term_draw_vline(dd: DataDictionary, cmd: Tree) -> None:
    style = TermConsts.BSTYLE_SINGLE
    arg_ind = 0
    args = _eval_all(dd, cmd)
    if len(args) > 1:
        style = _resolve_box_style(args[0])
        arg_ind = 1
    _draw_vline(style, max(0, int(args[arg_ind])))

def _draw_vline(style: int, lines: int) -> None:
    if lines:
        for _ in range(lines):
            _print(TermConsts.BOXES[style][TermConsts.I_VBAR], _CUB_1, _CUD_1)

def _eval_all(dd: DataDictionary, cmd: Tree) -> list:
    return [eval_expr(dd, child) for child in cmd.children]

def _term_draw_box(dd: DataDictionary, cmd: Tree) -> None:
    if _DUMB_TERM: return
    style = TermConsts.BSTYLE_SINGLE
    arg_ind = 0
    args = _eval_all(dd, cmd)
    if len(args) > 2:
        style = _resolve_box_style(args[arg_ind])
        arg_ind += 1
    height = int(args[arg_ind])
    width = int(args[arg_ind + 1])
    cursor_row, cursor_col = _get_cursor_pos()
    row = cursor_row
    col = cursor_col
    screen_cols, screen_rows = shutil.get_terminal_size()
    # Vertical adjustment
    if height >= 0:
        height = min(height, screen_rows - cursor_row + 1)
    else:
        height = min(-height, cursor_row)
        row = cursor_row - height + 1
    # Horizontal adjustment
    if width >= 0:
        width = min(width, screen_cols - cursor_col + 1)
    else:
        width = min(-width, cursor_col)
        col = cursor_col - width + 1
    if height == 0 or width == 0: return
    # Horizontal line
    if height == 1:
        _draw_hline(style, width)
        return
    # Vertical line
    if width == 1:
        _draw_vline(style, height)
        return
    # Box is at least 2x2
    inner_width = width - 2
    hbar = TermConsts.BOXES[style][TermConsts.I_HBAR] * inner_width if inner_width else ''
    # Box top
    _print(TermConsts.CUP.format(row, col),
           TermConsts.BOXES[style][TermConsts.I_TL],
           hbar,
           TermConsts.BOXES[style][TermConsts.I_TR])
    # Left and right sides
    row += 1
    if height > 2:
        inside = ''
        if inner_width:
            inside = ' '
            if inner_width > 1: inside += TermConsts.REP.format(inner_width - 1)
        for _ in range(height - 2):
            _print(TermConsts.CUP.format(row, col),
                   TermConsts.BOXES[style][TermConsts.I_VBAR],
                   inside,
                   TermConsts.BOXES[style][TermConsts.I_RVBAR])
            row += 1
    # And the bottom
    _print(TermConsts.CUP.format(row, col),
           TermConsts.BOXES[style][TermConsts.I_BL],
           hbar,
           TermConsts.BOXES[style][TermConsts.I_BR])
    # and move to within the box
    _print(TermConsts.CUP.format(row - height + 2, col + 1))

def _term_dh_print(dd: DataDictionary, cmd: Tree) -> None:
    s = eval_expr(dd, cmd.children[0])
    if s is not None:
        _print(TermConsts.DECDHL_TOP, _CUD_1, TermConsts.DECDHL_BOT, _CUU_1)
        for c in str(s):
            _print(c, _CUB_1, _CUD_1, c, _CUU_1)

def _term_scroll_region(dd: DataDictionary, cmd: Tree) -> None:
    top = int(eval_expr(dd, cmd.children[0]))
    bottom = int(eval_expr(dd, cmd.children[1]))
    _print(TermConsts.SECSTBM.format(top, bottom))

def _term_icon_name(dd: DataDictionary, cmd: Tree) -> None:
    s = eval_expr(dd, cmd.children[0])
    s = '' if s is None else str(s)
    _print(TermConsts.ICON_NAME.format(s))

def _term_window_title(dd: DataDictionary, cmd: Tree) -> None:
    s = eval_expr(dd, cmd.children[0])
    s = '' if s is None else str(s)
    _print(TermConsts.WINDOW_TITLE.format(s))

def _term_color(dd: DataDictionary, cmd: Tree, reset_seq: str, color_fmt: str) -> None:
    if _NO_COLOR:
        return
    if len(cmd.children) == 0:
        _print(reset_seq)
    else:
        value = eval_expr(dd, cmd.children[0])
        code = _resolve_ansi_color(value)
        _print(reset_seq if code is None else color_fmt.format(code))

def _term_toggle(dd: DataDictionary, cmd: Tree, on_seq: str, off_seq: str) -> None:
    on = True if len(cmd.children) == 0 else bool(eval_expr(dd, cmd.children[0]))
    _print(on_seq if on else off_seq)

def _term_with_count(dd: DataDictionary, cmd: Tree, control_seq: str) -> None:
    count = 1 if len(cmd.children) == 0 else int(eval_expr(dd, cmd.children[0]))
    _print(control_seq.format(count))

def _term_get_terminal_size(dd: DataDictionary, _: Tree) -> None:
    if not _DUMB_TERM:
        try:
            response =  shutil.get_terminal_size()
            if response is not None and len(response) >= 2:
                dd.set_var(response[0], 'term', 'size', 'cols')
                dd.set_var(response[1], 'term', 'size', 'rows')
                return
        except (OSError, ValueError):
            pass
    dd.set_var(None, 'term', 'size')

def _get_cursor_pos():
    return _parse_dsr_response(TermConsts.DSR_CURSOR, 'R')

def _term_get_cursor_pos(dd: DataDictionary, _: Tree) -> None:
    if not _DUMB_TERM:
        response = _get_cursor_pos()
        if response is None or len(response) < 2:
            dd.set_var(None, 'term', 'cursor')
        else:
            dd.set_var(response[0], 'term', 'cursor', 'row')
            dd.set_var(response[1], 'term', 'cursor', 'col')

def _parse_dsr_response(seq: str, terminator: str) -> list[int]:
    if _DUMB_TERM: return None
    ascii_zero = ord('0')
    ascii_nine = ord('9')
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        _print(seq)
        state = 'ESCAPE'
        acc = 0
        response = []
        while True:
            ch = sys.stdin.read(1)
            if state == 'ESCAPE':
                if ch == '\x1b':
                    state = 'BRACKET'
                elif ch == 0x9b:
                    state = 'NUM'
                else:
                    break
            elif state == 'BRACKET':
                if ch != '[': break
                state = 'NUM'
            elif state == 'NUM':
                c = ord(ch)
                if ascii_zero <= c <= ascii_nine:
                    acc = acc * 10 + (c - ascii_zero)
                elif ch == ';':
                    response.append(acc)
                    acc = 0
                else:
                    if ch != terminator: break
                    response.append(acc)
                    return response
            else:
                raise ValueError()
        return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

_CMD_DISPATCH = {
    "box":            _term_draw_box,
    "clear":          lambda _d, _c: _print(TermConsts.ED_ALL, TermConsts.CUP_HOME),
    "ctrl_ack":       lambda _d, _c: _print("\x06"),
    "ctrl_bel":       lambda _d, _c: _print("\a"),
    "ctrl_bs":        lambda _d, _c: _print("\b"),
    "ctrl_can":       lambda _d, _c: _print("\x18"),
    "ctrl_cr":        lambda _d, _c: _print("\r"),
    "ctrl_dc1":       lambda _d, _c: _print("\x11"),
    "ctrl_dc2":       lambda _d, _c: _print("\x12"),
    "ctrl_dc3":       lambda _d, _c: _print("\x13"),
    "ctrl_dc4":       lambda _d, _c: _print("\x14"),
    "ctrl_dle":       lambda _d, _c: _print("\x10"),
    "ctrl_em":        lambda _d, _c: _print("\x19"),
    "ctrl_enq":       lambda _d, _c: _print("\x05"),
    "ctrl_eot":       lambda _d, _c: _print("\x04"),
    "ctrl_esc":       lambda _d, _c: _print("\x1b"),
    "ctrl_etb":       lambda _d, _c: _print("\x17"),
    "ctrl_etx":       lambda _d, _c: _print("\x03"),
    "ctrl_ff":        lambda _d, _c: _print("\f"),
    "ctrl_fs":        lambda _d, _c: _print("\x1c"),
    "ctrl_gs":        lambda _d, _c: _print("\x1d"),
    "ctrl_ht":        lambda _d, _c: _print("\t"),
    "ctrl_lf":        lambda _d, _c: _print("\n"),
    "ctrl_nak":       lambda _d, _c: _print("\x15"),
    "ctrl_nul":       lambda _d, _c: _print("\x00"),
    "ctrl_rs":        lambda _d, _c: _print("\x1e"),
    "ctrl_si":        lambda _d, _c: _print("\x0f"),
    "ctrl_so":        lambda _d, _c: _print("\x0e"),
    "ctrl_soh":       lambda _d, _c: _print("\x01"),
    "ctrl_stx":       lambda _d, _c: _print("\x02"),
    "ctrl_sub":       lambda _d, _c: _print("\x1a"),
    "ctrl_syn":       lambda _d, _c: _print("\x16"),
    "ctrl_us":        lambda _d, _c: _print("\x1f"),
    "ctrl_vt":        lambda _d, _c: _print("\v"),
    "cub":            lambda d, c: _term_with_count(d, c, TermConsts.CUB),
    "cud":            lambda d, c: _term_with_count(d, c, TermConsts.CUD),
    "cuf":            lambda d, c: _term_with_count(d, c, TermConsts.CUF),
    "cup_home":       lambda _d, _c: _print(TermConsts.CUP_HOME),
    "cup":            _term_cursor_moveto,
    "cuu":            lambda d, c: _term_with_count(d, c, TermConsts.CUU),
    "dch":            lambda d, c: _term_with_count(d, c, TermConsts.DCH),
    "decaln":         lambda _d, _c: _print(TermConsts.DECALN),
    "decawm":         lambda d, c: _term_toggle(d, c, TermConsts.DECAWM_SET, TermConsts.DECAWM_RESET),
    "decdhl_bot":     lambda d, c: _term_toggle(d, c, TermConsts.DECDHL_BOT, TermConsts.DECSWL),
    "decdhl_top":     lambda d, c: _term_toggle(d, c, TermConsts.DECDHL_TOP, TermConsts.DECSWL),
    "decdwl":         lambda d, c: _term_toggle(d, c, TermConsts.DECDWL, TermConsts.DECSWL),
    "decom":          lambda d, c: _term_toggle(d, c, TermConsts.DECOM_SET, TermConsts.DECOM_RESET),
    "decrc":          lambda _d, _c: _print(TermConsts.DECRC),
    "decsc":          lambda _d, _c: _print(TermConsts.DECSC),
    "decsclm":        lambda d, c: _term_toggle(d, c, TermConsts.DECSCLM_SET, TermConsts.DECSCLM_RESET),
    "decstr":         lambda _d, _c: _print(TermConsts.DECSTR),
    "decswl":         lambda d, c: _term_toggle(d, c, TermConsts.DECSWL, TermConsts.DECDWL),
    "dectcem_reset":  lambda _d, _c: _print(TermConsts.DECTCEM_RESET),
    "dectcem_set":    lambda _d, _c: _print(TermConsts.DECTCEM_SET),
    "dectcem":        lambda d, c: _term_toggle(d, c, TermConsts.DECTCEM_SET, TermConsts.DECTCEM_RESET),
    "deiconify":      lambda _d, _c: _print(TermConsts.DEICONIFY),
    "dh_print":       _term_dh_print,
    "dl":             lambda d, c: _term_with_count(d, c, TermConsts.DL),
    "dsr_cursor":     _term_get_cursor_pos,
    "ech":            lambda d, c: _term_with_count(d, c, TermConsts.ECH),
    "ed_bos":         lambda _d, _c: _print(TermConsts.ED_BCK),
    "ed_eos":         lambda _d, _c: _print(TermConsts.ED_FWD),
    "ed":             lambda _d, _c: _print(TermConsts.ED_ALL),
    "el_bol":         lambda _d, _c: _print(TermConsts.EL_BOL),
    "el_eol":         lambda _d, _c: _print(TermConsts.EL_EOL),
    "el":             lambda _d, _c: _print(TermConsts.EL_ALL),
    "hline":          _term_draw_hline,
    "hpa":            lambda d, c: _term_with_count(d, c, TermConsts.HPA),
    "hts":            lambda _d, _c: _print(TermConsts.HTS),
    "ich":            lambda d, c: _term_with_count(d, c, TermConsts.ICH),
    "icon_name":      _term_icon_name,
    "il":             lambda d, c: _term_with_count(d, c, TermConsts.IL),
    "ind":            lambda _d, _c: _print(TermConsts.IND),
    "irm":            lambda d, c: _term_toggle(d, c, TermConsts.IRM_SET, TermConsts.IRM_RESET),
    "print":          lambda d, c: (val := eval_expr(d, c.children[0])) is not None and _print(str(val)),
    "raise_window":   lambda _d, _c: _print(TermConsts.RAISE_WINDOW),
    "rep":            lambda d, c: _term_with_count(d, c, TermConsts.REP),
    "reverse_video":  lambda d, c: _term_toggle(d, c, TermConsts.DECSCNM_SET, TermConsts.DECSCNM_RESET),
    "ri":             lambda _d, _c: _print(TermConsts.RI),
    "ris":            lambda _d, _c: _print(TermConsts.RIS),
    "s7c1t":          lambda d, c: _term_toggle(d, c, TermConsts.S7C1T, TermConsts.S8C1T),
    "s8c1t":          lambda d, c: _term_toggle(d, c, TermConsts.S8C1T, TermConsts.S7C1T),
    "secstbm":        _term_scroll_region,
    "sgr_bg":         lambda d, c: _term_color(d, c, TermConsts.SGR_RESET_BG, TermConsts.SGR_BG),
    "sgr_blink":      lambda d, c: _term_toggle(d, c, TermConsts.SGR_BLINK_ON, TermConsts.SGR_BLINK_OFF),
    "sgr_bold":       lambda d, c: _term_toggle(d, c, TermConsts.SGR_BOLD_ON, TermConsts.SGR_BOLD_OFF),
    "sgr_dim":        lambda d, c: _term_toggle(d, c, TermConsts.SGR_DIM_ON, TermConsts.SGR_DIM_OFF),
    "sgr_fg":         lambda d, c: _term_color(d, c, TermConsts.SGR_RESET_FG, TermConsts.SGR_FG),
    "sgr_hidden":     lambda d, c: _term_toggle(d, c, TermConsts.SGR_HIDDEN_ON, TermConsts.SGR_HIDDEN_OFF),
    "sgr_italic":     lambda d, c: _term_toggle(d, c, TermConsts.SGR_ITALIC_ON, TermConsts.SGR_ITALIC_OFF),
    "sgr_reset":      lambda _d, _c: _print(TermConsts.SGR_RESET),
    "sgr_reverse":    lambda d, c: _term_toggle(d, c, TermConsts.SGR_REVERSE_ON, TermConsts.SGR_REVERSE_OFF),
    "sgr_strikethru": lambda d, c: _term_toggle(d, c, TermConsts.SGR_STRIKETHRU_ON, TermConsts.SGR_STRIKETHRU_OFF),
    "sgr_style":       _term_sgr_style,
    "sgr_underline":  lambda d, c: _term_toggle(d, c, TermConsts.SGR_UNDERLINE_ON, TermConsts.SGR_UNDERLINE_OFF),
    "tbc_all":        lambda _d, _c: _print(TermConsts.TBC_ALL),
    "tbc":            lambda _d, _c: _print(TermConsts.TBC),
    "term_size":      _term_get_terminal_size,
    "vline":          _term_draw_vline,
    "vpa":            lambda d, c: _term_with_count(d, c, TermConsts.VPA),
    "window_title":   _term_window_title,
    "term_set_clipboard": _term_set_clipboard,
}

def execute_term_statement(dd: DataDictionary, statement: Tree) -> None:
    for cmd in statement.children:
        try:
            handler = _CMD_DISPATCH.get(cmd.data)
            if handler is None: raise ValueError(f"Unhandled term command: {cmd.data}")
            handler(dd, cmd)
        except (Exception, KeyboardInterrupt) as e:
            raise VgrRuntimeError(cmd, e) from e
