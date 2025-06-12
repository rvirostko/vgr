import sys
import traceback

from lark import Lark, Tree, Token, exceptions
from lark.exceptions import VisitError

from src_mgr import SSM

class VgrException(VisitError):
    def __init__(self, node, orig_exc, source_text):
        if isinstance(node, Tree):
            rule = getattr(node, 'data', '<unknown>')
            meta = node.meta
        elif isinstance(node, Token):
            rule = f'token:{node.type}'
            meta = node
        else:
            raise TypeError(f"Expected Tree or Token, got {type(node)}")
        super().__init__(rule, node, orig_exc)
        self.line = getattr(meta, 'line', None)
        self.column = getattr(meta, 'column', None)
        self._source_text = source_text

    def get_context(self, span=40):
        if not self._source_text or self.line is None or self.column is None:
            return ""
        lines = self._source_text.splitlines()
        if not (0 < self.line <= len(lines)):
            return ""
        line_str = lines[self.line - 1]
        # Strip leading whitespace and adjust column
        leading_ws = len(line_str) - len(line_str.lstrip())
        trimmed_line = line_str.lstrip()
        adjusted_column = max(self.column - leading_ws, 1)
        # Compute start and end positions for span truncation
        start = max(0, adjusted_column - 1 - span)
        end = adjusted_column - 1 + span
        snippet = trimmed_line[start:end]
        pointer_line = ' ' * (adjusted_column - 1 - start) + '^'
        return f"{snippet}\n{pointer_line}"

    def __str__(self):
        context = self.get_context()
        exc_txt = "Interrupted" if isinstance(self.orig_exc, KeyboardInterrupt) else str(self.orig_exc).strip()
        location = f'{exc_txt}{" at" if exc_txt else "At"} line {self.line}, column {self.column}'
        return f'{context}\n{location}' if context else location

class VgrRuntimeError(VgrException):
    def __init__(self, tree, orig_exc):
        super().__init__(tree, orig_exc, SSM.statement_text())

class VgrExitingException(VgrException):
    """Raised when a statement has decided the application needs to exit"""

    EXIT_SUCCESS = 0
    EXIT_FAILED = 1

    def __init__(self, exit_code: int, statement: Tree, message: str=''):
        super().__init__(statement, Exception(message), SSM.statement_text())
        self.message = message.strip()
        self.exit_code = exit_code
        self.statement = statement

class VgrStatementBreak(VgrException):
    """
    Thrown on a "break" to unwind the control block
    NB: root exception is for when it is used inappropriately
    """
    def __init__(self, statement: Tree):
        super().__init__(statement, Exception('Break used outside control statement'), SSM.statement_text())

class VgrStatementContinue(VgrException):
    """
    Thrown on a "continue" to unwind the control block
    NB: root exception is for when it is used inappropriately
    """
    def __init__(self, statement: Tree):
        super().__init__(statement, Exception('Continue used outside control statement'), SSM.statement_text())

# List of tokens that we don't try to translate in exceptions
_TOKEN_PASS = ('NAME',)

_TERMINALS = []

def remember_terminals(parser: Lark) -> None:
    _TERMINALS.clear()
    _TERMINALS.extend(parser.parser.lexer_conf.terminals)

def token_value(token_name) -> str:
    """Lark tokens to their values for error display"""
    if token_name not in _TOKEN_PASS:
        for terminal in _TERMINALS:
            # Get the regex pattern or literal value
            if terminal.name == token_name: return repr(terminal.pattern.value)
    # Fallback to token name if no mapping is found
    return token_name

def get_expected(e: Exception) -> str:
    rc = ''
    if hasattr(e, 'token') and e.token:
        rc += token_value(e.token) + 'unexpected.'
    if hasattr(e, 'expected') and e.expected:
        expected = e.expected
        if not isinstance(expected, (list, tuple, set)): expected = [expected]
        if expected:
            rc = '\nExpected '
            values = [token_value(tok) for tok in sorted(expected)]
            if len(values) == 1: rc += values[0]
            elif len(values) == 2: rc += values[0] + ' or ' + values[1]
            else: rc += ', '.join(values[:-1]) + ', or ' + values[-1]
            rc += '.'
    return rc

_ERROR_XLATE = {
    exceptions.UnexpectedInput: "Syntax error",
    exceptions.UnexpectedToken: "Unexpected input",
    exceptions.UnexpectedEOF: "Unexpected End-of-File",
    exceptions.UnexpectedCharacters: "Unexpected character",
    exceptions.ParseError: "Error",
    ValueError: "Error"
}

def exception_type(e: Exception) -> str:
    """
    Convert the exception type into a human-readable string based on a dictionary.
    If no custom message is found, fallback to the default class name.
    """
    etype = type(e)
    return _ERROR_XLATE.get(etype, etype.__name__)

def format_generic_exception(e: Exception) -> str:
    try:
        return exception_type(e) + ': ' + str(e)
    except (TypeError, ValueError) as e2:
        traceback.print_exc(file=sys.stderr)
        print(e2, file=sys.stderr)
        return str(e)

def format_unexpected_input(e: exceptions.UnexpectedInput) -> str:
    try:
        # TODO get file name if applicable
        return f'{e.get_context(SSM.statement_text())}{exception_type(e)} at line {e.line}, column {e.column}.{get_expected(e)}'
    except (TypeError, ValueError) as e2:
        traceback.print_exc(file=sys.stderr)
        print(e2, file=sys.stderr)
        return str(e)
