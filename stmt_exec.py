
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable
import ast
import math
import os

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
    _VGR_PREFIX,
    do_set,
    do_unset,
)
from evaluate import bind_operations, eval_expr, eval_expr_or_const, eval_filename_expr, var_name_path
from exec_context import ExecContext
from functions import build_dict
from mathpak import (
    bound_ops,
    poly_int,
    poly_list,
    poly_true,
)
from redir import execute_open, execute_close, print_stderr, print_stdout
from src_mgr import SSM
from stmt_cflags import execute_debug, execute_echo, execute_verbose
from stmt_choose import execute_choose, execute_choose_using
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
    execute_swap,
    execute_unset,
)
from stmt_sort import execute_sort
from stmt_zip import execute_zip
from tags import control_statement

@bound_ops("Source")
def execute_source(ctx: ExecContext, statement: Tree) -> None:
    """
**Execute statements stored in a file**

* Source _expression_ [, _expression_]... [;]

Each _expression_ is evaluated to a file name. Statements in the file
are executed, inheriting the current state of all variable and
input/output redirection.
"""
    for child in statement.children:
        file = eval_filename_expr(ctx.dd, child, True)
        if file is None or len(file) == 0: continue
        path = Path(file)
        if not path.exists():
            raise VgrRuntimeError(child, Exception(f'File {file!r} not found'))
        if not path.is_file():
            raise VgrRuntimeError(child, Exception(f'{file!r} does not reference a file'))
        if not os.access(path, os.R_OK):
            raise VgrRuntimeError(child, Exception(f'File {file!r} not readable'))
        try:
            statements = None
            with open(path, 'r', encoding='utf-8-sig') as f:
                statements = f.read()
            ctx.execute_statements(statements, file)
        except (OSError, IOError) as e:
            raise VgrRuntimeError(child, e) from e

@bound_ops("Break")
def execute_break(_: ExecContext, statement: Tree) -> None:
    """
**Exits the current block of statements**

* Break [;]

Can be used with If, Unless, While, Until, and ForEach statements
"""
    raise VgrStatementBreak(statement)

@bound_ops("Continue")
def execute_continue(_: ExecContext, statement: Tree) -> None:
    """
**Causes the current loop to start again**

* Continue [;]

"""
    raise VgrStatementContinue(statement)

@bound_ops("NOP", "Pass")
def execute_pass(_: ExecContext, __: Tree) -> None:
    """
**A placeholder for a statement**

* NOP [;]
* Pass [;]

A placeholder for a statement, which takes no action and has no side effects.
"""

def exec_if_else(ctx: ExecContext, statement: Tree, desired_value: bool) -> None:
    ctx.echo_source(statement, statement.children[1])
    has_else = statement.children[-1].data == 'else'
    if poly_true(ctx.eval_expr(bind_operations(statement.children[0]))) == desired_value:
        # Execute true side: skips the expression and the else if present
        ctx.dispatch_statements(statement.children[1:-1 if has_else else None])
    else:
        # Execute false side: the "else" is always the last child
        # and its children are the statements to execute
        if has_else: ctx.dispatch_statements(statement.children[-1].children)

@control_statement
@bound_ops("If-Then", "If-Else")
def execute_if(ctx: ExecContext, statement: Tree) -> None:
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
    exec_if_else(ctx, statement, True)

@control_statement
@bound_ops("Unless")
def execute_unless(ctx: ExecContext, statement: Tree) -> None:
    """
**Conditionally execute a block of statements**

* Unless _expression_ [Then | :] _statement_... End [;]

If the expression evaluates to _False_ the block of statements is executed.
"""
    exec_if_else(ctx, statement, False)

def exec_loop(ctx: ExecContext, statement: Tree, desired_value: bool) -> None:
    """Internal implemenation for loops with a predicate"""
    ctx.echo_source(statement, statement.children[1])
    predicate = bind_operations(statement.children[0])
    while True:
        if poly_true(ctx.eval_expr(predicate)) != desired_value: return
        try:
            ctx.dispatch_statements(statement.children[1:])
        except VgrStatementBreak:
            return
        except VgrStatementContinue:
            continue

def exec_repeat(ctx: ExecContext, statement: Tree) -> None:
    """Internal implementation for loops with a fixed count"""
    ctx.echo_source(statement, statement.children[1])
    counter = poly_int(ctx.eval_expr(bind_operations(statement.children[0])))
    if isinstance(counter, (int, float)):
        counter = math.floor(counter)
        while counter > 0:
            try:
                ctx.dispatch_statements(statement.children[1:])
            except VgrStatementBreak:
                return
            except VgrStatementContinue:
                pass
            counter -= 1

