
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable
import ast
import math
import os
import re
import warnings

from lark import Lark, Tree, Token, Transformer, v_args, exceptions

from .app_exceptions import (
    BlockType,
    VgrException,
    VgrRuntimeError,
    VgrStatementBreak,
    VgrStatementContinue,
)
from .data_dict import DataDictionary, DynamicValue
from .dbg import print_tree
from .dd_config import (
    add_include,
    INCLUDED_PATH,
    is_included,
    VGR_PREFIX,
)
from .evaluate import (
    bind_operations,
    eval_expr,
    eval_expr_or_const,
    get_writable_var_path,
)
from .exec_context import ExecContext
from .builtins import (
    bound_ops,
    build_dict,
    expand_filename,
    poly_int,
    poly_list,
    poly_number,
    poly_repr,
    poly_true,
    poly_type,
    verify_relative_path
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
    execute_list_replace,
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
    execute_set,
    execute_swap,
    execute_unset,
)
from .stmt_sort import execute_sort
from .stmt_zip import execute_zip
from .tags import control_statement

LOOP_META_PATH = ('$loop',)
_LOOP_META_LENGTH = 'length'
_LOOP_META_INDEX = 'index' # NB: this is zero based!
_LOOP_META_FIRST = 'first'
_LOOP_META_LAST = 'last'

def set_loop_meta(meta: dict, index: int, length: int=None) -> dict:
    """
    This sets the structure used inside the body of the loop
    reflecting the iteration count etc.
    Based on Jinja's behavior.
    """
    meta[_LOOP_META_INDEX] = index
    meta[_LOOP_META_FIRST] = index == 0
    if length is not None:
        meta[_LOOP_META_LAST] = index == (length-1)
        meta[_LOOP_META_LENGTH] = length
    return meta

_VGR_PATH: list[Path] = []

def get_vgr_path() -> list[Path]:
    """
    Parse VGR_PATH into a list of paths.
    If if not defined in the environment, platform specific defaults
    are choosen. The parsing is done once, so changing `env.VGR_PATH` does not
    affect this.
    """
    if len(_VGR_PATH) == 0:
        envpath = os.environ.get("VGR_PATH")
        if envpath is not None:
            entries = [(path.strip() or '.') for path in envpath.split(os.pathsep)]
        else:
            # OS-appropriate sensible defaults
            if os.name == 'posix':
                entries = ['.', str(Path.home() / '.vgr'), '/usr/local/share/vgr', '/usr/share/vgr']
            elif os.name == 'nt':
                entries = ['.', str(Path.home() / 'vgr')]
                pf = os.environ.get('PROGRAMFILES')
                if pf: entries.append(str(Path(pf) / 'vgr' / "lib"))
            else:
                entries = ['.', str(Path.home() / 'vgr')]
        for entry in entries:
            # Don't check for exist() here: user can create after start in repl
            _VGR_PATH.append(Path(expand_filename(entry)))
    return _VGR_PATH

def vgrpath_resolve(filename: str) -> Path:
    """
    Using get_vgr_path(), try to find a VGR source file.
    If filename contains any path info, it must be relative to the CWD.
    Returning None means we didn't find it on the path.
    It does _NOT_ mean the file doesn't exist.
    Likewise, returning a non-None value doesn't mean the item is
    a readable file, only that it exists.

    Behavior is modeled after AWKPATH:
    https://www.gnu.org/software/gawk/manual/html_node/AWKPATH-Variable.html
    """
    # If filename does not include a path component
    # we consult the path
    if (os.sep not in filename) and (not os.altsep or os.altsep not in filename):
        search_dirs = get_vgr_path()
        def _search(name: str):
            for d in search_dirs:
                if d.exists():
                    candidate = d / name
                    if candidate.exists(): return candidate.resolve()
            return None
        # First pass: exact name
        found = _search(filename)
        if found: return found
        # Second pass: try with extension
        if not filename.lower().endswith('.vgr'):
            found = _search(filename + '.vgr')
            if found: return found
    return None

def find_vgr_source(filename: str) -> Path:
    """
    Find a VGR source file for sourcing or including
    """
    filepath = vgrpath_resolve(filename)
    if filepath is not None: return filepath
    # Require that it be a local reference
    full_path = expand_filename(filename)
    cwd = expand_filename(os.getcwd())
    if os.path.commonpath([cwd, full_path]) != cwd:
        raise ValueError(f'File {poly_repr(full_path)} not relative to {poly_repr(cwd)}')
    return Path(full_path)

