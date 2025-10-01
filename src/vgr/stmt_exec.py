
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable
import ast
import math
import os

from lark import Lark, Tree, Token, Transformer, v_args, exceptions

from .app_exceptions import (
    VgrException,
    VgrRuntimeError,
    VgrStatementBreak,
    VgrStatementContinue,
)
from .data_dict import DataDictionary, DynamicValue
from .dbg import print_tree
from .dd_config import VGR_PREFIX
from .evaluate import (
    bind_operations,
    eval_expr,
    eval_expr_or_const,
    get_writable_var_path,
)
from .output import verify_relative_path
from .exec_context import ExecContext
from .functions import build_dict
from .mathpak import (
    bound_ops,
    poly_int,
    poly_list,
    poly_number,
    poly_true,
    type_str,
)
from .redir import (
    execute_open,
    execute_close,
    print_stderr,
    print_stdout,
)
from .src_mgr import SSM
from .stmt_cflags import (
    execute_debug,
    execute_echo,
    execute_verbose,
)
from .stmt_choose import (
    execute_choose,
    execute_choose_using,
)
from .stmt_exit import (
    execute_assert,
    execute_exit,
    execute_return,
)
from .stmt_funct import (
    execute_def_function,
    execute_call,
    execute_call_giving,
)
from .stmt_list import (
    execute_list_append,
    execute_list_insert,
    execute_list_prepend,
    execute_list_remove_first,
    execute_list_remove_last,
    execute_list_remove,
)
from .stmt_log import (
    execute_log,
    execute_log_setlevel,
)
from .stmt_misc import execute_sleep
from .stmt_print import (
    execute_print,
    execute_printf,
)
from .stmt_select import execute_select
from .stmt_set import (
    execute_compile_arrow,
    execute_load_from,
    execute_reset,
    execute_set_arrow,
    execute_set_in_place,
    execute_set,
    execute_swap,
    execute_unset,
)
from .stmt_sort import execute_sort
from .stmt_zip import execute_zip
from .tags import control_statement

LOOP_META_PATH = ('$loop',)
_LOOP_META_LENGTH = 'length'
_LOOP_META_INDEX = 'index'
_LOOP_META_FIRST = 'first'
_LOOP_META_LAST = 'last'

def set_loop_meta(meta: dict, index: int, length: int=None) -> dict:
    """
    This sets the structure used inside the body of the loop
    reflecting the iteration count etc.
    Based on Jinja's behavior.
    """
    meta[_LOOP_META_INDEX] = index
    meta[_LOOP_META_FIRST] = index == 1
    if length is not None:
        meta[_LOOP_META_LAST] = index == length
        meta[_LOOP_META_LENGTH] = length
    return meta

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
        file = ctx.eval_filename_expr(child, True)
        if file is None or len(file) == 0: continue
        path = Path(file)
        if not path.exists():
            raise VgrRuntimeError(child, FileNotFoundError(f'File {file!r} not found'))
        if not path.is_file():
            raise VgrRuntimeError(child, PermissionError(f'{file!r} does not reference a file'))
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

@control_statement
@bound_ops("Begin", "Begin-End", "Block")
def execute_block(ctx: ExecContext, statement: Tree) -> None:
    """
**Defines a group of statements with local variable scoping**

* Begin [:]<br>
  <em>_statement_...<br>
  End [;]

Also see `Declare`
"""
    # NB: no source to echo
    # NB: No loop meta here so we don't shadow
    #     when used inside a loop
    ctx.dd.push_frame()
    try:
        ctx.dispatch_statements(statement.children)
    finally:
        ctx.dd.pop_frame()

@bound_ops("Declare")
def execute_declare_local(ctx: ExecContext, statement: Tree) -> None:
    """
**Establishes a name as a variable; used for establishing scope**

* Declare _name_,... [;]
* Declare _name_,... [As] Local [;]
* Declare _name_,... [As] Global [;]

Without an argument, the variables are declared local.
"""
    _declare(ctx, statement)

def execute_declare_global(ctx: ExecContext, statement: Tree) -> None:
    """*documentation combined with local*"""
    _declare(ctx, statement, False)

