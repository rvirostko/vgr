
from typing import Any
import ast
import re
import math

from lark import Lark, Tree, Token, Transformer, v_args

from app_exceptions import remember_terminals, StatementBreak, StatementConinue
from data_dict import DataDictionary
from dbg import print_tree
from dd_config import dd_set_statement, dd_clear_scratch, dd_path
from evaluate import bind_operations, eval_expr
from mathpak import poly_bool, poly_list
from redir import execute_open, execute_close, print_stderr
from src_mgr import SSM
from stmt_cflags import execute_debug, execute_echo, execute_verbose
from stmt_exit import execute_assert, execute_exit
from stmt_math import execute_add_to, execute_add_giving, execute_mul_by
from stmt_math import execute_sub_from, execute_sub_giving, execute_div_into, execute_div_by
from stmt_print import execute_exhibit, execute_print, execute_printf, execute_display_on
from stmt_select import execute_select
from stmt_set import execute_load_from, execute_set, execute_unset, execute_inc, execute_dec, execute_move_to, do_set, do_unset
from stmt_sort import execute_sort
from stmt_zip import execute_zip

def execute_break(_: DataDictionary, __: Tree) -> None:
    """Exits the current block of statements.

* Break [;]

Can be used with If, Unless, While, Until, and ForEach statements
"""
    raise StatementBreak()

def execute_continue(_: DataDictionary, __: Tree) -> None:
    """Causes the current loop to to start again.

* Continue [;]

"""
    raise StatementConinue()

def execute_pass(_: DataDictionary, __: Tree) -> None:
    """A placeholder for a statement.
* NOP [;]
* Pass [;]

A placeholder for a statement, such as during iterative development
which takes no action and has no side effects."""

def _exec_if_else(dd: DataDictionary, statement: Tree, desired_value: bool) -> None:
    if dd.echo:
        print_stderr(SSM.source_for(statement, statement.children[1]))
    if poly_bool(eval_expr(dd, bind_operations(statement.children[0]))) == desired_value:
        for s in statement.children[1:]:
            if s.data != 'else':
                dispatch_statement(dd, s)
    else:
        last = statement.children[-1]
        if last.data == 'else':
            for s in last.children:
                dispatch_statement(dd, s)

def execute_if(dd: DataDictionary, statement: Tree) -> None:
    """Conditionally execute a block of statements.

* If _expression_ [Then | :] _statement_... End [;]
* If _expression_ [Then | :] _statement_... Else [Do | :] _statement_... End [;]

If the expression evaluates to True the first block of statements is executed.
If it evaluates to False, the second block of statements, if provided, is executed.
"""
    _exec_if_else(dd, statement, True)

def execute_unless(dd: DataDictionary, statement: Tree) -> None:
    """Conditionally execute a block of statements.

* Unless _expression [Then | :] _statement_... End [;]

If the expression evaluates to False the block of statements is executed.
"""
    _exec_if_else(dd, statement, False)

def _exec_loop(dd: DataDictionary, statement: Tree, desired_value: bool) -> None:
    if dd.echo:
        print_stderr(SSM.source_for(statement, statement.children[1]))
    predicate = bind_operations(statement.children[0])
    while True:
        if poly_bool(eval_expr(dd, predicate)) != desired_value: return
        try:
            for s in statement.children[1:]: dispatch_statement(dd, s)
        except StatementBreak:
            return
        except StatementConinue:
            continue

def execute_while(dd: DataDictionary, statement: Tree) -> None:
    """Repeatedly execute a block of statements while a condition exists.

* While _expression_ [Do | :] _statement_... End [;]

As long as the expression evaluates to True, the block of statements is
repeatedly executed.
If a Break statement is encountered, looping ends regardless of the
expression's value. If a Continue statement is encountered, statements
following it are skipped, and the expression is checked again.
    """
    _exec_loop(dd, statement, True)

def execute_until(dd: DataDictionary, statement: Tree) -> None:
    """Repeatedly execute a block of statements until a condition is reached.

* Until _expression_ [Do | :] _statement_... End [;]

The block of statements is executed until the expression evaluates to True.
If a Break statement is encountered, looping ends regardless of the
expression's value. If a Continue statement is encountered, statements
following it are skipped, and the expression is checked again.
"""
    _exec_loop(dd, statement, False)

