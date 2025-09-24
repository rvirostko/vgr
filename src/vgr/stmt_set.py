"""
Includes the implemenation for SET/UNSET, MOVE, and LOAD FROM.
"""

from io import TextIOWrapper
from typing import Any
import csv
import json
import os

from lark import Tree, Token

from .app_exceptions import VgrRuntimeError
from .user_callable import UserFunction
from .dd_config import dd_init, dd_init_args, _ARG_PREFIX
from .evaluate import do_set, do_unset, shorten, get_writable_var_path, create_param_list
from .exec_context import ExecContext
from .mathpak import (
    bound_ops,
    poly_add,
    poly_bit_and,
    poly_bit_or,
    poly_bit_xor,
    poly_div,
    poly_mod,
    poly_mul,
    poly_pow,
    poly_shl,
    poly_shr,
    poly_sub,
)
from .redir import close_all_redirects

@bound_ops("Set")
def execute_set(ctx: ExecContext, statement: Tree) -> None:
    """
**Assign a value to a variable or modify a variable's existing value**

* Set _variable_ [= | To] _expression_ [;]
* Set _variable_ [= | To] (_arg_...) -> _expression_ -- Arrow Function
* Set _variable_ [= | To] (_arg_...) -> Compile(_expression_) -- Dynamic Arrow Function
* Set _variable_ += _expression_ [;] -- Addition
* Set _variable_ -= _expression_ [;] -- Subtraction
* Set _variable_ *= _expression_ [;] -- Multiplication
* Set _variable_ /= _expression_ [;] -- Division
* Set _variable_ %= _expression_ [;] -- Modulo
* Set _variable_ **= _expression_ [;] -- Power
* Set _variable_ &= _expression_ [;] -- Bit And
* Set _variable_ |= _expression_ [;] -- Bit Or
* Set _variable_ ^= _expression_ [;] -- Bit Xor
* Set _variable_ <<= _expression_ [;] -- Bit Shift Left
* Set _variable_ >>= _expression_ [;] -- Bit Shift Right

"""
    var_path = get_writable_var_path(ctx, statement.children[0])
    expr = statement.children[1]
    do_set(ctx, ctx.eval_expr(expr), *var_path)

@bound_ops("Unset")
def execute_unset(ctx: ExecContext, statement: Tree) -> None:
    """
**Remove a variable**

* Unset _variable_ [, _variable_]... [;]
"""
    for child in statement.children:
        do_unset(ctx, *get_writable_var_path(ctx, child))

@bound_ops("Reset")
def execute_reset(ctx: ExecContext, statement: Tree) -> None:
    """
**Reset global state to initial conditions

* Reset _option_ [, _option_]... [;]

Where _option_ is-
* Data - Resets all user set data except for user arguments
  and the settings for Debug, Verbose, and Echo
* Args - Resets user arguments and the settings
  for Debug, Verbose, and Echo
* Output - Resets all output redirection
* All - Resets all of the above plus `Debug`, `Echo`, and `Verbose` settings

"""
    for opt in statement.children:
        s = str(opt.data).casefold()
        if s in ('all', 'output'):
            ctx.print_verbose('Resetting Output/Error redirection')
            close_all_redirects()
        if s in ('all', 'data'):
            ctx.print_verbose('Resetting all user data')
            # We preserve args but reset everything else
            t_args = ctx.get_var(_ARG_PREFIX)
            dd_init(ctx.dd)
            ctx.set_var(t_args, _ARG_PREFIX)
        if s in ('all', 'args'):
            if ctx.debug: ctx.print_verbose('Resetting', repr(_ARG_PREFIX), 'settings')
            dd_init_args(ctx.dd)
        if s in ('all'):
            ctx.print_verbose('Resetting Debug, Echo, and Verbose settings')
            ctx.debug = False
            ctx.echo = False
            ctx.verbose = False

def _inplace_add_shim(x: Any, y: Any) -> Any:
    if isinstance(x, (list, tuple)):
        if isinstance(y, (list, tuple)):
            x.extend(y)
        else:
            x.append(y)
        return x
    return poly_add(x, y)

_IN_PLACE_OP = {
    "+=":  _inplace_add_shim,
    "-=":  poly_sub,
    "*=":  poly_mul,
    "/=":  poly_div,
    "%=":  poly_mod,
    "**=": poly_pow,
    "&=":  poly_bit_and,
    "|=":  poly_bit_or,
    "^=":  poly_bit_xor,
    "<<=": poly_shl,
    ">>=": poly_shr,
}

