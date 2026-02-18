"""
Term(inal) Statements
"""

from enum import IntEnum, auto
from functools import lru_cache, cached_property
from typing import Any
import base64
import json
import os
import re
import shutil
import sys
import time

from lark import Tree

from ..app_exceptions import VgrRuntimeError
from ..data_dict import DataDictionary
from ..exec_context import ExecContext
from ..extn import VgrExtension
from ..mathpak import bound_ops
from ..redir import stdout

from .xterm_colors import TERM_COLORS, AUX_COLORS

# pylint: disable=invalid-name
class BoxPart(IntEnum):

    hbar   = 0
    vbar   = auto()
    tl     = auto()
    tr     = auto()
    bl     = auto()
    br     = auto()
    lt     = auto()
    rt     = auto()
    tt     = auto()
    bt     = auto()
    cc     = auto()
    rvbar  = auto()
    lvmid  = auto()
    rvmid  = auto()

    @cached_property
    def iname(self):
        return self.name.casefold()

    @classmethod
    @lru_cache(maxsize=1)
    def max_index(cls):
        return max(member.value for member in cls)

class BoxStyle(IntEnum):

    Blank        = 0
    ASCII        = auto()
    Single       = auto()
    Double       = auto()
    SingleDouble = auto()
    DoubleSingle = auto()
    Brackets     = auto()
    Parens       = auto()
    Braces       = auto()
    Light        = auto()
    LightRounded = auto()
    LightDash2   = auto()
    LightDash3   = auto()
    LightDash4   = auto()
    Heavy        = auto()
    HeavyDash2   = auto()
    HeavyDash3   = auto()
    HeavyDash4   = auto()
    LightHeavy   = auto()
    HeavyLight   = auto()

    @cached_property
    def iname(self):
        return self.name.casefold()

    @classmethod
    @lru_cache(maxsize=1)
    def max_index(cls):
        return max(member.value for member in cls)

    @classmethod
    @lru_cache(maxsize=1)
    def _abbrev_map(cls):
        # include CSS-like names
        return {
            '':        cls.Single,
            'a':       cls.ASCII,
            'b':       cls.Blank,
            'bracket': cls.Brackets,
            'd':       cls.Double,
            'dashed':  cls.LightDash2,
            'dotted':  cls.LightDash4,
            'ds':      cls.DoubleSingle,
            'e':       cls.Blank,
            'empty':   cls.Blank,
            'groove':  cls.Double,
            'h':       cls.Heavy,
            'hd':      cls.HeavyDash3,
            'hd2':     cls.HeavyDash2,
            'hd3':     cls.HeavyDash3,
            'hd4':     cls.HeavyDash4,
            'hl':      cls.HeavyLight,
            'inset':   cls.Heavy,
            'l':       cls.Light,
            'ld':      cls.LightDash3,
            'ld2':     cls.LightDash2,
            'ld3':     cls.LightDash3,
            'ld4':     cls.LightDash4,
            'lh':      cls.LightHeavy,
            'lr':      cls.LightRounded,
            'none':    cls.Blank,
            'outset':  cls.Heavy,
            'p':       cls.Parens,
            'paren':   cls.Parens,
            'r':       cls.LightRounded,
            'ridge':   cls.Heavy,
            'rounded': cls.LightRounded,
            's':       cls.Single,
            'sd':      cls.SingleDouble,
            'solid':   cls.Single,
        }

    @classmethod
    def to_style(cls, val: Any):
        if val is None: return BoxStyle.Single
        if isinstance(val, (int, float)):
            return max(0, min(BoxStyle.max_index(), int(val)))
        if isinstance(val, str):
            s = re.sub(r'[^a-z0-9]', '', val.strip().casefold())
            for style in BoxStyle:
                if style.iname == s: return style
            return cls._abbrev_map().get(s, BoxStyle.Single)
        return BoxStyle.Blank

# pylint: enable=invalid-name