def _declare(ctx: ExecContext, statement: Tree, as_local: bool=True) -> None:
    var_paths = []
    for child in statement.children:
        var_paths.append(get_writable_var_path(ctx, child))
    # Now declare them and produce verbose output
    for var_path in var_paths:
        rc = ctx.dd.declare_var(as_local, *var_path)
        if ctx.verbose and rc is not None: ctx.print_verbose('.'.join(var_path), 'declared as', 'Local' if rc else 'Global')

@control_statement
@bound_ops("Do-Forever", "Forever")
def execute_forever(ctx: ExecContext, statement: Tree) -> None:
    """
**Predicate-less loop**

* Do Forever [:]<br>
  <em>_statement_...<br>
  End [;]

The statements are repeatedly executed until a `Break` statement is
encountered. A `Continue` causes the statements to loop.

Inside the body of the loop, the _$loop_ variable is available.

```vgr
Set x To 5
Do Forever:
    Print x, $loop
    Add 5 to x
    If x > 20:
        Break
    End
End

5 {'index': 1, 'first': True}
10 {'index': 2, 'first': False}
15 {'index': 3, 'first': False}
20 {'index': 4, 'first': False}
```

Also see `Break` and `Continue`
"""
    meta = { }
    ctx.dd.push_frame([(LOOP_META_PATH, meta)])
    try:
        i = 1
        while True:
            set_loop_meta(meta, i)
            try:
                ctx.dispatch_statements(statement.children)
            except VgrStatementBreak:
                return
            except VgrStatementContinue:
                continue
            i += 1
    finally:
        ctx.dd.pop_frame()

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

* If _expression_ [Then | Do | :]<br>
  <em>_statement_...<br>
  End [;]
* If _expression_ [Then | Do | :]<br>
  <em>_statement_...<br>
  Else [Do | :]<br>
  <em>_statement_...<br>
  End [;]

If the expression evaluates to _True_ the first block of statements is executed.
If it evaluates to _False_, the second block of statements—if provided—is executed.
If `Break` or `Continue` is encountered, statements
following it are skipped. Execution resumes after the `End`.

Also see `Break` and `Continue`
"""
    exec_if_else(ctx, statement, True)

@control_statement
@bound_ops("Unless")
def execute_unless(ctx: ExecContext, statement: Tree) -> None:
    """
**Conditionally execute a block of statements**

* Unless _expression_ [Then | :]<br>
  <em>_statement_...<br>
  End [;]

If the expression evaluates to _False_ the block of statements is executed.
If `Break` is encountered, looping ends regardless of the
expression's value. If `Continue` is encountered, statements
following it are skipped, and the expression is checked again.

Also see `Break` and `Continue`
"""
    exec_if_else(ctx, statement, False)

def exec_loop(ctx: ExecContext, statement: Tree, desired_value: bool) -> None:
    """Internal implemenation for loops with a predicate"""
    ctx.echo_source(statement, statement.children[1])
    predicate = bind_operations(statement.children[0])
    meta = { }
    ctx.dd.push_frame([(LOOP_META_PATH, meta)])
    try:
        i = 1
        while True:
            if poly_true(ctx.eval_expr(predicate)) != desired_value: return
            set_loop_meta(meta, i)
            try:
                ctx.dispatch_statements(statement.children[1:])
            except VgrStatementBreak:
                return
            except VgrStatementContinue:
                continue
            i += 1
    finally:
        ctx.dd.pop_frame()

def exec_repeat(ctx: ExecContext, statement: Tree) -> None:
    """Internal implementation for loops with a fixed count"""
    ctx.echo_source(statement, statement.children[1])
    counter = poly_int(ctx.eval_expr(bind_operations(statement.children[0])))
    if isinstance(counter, (int, float)):
        counter = math.floor(counter)
        if counter > 0:
            meta = { }
            # Meta information is local to the loop
            ctx.dd.push_frame([(LOOP_META_PATH, meta)])
            try:
                length = counter
                i = 1
                while counter > 0:
                    # Update the meta information
                    set_loop_meta(meta, i, length)
                    try:
                        ctx.dispatch_statements(statement.children[1:])
                    except VgrStatementBreak:
                        return
                    except VgrStatementContinue:
                        pass
                    counter -= 1
                    i += 1
            finally:
                ctx.dd.pop_frame()

@control_statement
@bound_ops("While")
def execute_while(ctx: ExecContext, statement: Tree) -> None:
    """
