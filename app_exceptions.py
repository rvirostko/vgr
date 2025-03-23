#! /usr/bin/env python3

import sys
import traceback

from lark import Lark, Tree, exceptions

from src_mgr import SSM

class ExitingException(Exception):
    """Raised when a statement has decided the application needs to exit"""

    EXIT_SUCCESS = 0
    EXIT_FAILED = 1

    def __init__(self, exit_code: int, statement: Tree, message: str=''):
        super().__init__(message)
        self.message = message.strip()
        self.exit_code = exit_code
        self.statement = statement


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