@control_statement
@bound_ops("While")
def execute_while(ctx: ExecContext, statement: Tree) -> None:
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
    exec_loop(ctx, statement, True)

@control_statement
@bound_ops("Until")
def execute_until(ctx: ExecContext, statement: Tree) -> None:
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
    exec_loop(ctx, statement, False)

@control_statement
@bound_ops("Repeat")
def execute_repeat(ctx: ExecContext, statement: Tree) -> None:
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
    exec_repeat(ctx, statement)

@control_statement
@bound_ops("ForEach")
def execute_foreach(ctx: ExecContext, statement: Tree) -> None:
    """
**Iterate over a list of values**

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
    ctx.echo_source(statement, statement.children[2])
    path = var_name_path(statement.children[0])
    collection = poly_list(ctx.eval_expr(bind_operations(statement.children[1])))
    if collection is not None:
        try:
            for value in collection:
                do_set(ctx.dd, value, *path)
                try:
                    ctx.dispatch_statements(statement.children[2:])
                except VgrStatementBreak:
                    return
                except VgrStatementContinue:
                    continue
        finally:
            do_unset(ctx.dd, *path)

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

    @v_args(tree=True)
    def array(self, tree: Tree):
        items = tree.children
        if not items:
            meta = tree.meta
            return Token('CONST', [], meta.start_pos, meta.line, meta.column,
                         meta.end_line, meta.end_column, meta.end_pos)
        if all(isinstance(child, Token) and child.type == "CONST" for child in items):
            first, last = tree.children[0], tree.children[-1]
            return Token('CONST', [child.value for child in items],
                        first.start_pos, first.line, first.column,
                        last.end_line, last.end_column, last.end_pos)
        return tree

    @v_args(tree=True)
    def dict(self, tree: Tree):
        items = tree.children
        if not items:
            meta = tree.meta
            return Token('CONST', {}, meta.start_pos, meta.line, meta.column,
                         meta.end_line, meta.end_column, meta.end_pos)
        if all(isinstance(child, Token) and child.type == "CONST" for child in items):
            first, last = tree.children[0], tree.children[-1]
            return Token('CONST', build_dict(*[child.value for child in items]),
                        first.start_pos, first.line, first.column,
                        last.end_line, last.end_column, last.end_pos)
        return tree

    def STRING(self, token):
        try:
            # Removes the quoting and interprets escape sequences
            return self._const_token(token, ast.literal_eval(self.normalize_outer_quotes(token.value)))
        except SyntaxError as e:
            raise VgrRuntimeError(token, ValueError(str(e.msg).strip())) from e

    @v_args(tree=True)
    def vtrue(self, tree: Tree): return self._const_tree(tree, True)

    @v_args(tree=True)
    def vfalse(self, tree: Tree): return self._const_tree(tree, False)

    @v_args(tree=True)
    def vnone(self, tree: Tree): return self._const_tree(tree, None)

    @v_args(tree=True)
    def vinf(self, tree: Tree): return self._const_tree(tree, math.inf)

    @v_args(tree=True)
    def vnan(self, tree: Tree): return self._const_tree(tree, math.nan)

    def DEC_NUMBER(self, token): return self._to_int(token, 10)
    def HEX_NUMBER(self, token): return self._to_int(token, 16)
    def OCT_NUMBER(self, token): return self._to_int(token, 8)
    def BIN_NUMBER(self, token): return self._to_int(token, 2)
    def FLOAT_NUMBER(self, token): return self._const_token(token, float(token.value))
    def SUPERSCRIPT_FLOAT(self, token):
        val = float(token.value.translate(self.SUPERSCRIPT_TRANSLATION))
        return self._const_token(token, val if '·' in token.value else int(val))
    def _to_int(self, token, base: int): return self._const_token(token, int(token.value, base))

    def _const_token(self, token, value: Any):
        """The token is replaced by a CONST value"""
        return Token.new_borrow_pos('CONST', value, token)

    def _const_tree(self, tree: Tree, value: Any):
        """The tree is replaced by a CONST value"""
        meta = tree.meta
        return Token('CONST', value,
                     meta.start_pos, meta.line, meta.column,
                     meta.end_line, meta.end_column, meta.end_pos)


    def normalize_outer_quotes(self, s: str) -> str:
        """Fixes up typographic quotes from text pasted in from MS products like Word"""
        if s[0] in 'Rr':
            prefix = s[0]
            open_quote = s[1]
        else:
            prefix = ''
            open_quote = s[0]
        # the string is clean
        if open_quote in ('"', "'"): return s
        if prefix: s = s[1:]
        close_quote = s[-1]
        # Typographic single quotes
        if open_quote == '\u2018' and close_quote == '\u2019': return prefix + "'" + s[1:-1] + "'"
        # Typographic double quotes
        if open_quote == '\u201C' and close_quote == '\u201D': return prefix + '"' + s[1:-1] + '"'
        return prefix + s
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
    'choose':       execute_choose,
    'choose_using': execute_choose_using,
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
    'swap':         execute_swap,
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

@lru_cache
def get_statement_entries() -> list:
    entries = {}
    for _, func in STATEMENT_HANDLERS.items():
        # See mathpak/common for the bound_ops decorator
        if hasattr(func, 'bound_ops'):
            for op in func.bound_ops:
                entries[op] = (func, op.lower().replace(' ', ''), (func.__doc__ or '').lower())
    return entries

class DefaultExecContext(ExecContext):
    _SOURCE_STACK_PATH = (_VGR_PREFIX, 'source')
    _STATEMENT_PATH = (_VGR_PREFIX, 'statement')

    def __init__(self, parser: Lark, dd: DataDictionary):
        super().__init__(parser, dd)
        self.set_var('', *self._STATEMENT_PATH)
        self.set_var([], *self._SOURCE_STACK_PATH)

    def get_var(self, *path: str) -> Any: return self.dd.get_var(*path)
    def set_var(self, data: Any, /, *path: str) -> Any: return self.dd.set_var(data, *path)

    def get_var_user(self, *path: str) -> Any: return self.dd.get_var_user(*path)
    def set_var_user(self, data: Any, /, *path: str): return self.dd.set_var_user(data, *path)

    def eval_expr(self, expr: Any) -> Any: return eval_expr(self.dd, expr)
    def eval_expr_or_const(self, expr: Any) -> Any: return eval_expr_or_const(self.dd, expr)

    def echo_source(self, tree, end_tree = None):
        if self.dd.echo: print_stderr((SSM.source_for(tree, end_tree) or '').strip())

    def print_verbose(self, *args, **kwargs) -> None:
        if self.dd.verbose: print_stderr(*args, **kwargs)

    def execute_statements(self, statement_text: str, origin: str) -> None:
        """Parse the text and execute the resulting statements"""
        if statement_text and not statement_text.isspace():
            prev_statement = SSM.statement_text()
            prev_origin = SSM.origin()
            SSM.set_statement(statement_text, origin)
            try:
                self._push_source(origin)
                self.dispatch_statements(self._parser.parse(statement_text).children)
                # We only restore these if everything worked: otherwise we loose
                # the source that an exception may need
                SSM.set_statement(prev_statement, prev_origin)
            finally:
                self._pop_source()

    def dispatch_statements(self, statements: Iterable[Tree]) -> None:
        """Given a sequence of parsed statements dispatch them to their handler"""
        for statement in statements:
            self.set_var(SSM.source_for(statement), *self._STATEMENT_PATH)
            statement = ConstantsNormalizer().transform(statement)
            statement = VarRefOptimizer().transform(statement)
            if self.dd.debug: print_tree(statement)
            handler = STATEMENT_HANDLERS.get(statement.data)
            if not handler:
                raise VgrRuntimeError(statement, NotImplementedError(f'No handler established for {statement.data}')) #SNO
            if not getattr(handler, "_is_control_statement", False):
                # Simple statements: those that don't have nested
                # statements, ones that don't interate, or have complex requirements
                # Other statements need to handle binding
                # and decide what to do for echo
                statement = bind_operations(statement)
                self.echo_source(statement)
            try:
                handler(self, statement)
            except VgrException as e:
                raise e
            except KeyboardInterrupt as e:
                print_stdout('')
                raise VgrRuntimeError(statement, e) from e
            except Exception as e:
                raise VgrRuntimeError(statement, e) from e
            finally:
                dd_clear_scratch(self.dd)

    def _push_source(self, source: str) -> None:
        # the <...> notation is used to indicate cmd line, stdin, etc
        # which don't really have a file name.
        # the source stack is strictly for file name context
        if source.startswith('<') and source.endswith('>'): source = ''
        source_stack: list = self.get_var(*self._SOURCE_STACK_PATH)
        source_stack.insert(0, source)
        self.set_var(source_stack, *self._SOURCE_STACK_PATH)

    def _pop_source(self) -> None:
        source_stack: list = self.get_var(*self._SOURCE_STACK_PATH)
        if source_stack:
            source_stack.pop()
            self.set_var(source_stack, *self._SOURCE_STACK_PATH)

def create_exec_context(parser: Lark, dd: DataDictionary) -> ExecContext:
    ctx = DefaultExecContext(parser, dd)
    remember_terminals(parser)
    return ctx