def execute_foreach(dd: DataDictionary, statement: Tree) -> None:
    """Iterate over a set of values.

* ForEach _variable_ In _expression_ [Do | :] _statement_.. End [;]

If expression is a single value, non-_None_ value, the statements are executed
exactly once. If a list, the statements are executed once for each item,
including items that are _None_, and if a dictionary, the statements
are executed once for each key/value pair.

If a Break statement is encountered, iteration ends regardless of the
number of items remaining. If a Continue statement is encountered, statements
following it are skipped, and the loop continues with the next item.
"""
    if dd.echo:
        print_stderr(SSM.source_for(statement, statement.children[2]))
    path = dd_path(statement.children[0])
    collection = poly_list(eval_expr(dd, bind_operations(statement.children[1])))
    if collection is not None:
        try:
            for value in collection:
                do_set(dd, value, *path)
                try:
                    for s in statement.children[2:]: dispatch_statement(dd, s)
                except StatementBreak:
                    return
                except StatementConinue:
                    continue
        finally:
            do_unset(dd, *path)

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

SIMPLE_STATEMENT_HANDLERS = {
    'add_giving': execute_add_giving,
    'add_to': execute_add_to,
    'assert': execute_assert,
    'break': execute_break,
    'close': execute_close,
    'continue': execute_continue,
    'debug': execute_debug,
    'dec': execute_dec,
    'display_on': execute_display_on,
    'div_by': execute_div_by,
    'div_into': execute_div_into,
    'echo': execute_echo,
    'exhibit': execute_exhibit,
    'exit': execute_exit,
    'inc': execute_inc,
    'load_from': execute_load_from,
    'move_to': execute_move_to,
    'mul_by': execute_mul_by,
    'open': execute_open,
    'pass': execute_pass,
    'print': execute_print,
    'printf': execute_printf,
    'set': execute_set,
    'sort': execute_sort,
    'sub_from': execute_sub_from,
    'sub_giving': execute_sub_giving,
    'unset': execute_unset,
    'verbose': execute_verbose,
    'zip': execute_zip,
}

X_STATEMENT_HANDLERS = {
    'foreach': execute_foreach,
    'if': execute_if,
    'select': execute_select,
    'unless': execute_unless,
    'until': execute_until,
    'while': execute_while,
}

def remove_comments(input_text: str) -> str:
    """Removes comments but preserves lines for Lark metadata accuracy."""
    # We do Hash, C-style, and SQL style
    return re.sub(r'(^|;)[ \t]*(#|//|--).*$', r'\1\n', input_text, flags=re.MULTILINE)

def execute_statements(parser: Lark, dd: DataDictionary, statement_text: str, source: str=None) -> None:
    statement_text = remove_comments(statement_text)
    if not statement_text or statement_text.isspace(): return
    remember_terminals(parser)
    SSM.set_statement(statement_text, source)
    statements: Tree = parser.parse(statement_text)
    for statement in statements.children:
        try:
            dispatch_statement(dd, statement)
        except StatementBreak:
            if dd.verbose: print_stderr('Break used outside control statement; ignored')
        except StatementConinue:
            if dd.verbose: print_stderr('Continue used outside control statement; ignored')

def dispatch_statement(dd: DataDictionary, statement: Tree) -> None:
    text = SSM.source_for(statement)
    dd_set_statement(dd, text)
    statement = ConstantsNormalizer().transform(statement)
    statement = VarRefOptimizer().transform(statement)
    handler = SIMPLE_STATEMENT_HANDLERS.get(statement.data)
    if handler:
        statement = bind_operations(statement)
        if dd.echo: print_stderr(text)
    else:
        handler = X_STATEMENT_HANDLERS.get(statement.data)
        # NB: these statements need to do their own bind
        #     and decide what to do for "echo"
    if dd.debug: print_tree(statement)
    try:
        if handler: handler(dd, statement)
        else: raise NotImplementedError(f'No handler established for {statement.data}') #SNO
    finally:
        dd_clear_scratch(dd)
