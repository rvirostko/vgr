"""
Includes the implemenation for SET/UNSET, MOVE, and LOAD FROM.
"""

from io import TextIOWrapper
from typing import Any
import csv
import json
import os

from lark import Tree, Token

from app_exceptions import VgrRuntimeError
from data_dict import DataDictionary
from dd_config import do_assignment, do_set, do_unset, _ARG_PREFIX, dd_set_awk_params
from evaluate import eval_expr, eval_filename_expr, var_name_path
from mathpak import poly_add, poly_sub, poly_mul, poly_div, poly_fdiv, poly_mod, poly_pow
from mathpak import poly_bit_and, poly_bit_or, poly_bit_xor, poly_shl, poly_shr, bound_ops
from redir import print_stderr, shorten, close_all_redirects

@bound_ops("Set")
def execute_set(dd: DataDictionary, statement: Tree) -> None:
    """
**Assign a value to a variable or modify a variable's existing value**

* Set _variable_ [= | To] _expression_ [;]
* Set _variable_ += _expression_ [;] -- Addition
* Set _variable_ -= _expression_ [;] -- Subtraction
* Set _variable_ *= _expression_ [;] -- Multiplication
* Set _variable_ /= _expression_ [;] -- Division
* Set _variable_ //= _expression_ [;] -- Floor Division
* Set _variable_ %= _expression_ [;] -- Modulo
* Set _variable_ **= _expression_ [;] -- Power
* Set _variable_ &= _expression_ [;] -- Bit And
* Set _variable_ |= _expression_ [;] -- Bit Or
* Set _variable_ ^= _expression_ [;] -- Bit Xor
* Set _variable_ <<= _expression_ [;] -- Bit Shift Left
* Set _variable_ >>= _expression_ [;] -- Bit Shift Right

"""
    path = var_name_path(statement.children[0])
    expr = statement.children[1]
    do_assignment(dd, expr, eval_expr(dd, expr), path)

@bound_ops("Unset")
def execute_unset(dd: DataDictionary, statement: Tree) -> None:
    """
**Remove a variable**

* Unset _variable_ [, _variable_]... [;]
"""
    for item in statement.children:
        do_unset(dd, *var_name_path(item))

@bound_ops("Reset")
def execute_reset(dd: DataDictionary, statement: Tree) -> None:
    """
**Reset global state to initial conditions

* Reset _option_ [, _option_]... [;]

Where _option_ is-
* Data - Resets all user set data except for user arguments
  and the settings for Debug, Verbose, and Echo
* Args - Resets user arguments and the settings
  for Debug, Verbose, and Echo
* Output - Resets all output redirection
* All - Resets all of the above

"""
    o_verbose = dd.verbose
    for opt in statement.children:
        s = str(opt.data).casefold()
        if s in ('all', 'output'):
            if o_verbose: print_stderr('Resetting Output/Error redirection')
            close_all_redirects()
        if s in ('all', 'data'):
            if o_verbose: print_stderr('Resetting all user data')
            t_args = dd.get_var(_ARG_PREFIX)
            dd.reset()
            dd.set_var(t_args, _ARG_PREFIX)
        if s in ('all', 'args'):
            if o_verbose: print_stderr(f'Reseting {repr(_ARG_PREFIX)} settings')
            dd.unset_var(_ARG_PREFIX)
            dd.debug = False
            dd.verbose = False
            dd.echo = False
            dd_set_awk_params(dd)

_IN_PLACE_OP = {
    "+=":  poly_add,
    "-=":  poly_sub,
    "*=":  poly_mul,
    "/=":  poly_div,
    "//=": poly_fdiv,
    "%=":  poly_mod,
    "**=": poly_pow,
    "&=":  poly_bit_and,
    "|=":  poly_bit_or,
    "^=":  poly_bit_xor,
    "<<=": poly_shl,
    ">>=": poly_shr,
}

# Doc combined with set
def execute_set_in_place(dd: DataDictionary, statement: Tree) -> None:
    path = var_name_path(statement.children[0])
    op = _IN_PLACE_OP[statement.children[1].value]
    expr = statement.children[2]
    do_assignment(dd, expr, op(dd.get_var_user(*path), eval_expr(dd, expr)), path)

@bound_ops("Swap")
def execute_swap(dd: DataDictionary, statement: Tree) -> None:
    """
**Exchange the values of two variables**

* Swap [Varaible] _x_ With _y_ [;]
* Swap [Variables] _x_ And _y_ [;]

Both variables must _not_ be immutable
"""
    path1 = dd.validate_user_set_path(*var_name_path(statement.children[0]))
    path2 = dd.validate_user_set_path(*var_name_path(statement.children[1]))
    temp = dd.get_var_user(*path1)
    do_set(dd, dd.get_var_user(*path2), *path1)
    do_set(dd, temp, *path2)

@bound_ops("Load", "Load-From")
def execute_load_from(dd: DataDictionary, statement: Tree) -> None:
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
    path = var_name_path(statement.children[0])
    fn_child = statement.children[1]
    filename = eval_filename_expr(dd, fn_child)
    dtype = load_data_type(filename, statement.children[2] if len(statement.children) > 2 else None)
    # TODO need to have an encoding param
    # defaults to utf-8-sig
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            data, fieldnames = load_file_as(f, dtype)
            dd.set_var_user(data, *path)
    except Exception as e:
        raise VgrRuntimeError(fn_child, ValueError(f'While reading {repr(filename)}: {str(e)}')) from e
    if dd.verbose:
        if isinstance(data, list):
            length = len(data)
            print_stderr('Loaded', '.'.join(path), 'With', length, 'Records' if length != 1 else 'Record')
        else:
            print_stderr('Loaded', '.'.join(path), 'With', shorten(repr(data)))
        if fieldnames and dd.verbose: print_stderr('Fieldnames :', '', ', '.join(repr(f) for f in fieldnames))

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
    raise ValueError(f'Unknown file content type {repr(dtype)}') # SNO

def _info_from_csv(reader: csv.DictReader) -> tuple:
    return (list(reader), reader.fieldnames or [])

def _info_from_json(data: Any) -> tuple:
    sample = data[0] if isinstance(data, list) and data else data
    return (data, list(sample.keys()) if isinstance(sample, dict) else [])