def _find_source(ctx: ExecContext, expr: Tree) -> Path:
    """
    Internal version of find_vgr_source() that works with values
    from the parse tree.
    """
    filename = ctx.eval_to_str(expr, 'File name', True)
    return None if filename is None else find_vgr_source(filename)

@bound_ops("Source")
def execute_source(ctx: ExecContext, statement: Tree) -> None:
    """
**Execute statements stored in a file**

* Source [File | Files] *file_name* [, *file_name*]&hellip; [;]

Each argument is evaluated to a file name. Statements in the file
are executed, inheriting the current state of all variable and
input/output redirection.

> **Windows Note**\\
> If you hard code paths, please use the slash as a universal
> directory separator. Since the backslash is an escape character, if you use
> it in a string, you will either need to double it or use a _raw string_.

```vgr
**TODO**
```

Also see `@Include` and `Reset`
"""
    for child in statement.children:
        try:
            path = _find_source(ctx, child)
            if path is not None: do_source(ctx, path)
        except Exception as e:
            raise VgrRuntimeError(child, e) from e

@bound_ops("@Include")
def execute_include(ctx: ExecContext, statement: Tree) -> None:
    """
**Execute statements stored in a file once per run**

* @Include [File | Files] *file_name* [, *file_name*]&hellip; [;]

Similar to `Source` but files are only included once per run, unless
cleared by `Reset`.

> **Windows Note**\\
> If you hard code paths, please use the slash as a universal
> directory separator. Since the backslash is an escape character, if you use
> it in a string, you will either need to double it or use a _raw string_.

Also see `Source` and `Reset`
"""
    for child in statement.children:
        try:
            path = _find_source(ctx, child)
            if path is not None: do_include(ctx, path)
        except Exception as e:
            raise VgrRuntimeError(child, e) from e

def do_include(ctx: ExecContext, path: Path) -> None:
    if is_included(path):
        if ctx.verbose: ctx.print_verbose('Skipping ', poly_repr(path), ': previously included')
    else:
        do_source(ctx, path, True)
        add_include(path)

def do_source(ctx: ExecContext, path: Path, included: bool=False) -> None:
    filename = str(path)
    if not path.exists():
        raise FileNotFoundError(0, f'File {filename!r} not found')
    if not path.is_file():
        raise IsADirectoryError(0, f'{filename!r} does not reference a file')
    if not os.access(path, os.R_OK):
        raise PermissionError(0, f'File {filename!r} not readable')
    statements = None
    if ctx.verbose: ctx.print_verbose('Executing statements from ', poly_repr(filename), '...')
    with open(path, 'r', encoding='utf-8-sig') as f:
        statements = f.read()
    tval = ctx.get_var(*INCLUDED_PATH)
    try:
        ctx.set_var(included, *INCLUDED_PATH)
        ctx.execute_statements(statements, str(path))
    finally:
        ctx.set_var(tval, *INCLUDED_PATH)

@bound_ops("Break")
def execute_break(_: ExecContext, statement: Tree) -> None:
    """
**Exits the current block of statements**

* Break [;]

Used with `While`, `Until`, `ForEach` and other looping statements

```vgr
**TODO**
```

"""
    raise VgrStatementBreak(statement, BlockType.ALL_BLOCKS)

@bound_ops("Continue")
def execute_continue(_: ExecContext, statement: Tree) -> None:
    """
**Cause the current loop to start again**

* Continue [;]

```vgr
**TODO**
```

"""
    raise VgrStatementContinue(statement, BlockType.ALL_BLOCKS)

@bound_ops("Pass", "NOP")
def execute_pass(_: ExecContext, __: Tree) -> None:
    """
**A placeholder for a statement**

* Pass [;]
* NOP [;]

A placeholder for a statement, which takes no action and has no side effects.

```vgr
If x < 10:
    Pass // Must have one statement in block
Else:
    Print "x is too big"
End
```
"""

@control_statement
@bound_ops("Begin End")
def execute_block(ctx: ExecContext, statement: Tree) -> None:
    """
**Defines a group of statements with local variable scoping**

* Begin [:]\\
  &emsp;&emsp;_statement_&hellip;\\
  End [;]

```vgr
**TODO**
```

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
**Establishes a name as a variable, optionally establishing scope**

* Declare _name_,&hellip; [;]
* Declare _name_,&hellip; [As] Local [;]
* Declare _name_,&hellip; [As] Global [;]

```vgr
**TODO**
```

"""
    _declare(ctx, statement, True)

