#! /usr/bin/env python3

from lark import Tree

class ExitingException(Exception):
    """Raised when a statement has decided the application needs to exit"""
    def __init__(self, exit_code: int, statement: Tree, message: str=''):
        super().__init__(message)
        self.message = message.strip()
        self.exit_code = exit_code
        self.statement = statement
