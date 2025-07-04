
from contextvars import ContextVar
from pathlib import Path
from typing import Any
import ast
import math
import os
import re

from lark import Lark, Tree, Token, Transformer, v_args

from app_exceptions import (
    remember_terminals,
    VgrException,
    VgrRuntimeError,
    VgrStatementBreak,
    VgrStatementContinue,
)
from data_dict import DataDictionary
from dbg import print_tree
from dd_config import (
    dd_clear_scratch,
    dd_pop_source,
    dd_push_source,
    dd_set_statement,
    do_set,
    do_unset,
)
from evaluate import bind_operations, eval_expr, eval_filename_expr, var_name_path
from mathpak import poly_bool, poly_list, poly_int
from redir import execute_open, execute_close, print_stderr, print_stdout
from src_mgr import SSM
from stmt_cflags import execute_debug, execute_echo, execute_verbose
from stmt_exit import execute_assert, execute_exit
from stmt_list import (
    execute_list_append,
    execute_list_insert,
    execute_list_prepend,
    execute_list_remove_first,
    execute_list_remove_last,
    execute_list_remove,
)
from stmt_log import execute_log, execute_log_setlevel
from stmt_misc import execute_sleep
from stmt_print import execute_print, execute_printf
from stmt_select import execute_select
from stmt_set import (
    execute_load_from,
    execute_reset,
    execute_set_in_place,
    execute_set,
    execute_unset,
)
from stmt_sort import execute_sort
from stmt_zip import execute_zip
from tags import control_statement

def execute_source(dd: DataDictionary, statement: Tree) -> None:
    """
**Execute statements stored in a file**

* Source _expression_ [, _expression_]... [;]

Each _expression_ is evaluated to a file name. Statements in the file
are executed, inheriting the current state of all variable and
input/output redirection.
"""
    for child in statement.children:
        file = eval_filename_expr(dd, child, True)
        if file is None or len(file) == 0: continue
        path = Path(file)
        if not path.exists():
            raise VgrRuntimeError(child, Exception(f'File {repr(file)} not found'))
        if not path.is_file():
            raise VgrRuntimeError(child, Exception(f'{repr(file)} does not reference a file'))
        if not os.access(path, os.R_OK):
            raise VgrRuntimeError(child, Exception(f'File {repr(file)} not readable'))
        try:
            statements = None
            with open(path, 'r', encoding='utf-8-sig') as f:
                statements = f.read()
            execute_statements(None, dd, statements, file)
        except (OSError, IOError) as e:
            raise VgrRuntimeError(child, e) from e

def execute_break(_: DataDictionary, statement: Tree) -> None:
    """
**Exits the current block of statements**

* Break [;]

Can be used with If, Unless, While, Until, and ForEach statements
"""
    raise VgrStatementBreak(statement)

def execute_continue(_: DataDictionary, statement: Tree) -> None:
    """
**Causes the current loop to to start again**

* Continue [;]

"""
    raise VgrStatementContinue(statement)

def execute_pass(_: DataDictionary, __: Tree) -> None:
    """
**A placeholder for a statement**

* NOP [;]
* Pass [;]

A placeholder for a statement, which takes no action and has no side effects."""

def exec_if_else(dd: DataDictionary, statement: Tree, desired_value: bool) -> None:
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

@control_statement
def execute_if(dd: DataDictionary, statement: Tree) -> None:
    """
**Conditionally execute a block of statements**

* If _expression_ [Then | Do | :]
    _statement_...
  End [;]
* If _expression_ [Then | Do | :]
    _statement_...
  Else [Do | :]
    _statement_...
  End [;]

If the expression evaluates to True the first block of statements is executed.
If it evaluates to False, the second block of statements, if provided, is executed.
"""
    exec_if_else(dd, statement, True)

@control_statement
def execute_unless(dd: DataDictionary, statement: Tree) -> None:
    """
**Conditionally execute a block of statements**

* Unless _expression [Then | :] _statement_... End [;]

If the expression evaluates to _False_ the block of statements is executed.
"""
    exec_if_else(dd, statement, False)