def execute_declare_global(ctx: ExecContext, statement: Tree) -> None:
    """*documentation combined with local*"""
    _declare(ctx, statement, False)

def execute_declare(ctx: ExecContext, statement: Tree) -> None:
    """*documentation combined with local*"""
    _declare(ctx, statement, None)

def _declare(ctx: ExecContext, statement: Tree, as_local: bool) -> None:
    var_paths = []
    for child in statement.children:
        var_paths.append(get_writable_var_path(ctx, child))
    # Now declare them and produce verbose output
    for var_path in var_paths:
        rc = ctx.dd.declare_var(as_local, *var_path)
        if ctx.verbose and rc is not None:
            ctx.print_verbose('.'.join(var_path), 'declared as', 'Local' if rc else 'Global')

@control_statement
@bound_ops("Do Forever")
def execute_forever(ctx: ExecContext, statement: Tree) -> None:
    """
**Predicate-less loop**

* Do Forever [:]\\
  &emsp;&emsp;_statement_&hellip;\\
  End [;]

The statements are repeatedly executed until a `Break` statement is
encountered. A `Continue` causes the statements to loop.

Statements have access to the *$loop* variable, but only *index* and _first_.

```vgr
Set x To 5
Do Forever:
    Print x, $loop
    Add 5 to x
    If x > 20:
        Break
    End
End

5 {'index': 0, 'first': True}
10 {'index': 1, 'first': False}
15 {'index': 2, 'first': False}
20 {'index': 3, 'first': False}
```

Also see `Break` and `Continue`
"""
    meta = { }
    ctx.dd.push_frame([(LOOP_META_PATH, meta)])
    try:
        i = 0
        while True:
            set_loop_meta(meta, i)
            try:
                ctx.dispatch_statements(statement.children)
            except VgrStatementBreak as e:
                e.validate_for_block(BlockType.DO_LOOP)
                return
            except VgrStatementContinue as e:
                e.validate_for_block(BlockType.DO_LOOP)
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
@bound_ops("If Else")
def execute_if(ctx: ExecContext, statement: Tree) -> None:
    """
**Conditionally execute a block of statements**

* If *expression* [Then | :]\\
  &emsp;&emsp;_statement_&hellip;\\
  End [;]
* If *expression* [Then | :]\\
  &emsp;&emsp;_statement_&hellip;\\
  Else [:]\\
  &emsp;&emsp;_statement_&hellip;\\
  End [;]

If the expression evaluates to `True` the first block of statements is executed.
If it evaluates to `False`, the second block of statements—if provided—is executed.
If `Break` or `Continue` is encountered, statements
following it are skipped. Execution resumes after the `End`.

```vgr
**TODO**
```

Also see `Break` and `Continue`
"""
    exec_if_else(ctx, statement, True)

@control_statement
@bound_ops("Unless")
def execute_unless(ctx: ExecContext, statement: Tree) -> None:
    """
**Conditionally execute a block of statements**

* Unless *expression* [Then | :]\\
  &emsp;&emsp;_statement_&hellip;\\
  End [;]

If the expression evaluates to `False` the block of statements is executed.
If `Break` is encountered, looping ends regardless of the
expression's value. If `Continue` is encountered, statements
following it are skipped, and the expression is checked again.

```vgr
**TODO**
```

Also see `Break` and `Continue`
"""
    exec_if_else(ctx, statement, False)

def exec_loop(ctx: ExecContext, statement: Tree, desired_value: bool, block_types=BlockType.ALL_BLOCKS) -> None:
    """Internal implemenation for loops with a predicate"""
    ctx.echo_source(statement, statement.children[1])
    predicate = bind_operations(statement.children[0])
    meta = { }
    ctx.dd.push_frame([(LOOP_META_PATH, meta)])
    try:
        i = 0
        while True:
            if poly_true(ctx.eval_expr(predicate)) != desired_value: return
            set_loop_meta(meta, i)
            try:
                ctx.dispatch_statements(statement.children[1:])
            except VgrStatementBreak as e:
                e.validate_for_block(block_types)
                return
            except VgrStatementContinue as e:
                e.validate_for_block(block_types)
            i += 1
    finally:
        ctx.dd.pop_frame()

def exec_repeat(ctx: ExecContext, statement: Tree, block_types=BlockType.ALL_BLOCKS) -> None:
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
                i = 0
                while counter > 0:
                    # Update the meta information
                    set_loop_meta(meta, i, length)
                    try:
                        ctx.dispatch_statements(statement.children[1:])
                    except VgrStatementBreak as e:
                        e.validate_for_block(block_types)
                        return
                    except VgrStatementContinue as e:
                        e.validate_for_block(block_types)
                    counter -= 1
                    i += 1
            finally:
                ctx.dd.pop_frame()