def execute_set_in_place(ctx: ExecContext, statement: Tree) -> None:
    """-documentation combined with `set`-"""
    var_path = get_writable_var_path(ctx, statement.children[0])
    op = _IN_PLACE_OP[statement.children[1].value]
    expr = statement.children[2]
    do_set(ctx, op(ctx.get_var(*var_path), ctx.eval_expr(expr)), *var_path)

def execute_set_arrow(ctx: ExecContext, statement: Tree) -> None:
    """-documentation combined with `set`-"""
    var_path = get_writable_var_path(ctx, statement.children[0])
    param_paths = create_param_list(ctx, statement.children[1])
    expr = statement.children[-1]
    do_set(ctx, UserFunction.from_expression(ctx.get_source(expr), expr, param_paths), *var_path)

def execute_compile_arrow(ctx: ExecContext, statement: Tree) -> None:
    """-documentation combined with `set`-"""
    var_path = get_writable_var_path(ctx, statement.children[0])
    param_paths = create_param_list(ctx, statement.children[1])
    expr = statement.children[-1]
    do_set(ctx, UserFunction.compile(ctx, ctx.eval_expr(expr), param_paths), *var_path)

@bound_ops("Swap")
def execute_swap(ctx: ExecContext, statement: Tree) -> None:
    """
**Exchange the values of two variables**

* Swap [Varaible] _x_ With _y_ [;]
* Swap [Variables] _x_ And _y_ [;]

Both variables must _not_ be immutable
"""
    path1 = get_writable_var_path(ctx, statement.children[0])
    path2 = get_writable_var_path(ctx, statement.children[1])
    temp = ctx.get_var(*path1)
    do_set(ctx, ctx.get_var(*path2), *path1)
    do_set(ctx, temp, *path2)

@bound_ops("Load", "Load-From")
def execute_load_from(ctx: ExecContext, statement: Tree) -> None:
    """
**Assign a value to a variable from a file**

* Load _variable_ From [File] _expression_ [;]
* Load _variable_ From [File] _expression_ JSON [Object] [;]
* Load _variable_ From [File] _expression_ JSON [Object] Per Line [;]
* Load _variable_ From [File] _expression_ CSV [;]
* Load _variable_ From [File] _expression_ Text [;]
* Load _variable_ From [File] _expression_ Text Lines [;]

The _expression_ is resolved to string as file to be loaded

If no type is included, the type is inferred from the extension of the file
name with Text as the default.
"""
    var_path = get_writable_var_path(ctx, statement.children[0])
    fn_child = statement.children[1]
    filename = ctx.eval_filename_expr(fn_child)
    dtype = load_data_type(filename, statement.children[2] if len(statement.children) > 2 else None)
    # TODO need to have an encoding param
    # defaults to utf-8-sig
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            data, fieldnames = load_file_as(f, dtype)
            ctx.set_var(data, *var_path)
    except Exception as e:
        raise VgrRuntimeError(fn_child, OSError(f'While reading {filename!r}: {str(e)}')) from e
    if ctx.verbose:
        if isinstance(data, list):
            length = len(data)
            if ctx.verbose: ctx.print_verbose('Loaded', '.'.join(var_path), 'With', length, 'Records' if length != 1 else 'Record')
        else:
            if ctx.verbose: ctx.print_verbose('Loaded', '.'.join(var_path), 'With', shorten(repr(data)))
        if fieldnames and ctx.verbose: ctx.print_verbose('Fieldnames :', '', ', '.join(repr(f) for f in fieldnames))

def load_data_type(filename: str, token: Token) -> str:
    """Returns one of:
    * text_file
    * text_lines
    * json_object
    * json_objects
    * csv_file
    """
    if token is not None: return token.data
    ext = os.path.splitext(filename)[1].lower()
    return 'csv_file' if ext == '.csv' else 'json_object' if ext == '.json' else 'text_file'

def load_file_as(file: TextIOWrapper, dtype: str) -> tuple:
    """Read the file in according to the type, which comes for load_file_type()"""
    if dtype == 'text_file':
        return (file.read(), [])
    if dtype == 'text_lines':
        return (file.read().splitlines(), ['line'])
    if dtype == 'json_object':
        return _info_from_json(json.load(file))
    if dtype == 'json_objects':
        return _info_from_json([json.loads(line) for line in file if line.strip()])
    if dtype == 'csv_file':
        return _info_from_csv(csv.DictReader(file))
    raise ValueError(f'Unknown file content type {dtype!r}') # SNO

def _info_from_csv(reader: csv.DictReader) -> tuple:
    return (list(reader), reader.fieldnames or [])

def _info_from_json(data: Any) -> tuple:
    sample = data[0] if isinstance(data, list) and data else data
    return (data, list(sample.keys()) if isinstance(sample, dict) else [])