def exec_loop(dd: DataDictionary, statement: Tree, desired_value: bool) -> None:
    """Internal implemenation for loops with a predicate"""
    if dd.echo:
        print_stderr(SSM.source_for(statement, statement.children[1]))
    predicate = bind_operations(statement.children[0])
    while True:
        if poly_bool(eval_expr(dd, predicate)) != desired_value: return
        try:
            for s in statement.children[1:]: dispatch_statement(dd, s)
        except VgrStatementBreak:
            return
        except VgrStatementContinue:
            continue

def exec_repeat(dd: DataDictionary, statement: Tree) -> None:
    """Internal implementation for loops with a fixed count"""
    if dd.echo:
        print_stderr(SSM.source_for(statement, statement.children[1]))
    expr = bind_operations(statement.children[0])
    counter = poly_int(eval_expr(dd, expr))
    if isinstance(counter, (int, float)):
        counter = math.floor(counter)
        while counter > 0:
            try:
                for s in statement.children[1:]: dispatch_statement(dd, s)
            except VgrStatementBreak:
                return
            except VgrStatementContinue:
                pass
            counter -= 1

@control_statement
def execute_while(dd: DataDictionary, statement: Tree) -> None:
    """
**Repeatedly execute a block of statements while a condition exists**

* While _expression_ [Do | :]
    _statement_...
  End [;]

As long as the expression evaluates to _True_, the block of statements is
repeatedly executed.
If a Break statement is encountered, looping ends regardless of the
expression's value. If a Continue statement is encountered, statements
following it are skipped, and the expression is checked again.
"""
    exec_loop(dd, statement, True)

@control_statement
def execute_until(dd: DataDictionary, statement: Tree) -> None:
    """
**Repeatedly execute a block of statements until a condition is reached**

* Until _expression_ [Do | :]
    _statement_...
  End [;]

The block of statements is executed until the expression evaluates to _True_.
If a Break statement is encountered, looping ends regardless of the
expression's value. If a Continue statement is encountered, statements
following it are skipped, and the expression is checked again.
"""
    exec_loop(dd, statement, False)

@control_statement
def execute_repeat(dd: DataDictionary, statement: Tree) -> None:
    """
**Execute a block of statements a fixed number of times**

* Repeat _expression_ [Do | :]
    _statement_...
  End [;]

The block of statements is executed the given number of times.
The expression is evaluated an converted to an integer, rounding down.
For any statements to execute, the value must be greater than or equal to one.
If a Break statement is encountered, looping ends regardless of the
expression's value. If a Continue statement is encountered, statements
following it are skipped, and looping continues.
"""
    exec_repeat(dd, statement)