# NB: See https://unicodeplus.com/category/Sm/4 for details on multi part characters
BOXES = {
    BoxStyle.Blank:        (' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '),
    BoxStyle.ASCII:        ('-', '|', '+', '+', '+', '+', '+', '+', '+', '+', '+', '|', '|', '|'),
    BoxStyle.Single:       ('─', '│', '┌', '┐', '└', '┘', '├', '┤', '┬', '┴', '┼', '│', '│', '│'),
    BoxStyle.Double:       ('═', '║', '╔', '╗', '╚', '╝', '╠', '╣', '╦', '╩', '╬', '║', '║', '║'),
    BoxStyle.SingleDouble: ('─', '║', '╓', '╖', '╙', '╜', '╟', '╢', '╥', '╨', '╫', '║', '║', '║'),
    BoxStyle.DoubleSingle: ('═', '│', '╒', '╕', '╘', '╛', '╞', '╡', '╤', '╧', '╪', '│', '│', '│'),
    BoxStyle.Brackets:     (' ', '⎢', '⎡', '⎤', '⎣', '⎦', ' ', ' ', ' ', ' ', ' ', '⎥', '⎢', '⎥'),
    BoxStyle.Parens:       (' ', '⎜', '⎛', '⎞', '⎝', '⎠', ' ', ' ', ' ', ' ', ' ', '⎟', '⎜', '⎟'),
    BoxStyle.Braces:       (' ', '⎪', '⎧', '⎫', '⎩', '⎭', ' ', ' ', ' ', ' ', ' ', '⎪', '⎨', '⎬'),
    BoxStyle.Light:        ('─', '│', '┌', '┐', '└', '┘', '├', '┤', '┬', '┴', '┼', '│', '│', '│'),
    BoxStyle.LightRounded: ('─', '│', '╭', '╮', '╰', '╯', '├', '┤', '┬', '┴', '┼', '│', '│', '│'),
    BoxStyle.LightDash2:   ('╌', '╎', '┌', '┐', '└', '┘', '├', '┤', '┬', '┴', '┼', '╎', '╎', '╎'),
    BoxStyle.LightDash3:   ('┄', '┆', '┌', '┐', '└', '┘', '├', '┤', '┬', '┴', '┼', '┆', '┆', '┆'),
    BoxStyle.LightDash4:   ('┈', '┊', '┌', '┐', '└', '┘', '├', '┤', '┬', '┴', '┼', '┊', '┊', '┊'),
    BoxStyle.Heavy:        ('━', '┃', '┏', '┓', '┗', '┛', '┣', '┫', '┳', '┻', '╋', '┃', '┃', '┃'),
    BoxStyle.HeavyDash2:   ('╍', '╏', '┏', '┓', '┗', '┛', '┣', '┫', '┳', '┻', '╋', '╏', '╏', '╏'),
    BoxStyle.HeavyDash3:   ('┅', '┇', '┏', '┓', '┗', '┛', '┣', '┫', '┳', '┻', '╋', '┇', '┇', '┇'),
    BoxStyle.HeavyDash4:   ('┉', '┋', '┏', '┓', '┗', '┛', '┣', '┫', '┳', '┻', '╋', '┋', '┋', '┋'),
    BoxStyle.LightHeavy:   ('─', '┃', '┎', '┒', '┖', '┚', '┠', '┨', '┰', '┸', '╂', '┃', '┃', '┃'),
    BoxStyle.HeavyLight:   ('━', '│', '┍', '┑', '┕', '┙', '┝', '┥', '┯', '┷', '┿', '│', '│', '│'),
}

class TermConsts:
    """
    Reference material:
        https://vt100.net/docs/vt220-rm/contents.html
        https://www.xfree86.org/current/ctlseqs.html
        https://invisible-island.net/xterm/ctlseqs/ctlseqs.html
    """

    SOS = "\x1bX" # Start of String (SOS is 0x98)
    CSI = "\x1b[" # Control Sequence Introducer (CSI is 0x9b)
    ST = "\x1b\\" # String Terminator (ST is 0x9c)
    OSC = "\x1b]" # Operating System Command (OSC is 0x9d)

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

_COLOR_NAME_MAP = { }
_DUMB_TERM = os.getenv('TERM', '').lower() == 'dumb'
_NO_COLOR = "NO_COLOR" in os.environ

def add_dd_constants(dd: DataDictionary, prefix: str) -> None:
    def _boxes():
        boxes = {}
        for style, parts in BOXES.items():
            boxes[style.iname] = {part.iname: parts[part.value] for part in BoxPart}
        return boxes
    dd.set_var(_boxes(), prefix, 'box')
    dd.set_var([style.name for style in BoxStyle], prefix, 'box_styles')
    dd.set_var(TERM_COLORS, prefix, 'color_names')
    # TODO this block seems misplaced
    for val, name in enumerate(TERM_COLORS):
        _COLOR_NAME_MAP[_canonical_color_name(name)] = val
    for name, val in AUX_COLORS.items():
        _COLOR_NAME_MAP[_canonical_color_name(name)] = val
    #####
    dd.set_var(_DUMB_TERM, prefix, 'dumb_term')
    dd.set_var(_NO_COLOR, prefix, 'no_color')
    dd.set_var(json.loads(VgrExtension.read_resource_text(__package__, 'spinners.json')), prefix, 'spinner')
    dd.set_var('https://github.com/sindresorhus/cli-spinners/blob/main/spinners.json', prefix, 'spinners_source')

