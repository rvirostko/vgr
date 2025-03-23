
from typing import Any
import ast
import re
import math

from lark import Lark, Tree, Token, Transformer, v_args

from app_exceptions import remember_terminals
from data_dict import DataDictionary
from dd_config import dd_set_statement
from evaluate import bind_operations
from redir import print_stderr, execute_open, execute_close
from src_mgr import SSM
from stmt_cflags import execute_debug, execute_echo, execute_verbose
from stmt_exit import execute_assert, execute_exit
from stmt_print import execute_exhibit, execute_print, execute_printf
from stmt_select import execute_select
from stmt_set import execute_load_from, execute_set
from stmt_zip import execute_zip
from dbg import print_tree

# pylint: disable=invalid-name
# disabled because we MUST have methods named the same as the tokens
# and the tokens MUST have uppercase names
class ConstantsNormalizer(Transformer):
    def ESCAPED_STRING(self, token):
        # Removes the quoting and interprets escape sequences
        return self._new_token(token, "STRING", ast.literal_eval(token.value))
    def TRUE(self, token): return self._new_token(token, token.type, True)
    def FALSE(self, token): return self._new_token(token, token.type, False)
    def NONE(self, token): return self._new_token(token, 'NONE', None)
    def INF(self, token): return self._new_token(token, 'FLOAT', math.inf)
    def NAN(self, token): return self._new_token(token, 'FLOAT', math.nan)
    def DEC_NUMBER(self, token): return self._to_int(token, 10)
    def HEX_NUMBER(self, token): return self._to_int(token, 16)
    def OCT_NUMBER(self, token): return self._to_int(token, 8)
    def BIN_NUMBER(self, token): return self._to_int(token, 2)
    def FLOAT_NUMBER(self, token): return self._new_token(token, 'FLOAT', float(token.value))
    def _to_int(self, token, base: int): return self._new_token(token, 'INT', int(token.value, base))
    def _new_token(self, token, new_type: str, value: Any):
        return Token(new_type, value, token.start_pos, token.line, token.column,
                     token.end_line, token.end_column, token.end_pos)
# pylint: enable=invalid-name

@v_args(tree=True)
class VarRefOptimizer(Transformer):
    """
    Replaces deref(var_ref(NAME,...), NAME2) -> var_ref(NAME,...,NAME2)
    This eliminates any derefs that are dotted paths from the root
    """
    def deref(self, tree):
        if len(tree.children) == 2:
            c1, c2 = tree.children
            if isinstance(c1, Tree) and c1.data == 'var_ref':
                if isinstance(c2, Token) and c2.type == 'NAME':
                    c1.children.append(c2)
                    tree = c1
        return tree

STATEMENT_HANDLERS = {
    'assert': execute_assert,
    'close': execute_close,
    'debug': execute_debug,
    'echo': execute_echo,
    'exhibit': execute_exhibit,
    'exit': execute_exit,
    'load_from': execute_load_from,
    'open': execute_open,
    'print': execute_print,
    'printf': execute_printf,
    'select': execute_select,
    'set': execute_set,
    'verbose': execute_verbose,
    'zip': execute_zip,
}

def remove_comments(input_text: str) -> str:
    """Removes comments but preserves lines for Lark metadata accuracy."""
    # We do Hash, C-style, and SQL style
    return re.sub(r'(^|;)[ \t]*(#|//|--).*$', r'\1\n', input_text, flags=re.MULTILINE)

def execute_statements(parser: Lark, dd: DataDictionary, statement_text: str, source: str=None) -> None:
    statement_text = remove_comments(statement_text)
    if not statement_text or statement_text.isspace(): return
    remember_terminals(parser)
    statements: Tree = parser.parse(statement_text)
    SSM.set_statement(statement_text, source)
    for statement in statements.children:
        text = statement_text[statement.meta.start_pos : statement.meta.end_pos]
        dd_set_statement(dd, text)
        handler = STATEMENT_HANDLERS.get(statement.data)
        if not handler: raise NotImplementedError(f'No handler established for {statement.data}')
        statement = ConstantsNormalizer().transform(statement)
        statement = VarRefOptimizer().transform(statement)
        statement = bind_operations(statement)
        if dd.is_echo(): print_stderr(text)
        if dd.is_debug(): print_tree(statement)
        handler(dd, statement)