@control_statement
@bound_ops("While")
def execute_while(ctx: ExecContext, statement: Tree) -> None:
    """
**Repeatedly execute a block of statements while a condition exists**

* While *expression* [:]\\
  &emsp;&emsp;_statement_&hellip;\\
  End [;]

As long as the expression evaluates to `True`, the block of statements is
repeatedly executed.
If `Break` is encountered, looping ends regardless of the
expression's value. If `Continue` is encountered, statements
following it are skipped, and the expression is checked again.

```vgr
Set x To 0
While x < 50:
    Print x, ":", x.Pow(2), $loop
    Set x += 10
End

0 : 0 {'index': 0, 'first': True}
10 : 100 {'index': 1, 'first': False}
20 : 400 {'index': 2, 'first': False}
30 : 900 {'index': 3, 'first': False}
40 : 1600 {'index': 4, 'first': False}
```

Also see `Until` in addition to `Break` and `Continue`
"""
    exec_loop(ctx, statement, True, BlockType.WHILE_LOOP)

@control_statement
@bound_ops("Until")
def execute_until(ctx: ExecContext, statement: Tree) -> None:
    """
**Repeatedly execute a block of statements until a condition is reached**

* Until *expression* [:]\\
  &emsp;&emsp;_statement_&hellip;\\
  End [;]

The block of statements is executed until the expression evaluates to `True`.
If `Break` is encountered, looping ends regardless of the
expression's value. If `Continue` is encountered, statements
following it are skipped, and the expression is checked again.

```vgr
Set x To 0
Until x >= 50
    Print x, ":", x.Pow(2), $loop
    Set x += 10
End

0 : 0 {'index': 0, 'first': True}
10 : 100 {'index': 1, 'first': False}
20 : 400 {'index': 2, 'first': False}
30 : 900 {'index': 3, 'first': False}
40 : 1600 {'index': 4, 'first': False}
```

Also see `While` in addition to `Break` and `Continue`
"""
    exec_loop(ctx, statement, False)

@control_statement
@bound_ops("Repeat")
def execute_repeat(ctx: ExecContext, statement: Tree) -> None:
    """
**Execute a block of statements a fixed number of times**

* Repeat *expression* [:]\\
  &emsp;&emsp;_statement_&hellip;\\
  End [;]

The block of statements is executed the given number of times.
The expression is evaluated an converted to an integer, rounding down.
For any statements to execute, the value must be greater than or equal to one.
If `Break` is encountered, looping ends regardless of the
expression's value. If `Continue` is encountered, statements
following it are skipped and looping continues.

Statements have access to the *$loop* variable, including *index*, *length*, _first_, and _last_.

```vgr
Repeat 3:
   Print $loop
End

{'index': 0, 'first': True, 'last': False, 'length': 3}
{'index': 1, 'first': False, 'last': False, 'length': 3}
{'index': 2, 'first': False, 'last': True, 'length': 3}
```
"""
    exec_repeat(ctx, statement)