def _print(*args: Any, flush: bool= False, sleep: float= 0.0, **kwargs: Any) -> None:
    """
    Print to the terminal, optionally flushing and sleeping after flush.

    Args:
        *args: Values to print.
        flush (bool): Whether to flush the output (default False).
        sleep (float): Time in seconds to sleep after flushing (default 0.0).
        **kwargs: Additional print() keyword arguments (e.g., end, file, sep).
    """
    if _DUMB_TERM: return
    out = stdout()
    if out.isatty():
        flush = sleep > 0 or flush
        print(*args, file=out, sep='', end='', flush=flush, **kwargs)
        if sleep > 0: time.sleep(sleep)

def _flush() -> None:
    out = stdout()
    if out.isatty(): out.flush()

def _term_cursor_moveto(ctx: ExecContext, cmd: Tree) -> None:
    line = ctx.eval_to_int(cmd.children[0], "Line")
    col = ctx.eval_to_int(cmd.children[1], "Column")
    _print(TermConsts.CUP.format(line, col))

def _resolve_ansi_color(val: Any) -> int:
    if isinstance(val, (int, float)):
        val = round(val)
        return val if 0 <= val <= 255 else None
    if not isinstance(val, str): return None
    val = val.strip()
    try:
        v = round(float(val))
        return v if 0 <= v <= 255 else None
    except ValueError:
        pass
    m = re.fullmatch(r"color(\d{1,3})", val)
    if m:
        v = int(m.group(1))
        if 0 <= v <= 255: return v
    return _COLOR_NAME_MAP.get(_canonical_color_name(val))

def _canonical_color_name(val: str) -> str:
    val = re.sub(r'[^a-z0-9]', '', val.casefold())
    return val.replace('gray', 'grey')

# Everything except colors
_SGR_ALL_OFF = (
    TermConsts.SGR_BOLD_OFF, TermConsts.SGR_DIM_OFF, TermConsts.SGR_BLINK_OFF,
    TermConsts.SGR_ITALIC_OFF, TermConsts.SGR_UNDERLINE_OFF, TermConsts.SGR_REVERSE_OFF,
    TermConsts.SGR_HIDDEN_OFF, TermConsts.SGR_STRIKETHRU_OFF
)

def _term_sgr_style(ctx: ExecContext, cmd: Tree) -> None:
    reqs = str(ctx.eval_expr(cmd.children[0])).strip() if len(cmd.children) > 0 else ''
    if not reqs: return
    _print(*_SGR_ALL_OFF)
    for s in re.split(r'[^a-z0-9_+-]', reqs.casefold()):
        if s.isdigit():
            c = _resolve_ansi_color(s)
            if c and not _NO_COLOR: _print(TermConsts.SGR_FG.format(c))
            continue
        if s in ("reset",):
            # This resets FG color and "wide"
            _print(TermConsts.SGR_RESET_FG, TermConsts.DECSWL)
            # INTENTIONAL FALL-THRU
        if s in ("reset", "normal", "default"):
            # This resets everything else
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
            _print(TermConsts.DECSWL if negate else TermConsts.DECDWL, sleep=0.01)
            continue
        if s in ("single",):
            _print(TermConsts.DECDWL if negate else TermConsts.DECSWL, sleep=0.01)
            continue
        # Failed all the keyword tests; see if it is a named
        # color for the foreground
        if not _NO_COLOR:
            c = _resolve_ansi_color(s)
            if c: _print(TermConsts.SGR_FG.format(c))
        # errors ignored

def _term_set_clipboard(ctx: ExecContext, cmd: Tree) -> None:
    text = str(ctx.eval_expr(cmd.children[0])).strip() if len(cmd.children) > 0 else ''
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

def _term_draw_hline(ctx: ExecContext, cmd: Tree) -> None:
    arg_ind = 0
    args = _eval_all(ctx, cmd)
    if len(args) > 1:
        style = BoxStyle.to_style(args[arg_ind])
        arg_ind += 1
    else:
        style = BoxStyle.Single
    _draw_hline(style, max(0, int(args[arg_ind])))

def _draw_hline(style: BoxStyle, cols: int) -> None:
    if cols:
        _print(BOXES[style][BoxPart.hbar] * cols)

def _term_draw_vline(ctx: ExecContext, cmd: Tree) -> None:
    arg_ind = 0
    args = _eval_all(ctx, cmd)
    if len(args) > 1:
        style = BoxStyle.to_style(args[arg_ind])
        arg_ind += 1
    else:
        style = BoxStyle.Single
    _draw_vline(style, max(0, int(args[arg_ind])))

def _draw_vline(style: BoxStyle, lines: int) -> None:
    if lines:
        for _ in range(lines):
            _print(BOXES[style][BoxPart.vbar], _CUB_1, _CUD_1)

