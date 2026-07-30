from enum import Enum, auto
from typing import Any
import re
import sys
import traceback

from lark import Tree

from lark.exceptions import (
    LarkError,
    LexError,
    ParseError,
    UnexpectedCharacters,
    UnexpectedEOF,
    UnexpectedInput,
    UnexpectedToken,
    VisitError,
)

from .src_mgr import SSM

_ERRNO_RE = re.compile(r'^\[[^\s]+\s+\d+\]\s*')

_ERROR_XLATE = {
    KeyboardInterrupt:    "Interrupted",
    LexError:             "Lexing Error",
    ParseError:           "Parsing Error",
    VisitError:           "Visitor Error",
    ZeroDivisionError:    "Divide by Zero",
}

def _exception_type(e: Exception) -> str:
    """
    Convert the exception type into a human-readable string based on a dictionary.
    If no custom message is found, fallback to the default class name.
    """
    if e is None: return 'Error'
    cls = e if isinstance(e, type) else type(e)
    if cls in _ERROR_XLATE: return _ERROR_XLATE.get(cls)
    # insert space before A-Z if preceded by lowercase or digit
    s = re.sub(r'(?<=[a-z0-9])([A-Z])', r' \1', cls.__name__)
    # handle acronym boundary: XMLParser -> XML Parser
    return re.sub(r'(?<=[A-Z])([A-Z][a-z])', r' \1', s)

class VgrException(Exception):
    def __init__(self, node, orig_exc: Exception, source_origin: str, source_text: str):
        self.node = node
        self.orig_exc = orig_exc
        self.source_origin = source_origin
        self.source_text = source_text
        meta = node.meta if isinstance(node, Tree) else node
        self.line = getattr(meta, 'line', None) if node else None
        self.column = getattr(meta, 'column', None) if node else None

    def get_context(self, span=40):
        if not self.source_text or self.line is None or self.column is None: return ''
        lines = self.source_text.splitlines()
        if not 0 < self.line <= len(lines): return ''
        line_str = lines[self.line - 1]
        # Strip leading whitespace and adjust column
        leading_ws = len(line_str) - len(line_str.lstrip())
        trimmed_line = line_str.lstrip()
        adjusted_column = max(self.column - leading_ws, 1)
        # Compute start and end positions for span truncation
        # NB: lark uses one-based lines and columns
        start = max(0, adjusted_column - 1 - span)
        end = adjusted_column - 1 + span
        snippet = trimmed_line[start:end]
        pointer_line = ' ' * (adjusted_column - 1 - start) + '^'
        return f"{snippet}\n{pointer_line}"

    def __str__(self):
        try:
            msg = self._exception_message() or _exception_type(self.orig_exc) or 'Error'
            src = self.source_origin if self.source_origin and self.source_origin != '<repl>' else None
            line = f'line {self.line}' if self.line else None
            col = f'column {self.column}' if self.column else None
            if src or line or col:
                # All this because join() suxs
                msg += ' at'
                if src: msg += ' ' + src
                if line: msg += ' ' + line
                if col: msg += (', ' if line else ' ') + col
            return '\n'.join((self.get_context(), msg))
        except Exception:
            traceback.print_exc(file=sys.stderr)
            return 'Internal error while generating description'

    def _char_at(self, pos: int) -> str:
        if not self.source_text: return "<?>"
        if pos >= len(self.source_text): return "<eof>"
        return self.source_text[pos]

    def _exception_message(self) -> str:
        """
        Return a user-friendly message from any exception instance.
        - Special cases for OSError and assertions
        """
        e = self.orig_exc
        if e is None: return ''
        if isinstance(e, LexError):
            return f"Invalid value {self._char_at(e.pos_in_stream)!r}"
        if isinstance(e, ParseError):
            if getattr(e, "token", None):
                return f"Unexpected value {e.token.value!r}"
            return "Invalid syntax"
        if isinstance(e, UnexpectedToken):
            return f"Unexpected value {e.token.value!r}"
        if isinstance(e, UnexpectedCharacters):
            return f"Unexpected value {self._char_at(e.pos_in_stream)!r}"
        if isinstance(e, UnexpectedEOF):
            return "Unexpected end of input"
        if isinstance(e, UnexpectedInput):
            return "Syntax Error"
        if isinstance(e, LarkError):
            return "Invalid syntax"
        # Strip  numeric codes at front of OSError
        rc = _ERRNO_RE.sub('', str(e)) if isinstance(e, OSError) else str(e)
        # For these, the text is created either from the source or from a user format, so use verbatim
        return rc if isinstance(self, (VgrStatementAbort, VgrStatementAssert)) else rc.strip()

    @staticmethod
    def rewrap(e: "VgrException") -> "VgrException":
        return VgrException(e.node, e.orig_exc, e.source_origin, e.source_text)

class VgrRuntimeError(VgrException):
    def __init__(self, tree, orig_exc):
        super().__init__(tree, orig_exc, *SSM.current)

class VgrExitingException(VgrException):
    """Raised when a statement has decided the application needs to exit"""

    EXIT_SUCCESS = 0
    EXIT_FAILED = 1

    def __init__(self, exit_code: int, statement: Tree, message: str=''):
        super().__init__(statement, Exception(message), *SSM.current)
        self.message = message.strip()
        self.exit_code = exit_code
        self.statement = statement

class VgrStatementAbort(VgrExitingException):
    """Raised by an Abort statement"""

    def __init__(self, statement: Tree, message):
        super().__init__(VgrExitingException.EXIT_FAILED, statement, message)

class VgrStatementAssert(VgrExitingException):
    """Raised by a failed Assert statement"""

    def __init__(self, statement: Tree, message):
        super().__init__(VgrExitingException.EXIT_FAILED, statement, message)

class BlockType(Enum):
    ALL_BLOCKS = auto() # Can break/continue any control context

class VgrFlowControlException(VgrException):
    def __init__(self, statement: Tree, msg: str, block_type: BlockType=BlockType.ALL_BLOCKS):
        super().__init__(statement, Exception(msg), *SSM.current)
        self._block_type = block_type

    def validate_for_block(self, block_types: BlockType) -> None:
        if self._block_type == BlockType.ALL_BLOCKS: return
        if isinstance(block_types, BlockType) and self._block_type == block_types: return
        if isinstance(block_types, tuple) and self._block_type in block_types: return
        raise VgrRuntimeError(self.node, ValueError('Type not compatible with surrounding loop')) from self

class VgrStatementBreak(VgrFlowControlException):
    """
    Thrown on a "break" to unwind the control block
    NB: root exception is for when it is used inappropriately
    """
    def __init__(self, statement: Tree, block_type: BlockType):
        super().__init__(statement, 'Misplaced Break', block_type)

class VgrStatementContinue(VgrFlowControlException):
    """
    Thrown on a "continue" to unwind the control block
    NB: root exception is for when it is used inappropriately
    """
    def __init__(self, statement: Tree, block_type: BlockType):
        super().__init__(statement, 'Misplaced Continue', block_type)

class VgrStatementReturn(VgrFlowControlException):
    """Raised when a returning a value from a function or exiting a procedure"""

    def __init__(self, return_value: Any, statement: Tree):
        super().__init__(statement, 'Misplaced Return')
        self.return_value = return_value