@control_statement
@bound_ops("ForEach")
def execute_foreach(ctx: ExecContext, statement: Tree) -> None:
    """
**Iterate over a list of values**

* ForEach *variable* In *expression* [:]\\
  &emsp;&emsp;_statement_&hellip;\\
  End [;]

If expression is a single, non-`None` value, the statements are executed
exactly once. If a list, the statements are executed once for each item,
including items that are `None`, and if a dictionary, the statements
are executed once for each key/value pair.

If `Break` is encountered, iteration ends regardless of the
number of items remaining. If `Continue` is encountered, statements
following it are skipped, and the loop continues with the next item.

Statements have access to the *$loop* variable, including *index*, *length*, _first_, and _last_.

```vgr
ForEach a In ["A", "B", "C"]:
    Print a, $loop
End

A {'index': 0, 'first': True, 'last': False, 'length': 3}
B {'index': 1, 'first': False, 'last': False, 'length': 3}
C {'index': 2, 'first': False, 'last': True, 'length': 3}

ForEach kv_pair In math:
    If $loop.first: Print "-" * 60; End
    Print kv_pair
    If $loop.last: Print "-" * 60; End
End

------------------------------------------------------------
['e', 2.718281828459045]
['float', {'max': 1.7976931348623157e+308, 'min': 2.2250738585072014e-308}]
['inf', inf]
['nan', nan]
['neg_inf', -inf]
['pi', 3.141592653589793]
['random', 0.30365351264499363]
['random100', 7]
['tau', 6.283185307179586]
------------------------------------------------------------
```

Also see `Break` and `Continue`
"""
    ctx.echo_source(statement, statement.children[2])
    var_path = get_writable_var_path(ctx, statement.children[0])
    collection = ctx.eval_expr(bind_operations(statement.children[1]))
    if collection is None: return # very fast fail
    if isinstance(collection, list):
        if not collection: return # fast fail
        # Lists are copied to allow mutation within the loop
        collection = collection.copy()
    else:
        # poly_list() converts
        #   - Single values to an list of one
        #   - Tuples to mutable arrays
        #   - Dictionaries into name/value list
        # The user does not have access to these collections
        # so they can't mutate them, so there is no need to copy
        collection = poly_list(collection)
    length = len(collection)
    if length:
        meta = { }
        # The value and meta information are local to the loop
        ctx.dd.push_frame([(var_path, None), (LOOP_META_PATH, meta)])
        try:
            for i, value in enumerate(collection.copy() if isinstance(collection, list) else collection):
                # Update the meta information
                set_loop_meta(meta, i, length)
                # And the value itself
                ctx.set_var(value, *var_path)
                try:
                    ctx.dispatch_statements(statement.children[2:])
                except VgrStatementBreak as e:
                    e.validate_for_block(BlockType.FOR_LOOP)
                    return
                except VgrStatementContinue as e:
                    e.validate_for_block(BlockType.FOR_LOOP)
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
            return self._const_token(token, ConstantsNormalizer.tolerant_literal_eval(ConstantsNormalizer.normalize_outer_quotes(token.value)))
        except ValueError as e:
            raise VgrRuntimeError(token, e) from e
        except SyntaxError as e:
            raise VgrRuntimeError(token, ValueError(str(e.msg).strip())) from e

    # The None/Null constant
    @v_args(tree=True)
    def vnone(self, tree: Tree): return self._const_tree(tree, None)

    # Boolean constants
    @v_args(tree=True)
    def vtrue(self, tree: Tree): return self._const_tree(tree, True)

    @v_args(tree=True)
    def vfalse(self, tree: Tree): return self._const_tree(tree, False)

    # Numeric figurative constants
    @v_args(tree=True)
    def vnan(self, tree: Tree): return self._const_tree(tree, math.nan)

    @v_args(tree=True)
    def vzero(self, tree: Tree): return self._const_tree(tree, 0)

    @v_args(tree=True)
    def vinf(self, tree: Tree): return self._const_tree(tree, math.inf)

    # Character figurative constants
    @v_args(tree=True)
    def vcolon(self, tree: Tree): return self._const_tree(tree, ':')

    @v_args(tree=True)
    def vcomma(self, tree: Tree): return self._const_tree(tree, ',')

    @v_args(tree=True)
    def vnewline(self, tree: Tree): return self._const_tree(tree, '\n')

    @v_args(tree=True)
    def vperiod(self, tree: Tree): return self._const_tree(tree, '.')

    @v_args(tree=True)
    def vquote(self, tree: Tree): return self._const_tree(tree, '"')

    @v_args(tree=True)
    def vspace(self, tree: Tree): return self._const_tree(tree, ' ')

    @v_args(tree=True)
    def vtab(self, tree: Tree): return self._const_tree(tree, '\t')

    # Numeric constants
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

    @staticmethod
    def normalize_outer_quotes(s: str) -> str:
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

    @staticmethod
    def tolerant_literal_eval(s: str) -> str:
        try:
            return ConstantsNormalizer.quiet_literal_eval(s)
        except (SyntaxError, ValueError) as e:
            # Raw string should not have any problems with bad
            # backslash problems, so must be something we can't fix
            if s[0].lower() == 'r': raise e
            # escape stray backslashes not part of valid escape sequences
            try:
                safe = re.sub(r'(?<!\\)\\(?![\\abfnrtv\'"xuU0-9])', r'\\\\', s)
                return ConstantsNormalizer.quiet_literal_eval(safe)
            except (SyntaxError, ValueError):
                # that didn't fix it, so treat it as a
                # raw string and let any problems flow upward
                return ConstantsNormalizer.quiet_literal_eval('r' + s)

    @staticmethod
    def quiet_literal_eval(s: str) -> str:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning) # older
            warnings.simplefilter("ignore", SyntaxWarning) # newer
            return ast.literal_eval(s)

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
    'declare':           execute_declare,
    'declare_local':     execute_declare_local,
    'declare_global':    execute_declare_global,
    'def_function':      execute_def_function,
    'echo':              execute_echo,
    'exit':              execute_exit,
    'foreach':           execute_foreach,
    'forever':           execute_forever,
    'if':                execute_if,
    'include':           execute_include,
    'list_append':       execute_list_append,
    'list_insert':       execute_list_insert,
    'list_prepend':      execute_list_prepend,
    'list_remove_first': execute_list_remove_first,
    'list_remove_last':  execute_list_remove_last,
    'list_remove':       execute_list_remove,
    'list_replace':      execute_list_replace,
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
        # See builtins/common for the bound_ops decorator
        if hasattr(func, 'bound_ops'):
            for op in func.bound_ops:
                entries[op] = (func, op.lower().replace(' ', ''), (func.__doc__ or '').lower())
    return entries