def _eval_all(ctx: ExecContext, cmd: Tree) -> list:
    return [ctx.eval_expr_or_const(child) for child in cmd.children]

def _term_draw_box(ctx: ExecContext, cmd: Tree) -> None:
    if _DUMB_TERM: return
    arg_ind = 0
    args = _eval_all(ctx, cmd)
    if len(args) > 2:
        style = BoxStyle.to_style(args[arg_ind])
        arg_ind += 1
    else:
        style = BoxStyle.Single
    height = int(args[arg_ind])
    width = int(args[arg_ind + 1])
    cur_rsp = _get_cursor_pos()
    if cur_rsp is None: return
    start_row, start_col = cur_rsp
    screen_cols, screen_rows = shutil.get_terminal_size()
    # Vertical adjustment
    if height >= 0:
        height = min(height, screen_rows - start_row + 1)
    else:
        height = min(-height, start_row)
        start_row = start_row - height + 1
    # Horizontal adjustment
    if width >= 0:
        width = min(width, screen_cols - start_col + 1)
    else:
        width = min(-width, start_col)
        start_col = start_col - width + 1
    if height == 0 or width == 0: return
    # Horizontal line
    if height == 1:
        _draw_hline(style, width)
        return
    # Vertical line
    if width == 1:
        _draw_vline(style, height)
        return
    row = start_row
    col = start_col
    # Box is at least 2x2
    inner_width = width - 2
    box = BOXES[style]
    hbar = box[BoxPart.hbar] * inner_width if inner_width else ''
    # Box top
    _print(TermConsts.CUP.format(row, col), box[BoxPart.tl], hbar, box[BoxPart.tr])
    # Left and right sides
    row += 1
    if height > 2:
        inside = ''
        if inner_width:
            inside = ' '
            if inner_width > 1: inside += TermConsts.REP.format(inner_width - 1)
        for _ in range(height - 2):
            _print(TermConsts.CUP.format(row, col), box[BoxPart.vbar], inside, box[BoxPart.rvbar])
            row += 1
        # if the mid parts exist, paint them
        lvmid = box[BoxPart.lvmid]
        if lvmid is not None:
            _print(TermConsts.CUP.format(start_row + (height // 2), start_col), lvmid)
        rvmid = box[BoxPart.rvmid]
        if rvmid is not None:
            _print(TermConsts.CUP.format(start_row + (height // 2), start_col + width - 1), rvmid)
    # And the bottom
    _print(TermConsts.CUP.format(start_row + height - 1, start_col), box[BoxPart.bl], hbar, box[BoxPart.br])
    # Move to within the box's boarder
    _print(TermConsts.CUP.format(start_row + 1, start_col + 1))

def _term_dh_print(ctx: ExecContext, cmd: Tree) -> None:
    s = ctx.eval_expr(cmd.children[0])
    if s is not None:
        # Turn the current and following lines into double high lines
        for x in [TermConsts.DECDHL_TOP, _CUD_1, TermConsts.DECDHL_BOT, _CUU_1]:
            _print(x, sleep=0.01)
        # Paint each char on both lines to form the full text
        for char in str(s):
            _print(char, _CUB_1, _CUD_1, char, _CUU_1)

def _term_scroll_region(ctx: ExecContext, cmd: Tree) -> None:
    top = ctx.eval_to_int(cmd.children[0], "Top")
    bottom = ctx.eval_to_int(cmd.children[1], "Bottom")
    _print(TermConsts.SECSTBM.format(top, bottom))

def _term_icon_name(ctx: ExecContext, cmd: Tree) -> None:
    s = ctx.eval_expr(cmd.children[0])
    s = '' if s is None else str(s)
    _print(TermConsts.ICON_NAME.format(s))

def _term_window_title(ctx: ExecContext, cmd: Tree) -> None:
    s = ctx.eval_expr(cmd.children[0])
    s = '' if s is None else str(s)
    _print(TermConsts.WINDOW_TITLE.format(s))

def _term_color(ctx: ExecContext, cmd: Tree, reset_seq: str, color_fmt: str) -> None:
    if _NO_COLOR:
        return
    if len(cmd.children) == 0:
        _print(reset_seq)
    else:
        value = ctx.eval_expr(cmd.children[0])
        code = _resolve_ansi_color(value)
        _print(reset_seq if code is None else color_fmt.format(code))

def _term_toggle(ctx: ExecContext, cmd: Tree, on_seq: str, off_seq: str) -> None:
    on = True if len(cmd.children) == 0 else bool(ctx.eval_expr(cmd.children[0]))
    _print(on_seq if on else off_seq)

def _term_with_count(ctx: ExecContext, cmd: Tree, control_seq: str) -> None:
    count = 1 if len(cmd.children) == 0 else ctx.eval_to_int(cmd.children[0], "Count")
    _print(control_seq.format(count))

def _term_get_terminal_size(ctx: ExecContext, _: Tree) -> None:
    """
    Get the window size in term.size.rows/cols
    If not available, term.size will be empty
    """
    response = None
    if not _DUMB_TERM:
        try:
            response =  shutil.get_terminal_size()
        except (OSError, ValueError):
            pass
    if response is None or len(response) < 2:
        ctx.set_var({}, 'term', 'size')
    else:
        ctx.set_var(response[0], 'term', 'size', 'cols')
        ctx.set_var(response[1], 'term', 'size', 'rows')

def _term_get_cursor_pos(ctx: ExecContext, _: Tree) -> None:
    """
    Get the cursor position in term.cursor.row/col (1 based)
    If not available, term.cursor will be empty
    """
    response = None if _DUMB_TERM else _get_cursor_pos()
    if response is None or len(response) < 2:
        ctx.set_var({}, 'term', 'cursor')
    else:
        ctx.set_var(response[0], 'term', 'cursor', 'row')
        ctx.set_var(response[1], 'term', 'cursor', 'col')

def _get_cursor_pos() -> list[int]:
    """
    Internal call to get and return the row & col in a list.
    May return None.
    """
    if sys.platform.startswith("win"):
        from .win_api import win_get_cursor_pos
        return win_get_cursor_pos()
    return _parse_dsr_response(TermConsts.DSR_CURSOR, 'R')

def _parse_dsr_response(seq: str, terminator: str) -> list[int]:
    """
    Internal call to make a DSR request and return the integer results in a list.
    Unix only!
    """
    ascii_zero = ord('0')
    ascii_nine = ord('9')
    old_settings = None
    fd = None
    try:
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
    except Exception:
        return None
    try:
        try:
            import tty
            tty.setcbreak(fd)
        except Exception:
            return None
        _print(seq, flush=True)
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
        try:
            import termios
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception:
            return None

_CMD_DISPATCH = {
    "box":            _term_draw_box,
    "clear":          lambda _ctx, _cmd: _print(TermConsts.ED_ALL, TermConsts.CUP_HOME),
    "ctrl_ack":       lambda _ctx, _cmd: _print("\x06"),
    "ctrl_bel":       lambda _ctx, _cmd: _print("\a"),
    "ctrl_bs":        lambda _ctx, _cmd: _print("\b"),
    "ctrl_can":       lambda _ctx, _cmd: _print("\x18"),
    "ctrl_cr":        lambda _ctx, _cmd: _print("\r"),
    "ctrl_dc1":       lambda _ctx, _cmd: _print("\x11"),
    "ctrl_dc2":       lambda _ctx, _cmd: _print("\x12"),
    "ctrl_dc3":       lambda _ctx, _cmd: _print("\x13"),
    "ctrl_dc4":       lambda _ctx, _cmd: _print("\x14"),
    "ctrl_dle":       lambda _ctx, _cmd: _print("\x10"),
    "ctrl_em":        lambda _ctx, _cmd: _print("\x19"),
    "ctrl_enq":       lambda _ctx, _cmd: _print("\x05"),
    "ctrl_eot":       lambda _ctx, _cmd: _print("\x04"),
    "ctrl_esc":       lambda _ctx, _cmd: _print("\x1b"),
    "ctrl_etb":       lambda _ctx, _cmd: _print("\x17"),
    "ctrl_etx":       lambda _ctx, _cmd: _print("\x03"),
    "ctrl_ff":        lambda _ctx, _cmd: _print("\f"),
    "ctrl_fs":        lambda _ctx, _cmd: _print("\x1c"),
    "ctrl_gs":        lambda _ctx, _cmd: _print("\x1d"),
    "ctrl_ht":        lambda _ctx, _cmd: _print("\t"),
    "ctrl_lf":        lambda _ctx, _cmd: _print("\n"),
    "ctrl_nak":       lambda _ctx, _cmd: _print("\x15"),
    "ctrl_nul":       lambda _ctx, _cmd: _print("\x00"),
    "ctrl_rs":        lambda _ctx, _cmd: _print("\x1e"),
    "ctrl_si":        lambda _ctx, _cmd: _print("\x0f"),
    "ctrl_so":        lambda _ctx, _cmd: _print("\x0e"),
    "ctrl_soh":       lambda _ctx, _cmd: _print("\x01"),
    "ctrl_stx":       lambda _ctx, _cmd: _print("\x02"),
    "ctrl_sub":       lambda _ctx, _cmd: _print("\x1a"),
    "ctrl_syn":       lambda _ctx, _cmd: _print("\x16"),
    "ctrl_us":        lambda _ctx, _cmd: _print("\x1f"),
    "ctrl_vt":        lambda _ctx, _cmd: _print("\v"),
    "cub":            lambda ctx, cmd: _term_with_count(ctx, cmd, TermConsts.CUB),
    "cud":            lambda ctx, cmd: _term_with_count(ctx, cmd, TermConsts.CUD),
    "cuf":            lambda ctx, cmd: _term_with_count(ctx, cmd, TermConsts.CUF),
    "cup_home":       lambda _ctx, _cmd: _print(TermConsts.CUP_HOME),
    "cup":            _term_cursor_moveto,
    "cuu":            lambda ctx, cmd: _term_with_count(ctx, cmd, TermConsts.CUU),
    "dch":            lambda ctx, cmd: _term_with_count(ctx, cmd, TermConsts.DCH),
    "decaln":         lambda _ctx, _cmd: _print(TermConsts.DECALN),
    "decawm":         lambda ctx, cmd: _term_toggle(ctx, cmd, TermConsts.DECAWM_SET, TermConsts.DECAWM_RESET),
    "decdhl_bot":     lambda ctx, cmd: _term_toggle(ctx, cmd, TermConsts.DECDHL_BOT, TermConsts.DECSWL),
    "decdhl_top":     lambda ctx, cmd: _term_toggle(ctx, cmd, TermConsts.DECDHL_TOP, TermConsts.DECSWL),
    "decdwl":         lambda ctx, cmd: _term_toggle(ctx, cmd, TermConsts.DECDWL, TermConsts.DECSWL),
    "decom":          lambda ctx, cmd: _term_toggle(ctx, cmd, TermConsts.DECOM_SET, TermConsts.DECOM_RESET),
    "decrc":          lambda _ctx, _cmd: _print(TermConsts.DECRC),
    "decsc":          lambda _ctx, _cmd: _print(TermConsts.DECSC),
    "decsclm":        lambda ctx, cmd: _term_toggle(ctx, cmd, TermConsts.DECSCLM_SET, TermConsts.DECSCLM_RESET),
    "decstr":         lambda _ctx, _cmd: _print(TermConsts.DECSTR),
    "decswl":         lambda ctx, cmd: _term_toggle(ctx, cmd, TermConsts.DECSWL, TermConsts.DECDWL),
    "dectcem_reset":  lambda _ctx, _cmd: _print(TermConsts.DECTCEM_RESET),
    "dectcem_set":    lambda _ctx, _cmd: _print(TermConsts.DECTCEM_SET),
    "dectcem":        lambda ctx, cmd: _term_toggle(ctx, cmd, TermConsts.DECTCEM_SET, TermConsts.DECTCEM_RESET),
    "deiconify":      lambda _ctx, _cmd: _print(TermConsts.DEICONIFY, flush=True),
    "dh_print":       _term_dh_print,
    "dl":             lambda ctx, cmd: _term_with_count(ctx, cmd, TermConsts.DL),
    "dsr_cursor":     _term_get_cursor_pos,
    "ech":            lambda ctx, cmd: _term_with_count(ctx, cmd, TermConsts.ECH),
    "ed_bos":         lambda _ctx, _cmd: _print(TermConsts.ED_BCK),
    "ed_eos":         lambda _ctx, _cmd: _print(TermConsts.ED_FWD),
    "ed":             lambda _ctx, _cmd: _print(TermConsts.ED_ALL),
    "el_bol":         lambda _ctx, _cmd: _print(TermConsts.EL_BOL),
    "el_eol":         lambda _ctx, _cmd: _print(TermConsts.EL_EOL),
    "el":             lambda _ctx, _cmd: _print(TermConsts.EL_ALL),
    "hline":          _term_draw_hline,
    "hpa":            lambda ctx, cmd: _term_with_count(ctx, cmd, TermConsts.HPA),
    "hts":            lambda _ctx, _cmd: _print(TermConsts.HTS),
    "ich":            lambda ctx, cmd: _term_with_count(ctx, cmd, TermConsts.ICH),
    "icon_name":      _term_icon_name,
    "il":             lambda ctx, cmd: _term_with_count(ctx, cmd, TermConsts.IL),
    "ind":            lambda _ctx, _cmd: _print(TermConsts.IND),
    "irm":            lambda ctx, cmd: _term_toggle(ctx, cmd, TermConsts.IRM_SET, TermConsts.IRM_RESET),
    "print":          lambda ctx, cmd: (val := ctx.eval_expr(cmd.children[0])) is not None and _print(str(val)),
    "raise_window":   lambda _ctx, _cmd: _print(TermConsts.RAISE_WINDOW, flush=True),
    "rep":            lambda ctx, cmd: _term_with_count(ctx, cmd, TermConsts.REP),
    "reverse_video":  lambda ctx, cmd: _term_toggle(ctx, cmd, TermConsts.DECSCNM_SET, TermConsts.DECSCNM_RESET),
    "ri":             lambda _ctx, _cmd: _print(TermConsts.RI),
    "ris":            lambda _ctx, _cmd: _print(TermConsts.RIS),
    "s7c1t":          lambda ctx, cmd: _term_toggle(ctx, cmd, TermConsts.S7C1T, TermConsts.S8C1T),
    "s8c1t":          lambda ctx, cmd: _term_toggle(ctx, cmd, TermConsts.S8C1T, TermConsts.S7C1T),
    "secstbm":        _term_scroll_region,
    "sgr_bg":         lambda ctx, cmd: _term_color(ctx, cmd, TermConsts.SGR_RESET_BG, TermConsts.SGR_BG),
    "sgr_blink":      lambda ctx, cmd: _term_toggle(ctx, cmd, TermConsts.SGR_BLINK_ON, TermConsts.SGR_BLINK_OFF),
    "sgr_bold":       lambda ctx, cmd: _term_toggle(ctx, cmd, TermConsts.SGR_BOLD_ON, TermConsts.SGR_BOLD_OFF),
    "sgr_dim":        lambda ctx, cmd: _term_toggle(ctx, cmd, TermConsts.SGR_DIM_ON, TermConsts.SGR_DIM_OFF),
    "sgr_fg":         lambda ctx, cmd: _term_color(ctx, cmd, TermConsts.SGR_RESET_FG, TermConsts.SGR_FG),
    "sgr_hidden":     lambda ctx, cmd: _term_toggle(ctx, cmd, TermConsts.SGR_HIDDEN_ON, TermConsts.SGR_HIDDEN_OFF),
    "sgr_italic":     lambda ctx, cmd: _term_toggle(ctx, cmd, TermConsts.SGR_ITALIC_ON, TermConsts.SGR_ITALIC_OFF),
    "sgr_reset":      lambda _ctx, _cmd: _print(TermConsts.SGR_RESET),
    "sgr_reverse":    lambda ctx, cmd: _term_toggle(ctx, cmd, TermConsts.SGR_REVERSE_ON, TermConsts.SGR_REVERSE_OFF),
    "sgr_strikethru": lambda ctx, cmd: _term_toggle(ctx, cmd, TermConsts.SGR_STRIKETHRU_ON, TermConsts.SGR_STRIKETHRU_OFF),
    "sgr_style":       _term_sgr_style,
    "sgr_underline":  lambda ctx, cmd: _term_toggle(ctx, cmd, TermConsts.SGR_UNDERLINE_ON, TermConsts.SGR_UNDERLINE_OFF),
    "space":          lambda _ctx, _cmd: _print(" "),
    "del":            lambda _ctx, _cmd: _print("\x7F"),
    "tbc_all":        lambda _ctx, _cmd: _print(TermConsts.TBC_ALL),
    "tbc":            lambda _ctx, _cmd: _print(TermConsts.TBC),
    "term_size":      _term_get_terminal_size,
    "vline":          _term_draw_vline,
    "vpa":            lambda ctx, cmd: _term_with_count(ctx, cmd, TermConsts.VPA),
    "window_title":   _term_window_title,
    "term_set_clipboard": _term_set_clipboard,
}

@bound_ops("Terminal", "Term")
def execute_term_statement(ctx: ExecContext, statement: Tree) -> None:
    """
**Execute Terminal control commands**

* Terminal *command* [, *command*]&hellip; [;]
* Term *command* [, *command*]&hellip; [;]

_Cursor Control Commands_

* [CursorPos | Pos] _line_, _column_ - Move cursor to line,column, ones based
* [GetCursorPos | GetPos] - Read cursposition into _term.cursor_
* Line [_line_] - Move cursor position to line
* Col [_column_] - Move cursor position to column
* [CursorHome | Home] - Move cursor to 1,1
* [CursorSave | CSave] - Save the cursor location
* [CursorRestore | CRestore] - Reposition cursor to last saved location
* [CursorShow | CShow] - Make the cursor visiable
* [CursorHide | CHide] - Hide the cursor
* CursorVisible [_visible_] - Change cursor visibility
* CursorUp [_lines_] - Move the cursor up one or more lines
* CursorDown [_lines_] - Move the cursor down one or more lines
* [CursorLeft | CursorBack] [_columns_] - Move the cursor left one or more columns
* [CursorRight | CursorForward] [_columns_] - Move the cursor right one or more columns

_Screen Editing Commands_

* [InsertLine | InsertLines] [_count_] - Insert one or more lines
* [DeleteLine | DeleteLines] [_count_] - Delete one or more lines
* [InsertChar | InsertChars] [_count_] - Insert one or more characters at cursor
* [DeleteChar | DeleteChars] [_count_] - Delete one or more characters at cursor
* [EraseChar | EraseChars] [_count_] - Erase one or more characters at cursor
* EraseLine - Erase the current line
* EraseEOL - Erase from cursor to end of the line
* EraseBOL - Erase from cursor to begining of the line
* [EraseDisplay | EraseScreen] - Erase the screen
* EraseEOS - Erase from cursor to end of the screen
* EraseBOS - Erase from cursor to begining of the screen
* [Clear | CLS] - Erase the screen and home the cursor

_Scrolling Commands_

* ScrollUp - Scroll up one line
* ScrollDown - Scroll down one line
* ScrollRegion *start_line*, *end_line* - Scroll text in the given region

_Options Commands_

* S7C1 [*on_off*] - Change between 7 and 8-bit control sequences
* S8C1 [*on_off*] - Change between 7 and 8-bit control sequences
* DECSCNM [expr] - Switch between normal and reverse mode
* SmoothScroll [*on_off*] - Turn smooth scrolling on/off
* OriginMode [*on_off*] - Turn origin mode on/off
* AutoWrap [*on_off*] - Turn auto wrap on/off
* InsertMode [*on_off*] - Toggle between insert and overwrite mode
* SoftReset - Perform a sort reset on the terminal's settings
* HardReset - Perform a hard reset on the terminal's settings
* AlignmentTest - Display an alignment test pattern
* TabSet - Set a tab stop at the cursor's column
* TabClear - Clear a tab stop at the cursor's column
* TabClearAll - Clear all tab stops

_Printing Commands_

* Print _text_ - Print the text starting at the cursor's position
* DHPrint _text_ - Print text in double-high mode
* RepeatChar [_count_] - Repeat the last character a number of times

_Windowing Commands_

* SetClipboard _text_ - Set the system clipboard to _text_
* DeIconify - De-iconify the terminal window
* RaiseWindow - Raise the terminal window to the front
* IconName _text_ - Set the icon name for the terminal window
* WindowTitle _text_ - Set the terminal window's title
* [GetWindowSize | GetTerminalSize | GetTermSize] - Retrieve the window's size; stored in _term.size_

_Sending Control Characters_

* NUL, SOH, STX, ETX, EOT, ENQ, ACK, BEL - 0x00 through 0x07
* BS, HT, LF, VT, FF, CR, SO, SI - 0x08 through 0x0F
* DLE, DC1, DC2, DC3, DC4, NAK, SYN, ETB - 0x10 through 0x17
* CAN, EM, SUB, ESC, FS, GS, RS, US - 0x18 through 0x1F
* SP - 0x20 (Space)
* DEL - 0x7F (Delete)

*Colors and Attrribute Commands*

* Reset - Reset the colors and attributes
* Style *style* - Intepret *style* as colors and attributes
* Bold [*on_off*] - Turn bold on/off
* Dim [*on_off*] - Turn dim on/off
* Blink [*on_off*] - Turn blink on/off
* [Italic | Italics] [*on_off*] - Turn italics on/off
* [Underline | UL] [*on_off*] - Turn underline on/off
* [Foreground | FG] [*color*] - Set the foreground color
* [Background | BG] [*color*] - Set the background color
* [Reverse | Rev] [*on_off*] - Turn reverse on/off
* [Hidden | Hide] [*on_off*] - Turn hidden text on/off
* [Strikethrough | Strikethru | Strikeout ] [*on_off*] - Turn strikethrough text on/off
* [Double | Wide] [*on_off*] - Change between double and single wide characters
* Single [*on_off*] - Change between double and single wide characters
* HighTop [*on_off*] - change the double-high setting of the cursor's line
* HighBottom | HighBot [*on_off*] - change the double-high setting of the cursor's line

*Box and Line Drawing Commands*

* [DrawBox | Box] [*style*,] *height*, *width*
* [DrawHLine | HLine] [*style*,] *length*
* [DrawVLine | VLine] [*style*,] *height*
* Styles - Blank, ASCII, Single Double, SingleDouble, DoubleSingle,
  Brackets, Parens, Braces, Light, LightRounded, LightDash2,
  LightDash3, LightDash4, Heavy, HeavyDash2, HeavyDash3, HeavyDash4,
  LightHeavy, HeavyLight

"""
    try:
        for cmd in statement.children:
            try:
                handler = _CMD_DISPATCH.get(cmd.data)
                if handler is None: raise ValueError(f"Unhandled term command: {cmd.data}")
                handler(ctx, cmd)
            except KeyboardInterrupt as e:
                _print('\n')
                raise VgrRuntimeError(cmd, e) from e
            except Exception as e:
                raise VgrRuntimeError(cmd, e) from e
    finally:
        _flush()