**Repeatedly execute a block of statements while a condition exists**

* While _expression_ [Do | :]<br>
  <em>_statement_...<br>
  End [;]

As long as the expression evaluates to _True_, the block of statements is
repeatedly executed.
If `Break` is encountered, looping ends regardless of the
expression's value. If `Continue` is encountered, statements
following it are skipped, and the expression is checked again.

Also see `Break` and `Continue`
"""
    exec_loop(ctx, statement, True)

@control_statement
@bound_ops("Until")
def execute_until(ctx: ExecContext, statement: Tree) -> None:
    """
**Repeatedly execute a block of statements until a condition is reached**

* Until _expression_ [Do | :]<br>
  <em>_statement_...<br>
  End [;]

The block of statements is executed until the expression evaluates to _True_.
If `Break` is encountered, looping ends regardless of the
expression's value. If `Continue` is encountered, statements
following it are skipped, and the expression is checked again.

Also see `Break` and `Continue`
"""
    exec_loop(ctx, statement, False)

@control_statement
@bound_ops("Repeat")
def execute_repeat(ctx: ExecContext, statement: Tree) -> None:
    """
**Execute a block of statements a fixed number of times**

* Repeat _expression_ [Do | :]<br>
  <em>_statement_...<br>
  End [;]

The block of statements is executed the given number of times.
The expression is evaluated an converted to an integer, rounding down.
For any statements to execute, the value must be greater than or equal to one.
If `Break` is encountered, looping ends regardless of the
expression's value. If `Continue` is encountered, statements
following it are skipped and looping continues.

Statements have access to a _$loop_ local variable
which provides information such as _$loop.index_, _$loop.first_,
and _$loop.last_.

```vgr
Repeat 3:
   Print $loop
End

{'index': 1, 'first': True, 'last': False, 'length': 3}
{'index': 2, 'first': False, 'last': False, 'length': 3}
{'index': 3, 'first': False, 'last': True, 'length': 3}
```
"""
    exec_repeat(ctx, statement)

@control_statement
@bound_ops("ForEach")
def execute_foreach(ctx: ExecContext, statement: Tree) -> None:
    """
**Iterate over a list of values**

* ForEach _variable_ In _expression_ [Do | :]<br>
  <em>_statement_...<br>
  End [;]

If expression is a single value, non-_None_ value, the statements are executed
exactly once. If a list, the statements are executed once for each item,
including items that are _None_, and if a dictionary, the statements
are executed once for each key/value pair.

If `Break` is encountered, iteration ends regardless of the
number of items remaining. If `Continue` is encountered, statements
following it are skipped, and the loop continues with the next item.

Statements have access to a _$loop_ local variable
which provides information such as _$loop.index_, _$loop.first_,
and _$loop.last_.

```vgr
ForEach a In ["A", "B", "C"]:
    Print a, $loop
End

A {'index': 1, 'first': True, 'last': False, 'length': 3}
B {'index': 2, 'first': False, 'last': False, 'length': 3}
C {'index': 3, 'first': False, 'last': True, 'length': 3}
```