@control_statement
def execute_foreach(dd: DataDictionary, statement: Tree) -> None:
    """
**Iterate over a set of values**

* ForEach _variable_ In _expression_ [Do | :]
    _statement_...
  End [;]

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
    path = var_name_path(statement.children[0])
    collection = poly_list(eval_expr(dd, bind_operations(statement.children[1])))
    if collection is not None:
        try:
            for value in collection:
                do_set(dd, value, *path)
                try:
                    for s in statement.children[2:]: dispatch_statement(dd, s)
                except VgrStatementBreak:
                    return
                except VgrStatementContinue:
                    continue
        finally:
            do_unset(dd, *path)

# pylint: disable=invalid-name
# disabled because we MUST have methods named the same as the tokens
# and the tokens MUST have uppercase names
class ConstantsNormalizer(Transformer):

    SUPERSCRIPT_TRANSLATION = str.maketrans({
        '⁰': '0',
        '¹': '1',
        '²': '2',
        '³': '3',
        '⁴': '4',
        '⁵': '5',
        '⁶': '6',
        '⁷': '7',
        '⁸': '8',
        '⁹': '9',
        '⁺': '+',
        '⁻': '-',
        '·': '.',
        '⁽': '',     # remove left paren
        '⁾': '',     # remove right paren
    })

    def STRING(self, token):
        # Removes the quoting and interprets escape sequences
        token.value = ast.literal_eval(token.value)
        return token
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
    def SUPERSCRIPT_FLOAT(self, token):
        val = float(token.value.translate(self.SUPERSCRIPT_TRANSLATION))
        is_float = '·' in token.value
        return self._new_token(token, 'FLOAT' if is_float else 'INT', val if is_float else int(val))
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

# NB: Extension may add items to this list,
#     but they can't replace existing ones
STATEMENT_HANDLERS = {
    'assert':       execute_assert,
    'break':        execute_break,
    'close':        execute_close,
    'continue':     execute_continue,
    'debug':        execute_debug,
    'echo':         execute_echo,
    'exit':         execute_exit,
    'foreach':      execute_foreach,
    'if':           execute_if,
    'load_from':    execute_load_from,
    'open':         execute_open,
    'pass':         execute_pass,
    'print':        execute_print,
    'printf':       execute_printf,
    'repeat':       execute_repeat,
    'select':       execute_select,
    'reset':        execute_reset,
    'set':          execute_set,
    'set_in_place': execute_set_in_place,
    'sleep':        execute_sleep,
    'sort':         execute_sort,
    'source':       execute_source,
    'unless':       execute_unless,
    'unset':        execute_unset,
    'until':        execute_until,
    'verbose':      execute_verbose,
    'while':        execute_while,
    'zip':          execute_zip,
    'log':          execute_log,
    'log_setlevel': execute_log_setlevel,
    'list_append':  execute_list_append,
    'list_prepend': execute_list_prepend,
    'list_insert':  execute_list_insert,
    'list_remove':  execute_list_remove,
    'list_remove_first': execute_list_remove_first,
    'list_remove_last': execute_list_remove_last,
}

def remove_comments(input_text: str) -> str:
    """Removes comments but preserves lines for Lark metadata accuracy."""
    # We do Hash, C-style, and SQL style
    return re.sub(r'(^|;)[ \t]*(#|//|--).*$', r'\1', input_text, flags=re.MULTILINE)

_parser_context: ContextVar = ContextVar('vgr_parser_context', default=None)

def execute_statements(parser: Lark, dd: DataDictionary, statement_text: str, source: str) -> None:
    try:
        dd_push_source(dd, source)
        statement_text = remove_comments(statement_text)
        if not statement_text or statement_text.isspace(): return
        _parser = _parser_context.get() if parser is None else parser
        remember_terminals(_parser)
        SSM.set_statement(statement_text, source)
        statements: Tree = _parser.parse(statement_text)
        for statement in statements.children:
            try:
                if parser is not None: _parser_context.set(parser)
                dispatch_statement(dd, statement)
            finally:
                if parser is not None: _parser_context.set(None)
    finally:
        dd_pop_source(dd)

def dispatch_statement(dd: DataDictionary, statement: Tree) -> None:
    text = SSM.source_for(statement)
    dd_set_statement(dd, text)
    statement = ConstantsNormalizer().transform(statement)
    statement = VarRefOptimizer().transform(statement)
    if dd.debug: print_tree(statement)
    handler = STATEMENT_HANDLERS.get(statement.data)
    if handler:
        if not getattr(handler, "_is_control_statement", False):
            # Simple statements: those that don't have nested
            # statements, ones that don't interate, or have complex requirements
            # Other statements need to handle binding
            # and decide what to do for echo
            statement = bind_operations(statement)
            if dd.echo: print_stderr(text)
        try:
            handler(dd, statement)
        except VgrException as e:
            raise e
        except KeyboardInterrupt as e:
            print_stdout('')
            raise VgrRuntimeError(statement, e) from e
        except Exception as e:
            raise VgrRuntimeError(statement, e) from e
        finally:
            dd_clear_scratch(dd)
    else:
        raise VgrRuntimeError(statement, NotImplementedError(f'No handler established for {statement.data}')) #SNO