class DefaultExecContext(ExecContext):

    _DEFAULT_PARSE_START = 'opt_statements'

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
    def var_exists(self, *path: str) -> tuple[bool, str, Any]: return self.dd.var_exists(*path)

    def set_var_user(self, data: Any, /, *path: str):
        """*deprecated*"""
        return self.dd.set_var_user(data, *path)

    def eval_expr(self, expr: Any) -> Any: return eval_expr(self, expr)
    def eval_expr_or_const(self, expr: Any) -> Any: return eval_expr_or_const(self, expr)

    def eval_to_str(self, expr: Tree, name: str, allow_none: bool=False) -> str:
        """Helper that makes sure you got a string back from an expression"""
        rc = self.eval_expr(expr)
        if rc is None and allow_none: return None
        # TODO should we not convert numbers to a string?
        if not isinstance(rc, str):
            raise VgrRuntimeError(expr, TypeError(f'{name} must be a string; found {poly_type(rc)!r}'))
        return rc

    def eval_filename_expr(self, expr: Any, allow_none: bool=False) -> str:
        """Helper that gets a string that should be a relative filename"""
        # TODO better error handling?
        return verify_relative_path(self.eval_to_str(expr, 'File name', allow_none))

    def eval_to_int(self, expr: Tree, name: str, allow_none: bool=False) -> int:
        rc = self.eval_expr(expr)
        if rc is None and allow_none: return None
        if isinstance(rc, (bool, int, float)): return int(rc)
        # TODO still a problem with None?
        if isinstance(rc, str):
            try:
                return poly_int(rc)
            except ValueError as e:
                raise VgrRuntimeError(expr, str(e)) from e
        raise VgrRuntimeError(expr, TypeError(f'{name} must be an integer; found {poly_type(rc)!r}'))

    def eval_to_number(self, expr: Tree, name: str, allow_none: bool=False):
        rc = self.eval_expr(expr)
        # TODO better error handling including None check
        if isinstance(rc, str): return poly_number(rc)
        if rc is None and allow_none: return None
        if isinstance(rc, bool): return int(rc)
        if isinstance(rc, (int, float)): return rc
        raise VgrRuntimeError(expr, TypeError(f'{name} must be a number; found {poly_type(rc)!r}'))

    def eval_to_bool(self, expr: Tree, name: str, allow_none: bool=False) -> bool:
        # TODO see other conv routines
        rc = self.eval_expr(expr)
        if rc is None and allow_none: return None
        if not isinstance(rc, (bool, int, float, str)):
            raise VgrRuntimeError(expr, TypeError(f'{name} must be a boolean; found {poly_type(rc)!r}'))
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

    def execute_statements(self, statement_text: str, origin: str, start: str=None) -> None:
        """Parse the text and execute the resulting statements"""
        if statement_text and not statement_text.isspace():
            SSM.push(origin, statement_text)
            # the <...> notation is used to indicate cmd line, stdin, etc
            # which don't really have a file name.
            # the source stack is strictly for file name context
            origin = '' if origin.startswith('<') and origin.endswith('>') else origin
            if origin: self.source_stack.insert(0, origin)
            try:
                tree = self._parser.parse(statement_text, start=start or self._DEFAULT_PARSE_START)
                # NB: this assumes that a user provided "start" is a single statement
                self.dispatch_statements(tree.children if start is None else [tree])
            except exceptions.LarkError as e:
                raise VgrException(e, e, *SSM.current) from e
            finally:
                if origin: self.source_stack.pop(0)
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