Also see `Break` and `Continue`
"""
    ctx.echo_source(statement, statement.children[2])
    var_path = get_writable_var_path(ctx, statement.children[0])
    collection = poly_list(ctx.eval_expr(bind_operations(statement.children[1])))
    if collection is not None and len(collection) > 0:
        length = len(collection)
        meta = { }
        # The value and meta information are local to the loop
        ctx.dd.push_frame([(var_path, None), (LOOP_META_PATH, meta)])
        try:
            # The list is copied to allow mutation within the loop
            for i, value in enumerate(collection.copy()):
                # Update the meta information
                set_loop_meta(meta, i + 1, length)
                # And the value itself
                ctx.set_var(value, *var_path)
                try:
                    ctx.dispatch_statements(statement.children[2:])
                except VgrStatementBreak:
                    return
                except VgrStatementContinue:
                    continue
        finally:
            ctx.dd.pop_frame()

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
        # TODO Need to handle triple-quotes in a similar manner
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
    'assert':            execute_assert,
    'block':             execute_block,
    'break':             execute_break,
    'call_giving':       execute_call_giving,
    'call':              execute_call,
    'choose_using':      execute_choose_using,
    'choose':            execute_choose,
    'close':             execute_close,
    'compile_arrow':     execute_compile_arrow,
    'continue':          execute_continue,
    'debug':             execute_debug,
    'declare_local':     execute_declare_local,
    'declare_global':    execute_declare_global,
    'def_function':      execute_def_function,
    'echo':              execute_echo,
    'exit':              execute_exit,
    'foreach':           execute_foreach,
    'forever':           execute_forever,
    'if':                execute_if,
    'list_append':       execute_list_append,
    'list_insert':       execute_list_insert,
    'list_prepend':      execute_list_prepend,
    'list_remove_first': execute_list_remove_first,
    'list_remove_last':  execute_list_remove_last,
    'list_remove':       execute_list_remove,
    'load_from':         execute_load_from,
    'log_setlevel':      execute_log_setlevel,
    'log':               execute_log,
    'open':              execute_open,
    'pass':              execute_pass,
    'print':             execute_print,
    'printf':            execute_printf,
    'repeat':            execute_repeat,
    'reset':             execute_reset,
    'return':            execute_return,
    'select':            execute_select,
    'set_arrow':         execute_set_arrow,
    'set_in_place':      execute_set_in_place,
    'set':               execute_set,
    'sleep':             execute_sleep,
    'sort':              execute_sort,
    'source':            execute_source,
    'swap':              execute_swap,
    'unless':            execute_unless,
    'unset':             execute_unset,
    'until':             execute_until,
    'verbose':           execute_verbose,
    'while':             execute_while,
    'zip':               execute_zip,
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

    def __init__(self, parser: Lark, dd: DataDictionary):
        super().__init__(parser, dd)
        self._source_stack = []
        # We maintain the state, but the user can still
        # read the values, which are global.
        self.set_var(DynamicValue(lambda: self.source_stack), VGR_PREFIX,  'source')
        self.set_var(DynamicValue(lambda: self.debug), VGR_PREFIX,  'debug')
        self.set_var(DynamicValue(lambda: self.echo), VGR_PREFIX, 'echo')
        self.set_var(DynamicValue(lambda: self.verbose), VGR_PREFIX, 'verbose')

    def get_var(self, *path: str) -> Any: return self.dd.get_var(*path)
    def set_var(self, data: Any, /, *path: str) -> Any: return self.dd.set_var(data, *path)
    def var_exists(self, *path: str) -> tuple[bool, Any]: return self.dd.var_exists(*path)

    def set_var_user(self, data: Any, /, *path: str):
        """*deprecated*"""
        return self.dd.set_var_user(data, *path)

    def eval_expr(self, expr: Any) -> Any: return eval_expr(self, expr)
    def eval_expr_or_const(self, expr: Any) -> Any: return eval_expr_or_const(self, expr)

    def eval_to_str(self, expr: Tree, name: str, allow_none: bool=False) -> str:
        """Helper that makes sure you got a string back from an expression"""
        rc = self.eval_expr(expr)
        if rc is None and allow_none: return None
        if not isinstance(rc, str):
            raise VgrRuntimeError(expr, TypeError(f'{name} must be a string; found {type_str(rc)}'))
        return rc

    def eval_filename_expr(self, expr: Any, allow_none: bool=False) -> str:
        """Helper that gets a string that should be a relative filename"""
        return verify_relative_path(self.eval_to_str(expr, 'File name', allow_none))

    def eval_to_int(self, expr: Tree, name: str, allow_none: bool=False) -> int:
        rc = self.eval_expr(expr)
        if rc is None and allow_none: return None
        if not isinstance(rc, (bool, int, float, str)):
            raise VgrRuntimeError(expr, TypeError(f'{name} must be an integer; found {type_str(rc)}'))
        return poly_int(rc)

    def eval_to_number(self, expr: Tree, name: str, allow_none: bool=False):
        rc = self.eval_expr(expr)
        if rc is None and allow_none: return None
        if isinstance(rc, bool): return int(rc)
        if isinstance(rc, (int, float)): return rc
        if isinstance(rc, str): return poly_number(rc)
        raise VgrRuntimeError(expr, TypeError(f'{name} must be an integer; found {type_str(rc)}'))

    def eval_to_bool(self, expr: Tree, name: str, allow_none: bool=False) -> bool:
        rc = self.eval_expr(expr)
        if rc is None and allow_none: return None
        if not isinstance(rc, (bool, int, float, str)):
            raise VgrRuntimeError(expr, TypeError(f'{name} must be an boolean; found {type_str(rc)}'))
        return poly_true(rc)

    def get_source(self, tree, end_tree = None) -> str:
        return (SSM.source_for(tree, end_tree) or '').strip()

    @property
    def source_stack(self) -> list[str]:
        return self._source_stack

    @ExecContext.echo.setter
    def echo(self, v: bool):
        super(DefaultExecContext, DefaultExecContext).echo.__set__(self, v)

    def echo_source(self, tree, end_tree = None) -> None:
        if super().echo:
            src = self.get_source(tree, end_tree)
            src = src.splitlines()[0] if src else '--unknown--'
            if super().verbose:
                # prefix the source with file and line number
                print_stderr(f'{SSM.current[0]}({SSM.line_number(tree)}) :', src)
            else:
                # just the source
                print_stderr(src)

    @ExecContext.debug.setter
    def debug(self, v: bool):
        super(DefaultExecContext, DefaultExecContext).debug.__set__(self, v)

    def print_debug(self, *args, **kwargs) -> None:
        if super().debug: print_stderr(*args, **kwargs)

    @ExecContext.verbose.setter
    def verbose(self, v: bool):
        super(DefaultExecContext, DefaultExecContext).verbose.__set__(self, v)

    def print_verbose(self, *args, **kwargs) -> None:
        if super().verbose: print_stderr(*args, **kwargs)

    def parse_expression(self, expr_text: str) -> Tree:
        # TODO push source here?
        # when we create it, we need to know the origin
        if expr_text and not expr_text.isspace():
            expr = self._parser.parse(expr_text, start='expr')
            expr = ConstantsNormalizer().transform(expr)
            expr = VarRefOptimizer().transform(expr)
            expr = bind_operations(expr)
            self.print_tree(expr)
            return expr
        return None

    def execute_statements(self, statement_text: str, origin: str) -> None:
        """Parse the text and execute the resulting statements"""
        if statement_text and not statement_text.isspace():
            SSM.push(origin, statement_text)
            # the <...> notation is used to indicate cmd line, stdin, etc
            # which don't really have a file name.
            # the source stack is strictly for file name context
            self._source_stack.insert(0, '' if origin.startswith('<') and origin.endswith('>') else origin)
            try:
                self.dispatch_statements(self._parser.parse(statement_text, start='opt_statements').children)
            except exceptions.UnexpectedInput as e:
                raise VgrException(e, e, *SSM.current) from e
            finally:
                self._source_stack.pop(0)
                SSM.pop()

    def dispatch_statements(self, statements: Iterable[Tree]) -> None:
        """Given a sequence of parsed statements dispatch them to their handler"""
        for statement in statements:
            statement = ConstantsNormalizer().transform(statement)
            statement = VarRefOptimizer().transform(statement)
            handler = STATEMENT_HANDLERS.get(statement.data)
            if not handler:
                raise VgrRuntimeError(statement, NotImplementedError(f'No handler established for {statement.data}')) #SNO
            if not getattr(handler, "_is_control_statement", False):
                # Simple statements: those that don't have nested
                # statements, ones that don't interate, or have complex requirements
                # Other statements need to handle binding
                # and decide what to do for echo
                statement = bind_operations(statement)
                self.print_tree(statement)
                self.echo_source(statement)
            else:
                self.print_tree(statement)
            try:
                handler(self, statement)
            except VgrException as e:
                raise e
            except KeyboardInterrupt as e:
                print_stdout('')
                raise VgrRuntimeError(statement, e) from e
            except Exception as e:
                raise VgrRuntimeError(statement, e) from e

    def print_tree(self, item: Any) -> None:
        if super().debug: print_tree(item)

def create_exec_context(parser: Lark, dd: DataDictionary) -> ExecContext:
    return DefaultExecContext(parser, dd)
