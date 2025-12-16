"""
Includes the implemenation for SET/UNSET, MOVE, and LOAD FROM.
"""

from io import TextIOWrapper
from typing import Any
import configparser
import csv
import json
import os

import hcl2
import yaml

from lark import Tree, Token

from .app_exceptions import VgrRuntimeError
from .user_callable import UserFunction
from .dd_config import (
    clear_includes,
    dd_init,
    get_user_args,
    set_user_args,
)
from .evaluate import do_set, do_unset, get_writable_var_path, create_param_list
from .exec_context import ExecContext
from .mathpak import (
    bound_ops,
    poly_add,
    poly_bit_and,
    poly_bit_or,
    poly_bit_xor,
    poly_div,
    poly_getkeys,
    poly_mod,
    poly_mul,
    poly_plural,
    poly_pow,
    poly_repr,
    poly_shl,
    poly_shr,
    poly_sub,
)
from .redir import close_all_redirects

_LOAD_META_PATH = ('$load',)

_EXTENSION_MAP = {
    '.csv':    'csv_file',
    '.hcl':    'hcl_file',
    '.ini':    'ini_file',
    '.json':   'json_object',
    '.tf':     'hcl_file',
    '.tfvars': 'hcl_file',
    '.yaml':   'yaml_file',
    '.yml':    'yaml_file',
}

@bound_ops("Set")
def execute_set(ctx: ExecContext, statement: Tree) -> None:
    """
**Assign a value to a variable or modify a variable's existing value**

* Set _variable_ [= | To] _expression_ [;]
* Set _variable_ [= | To] (_arg_...) -> _expression_ _Arrow_ _Function_
* Set _variable_ [= | To] (_arg_...) -> Compile(_expression_) _Dynamic_ _Arrow_ _Function_
* Set _variable_ += _expression_ [;] _Addition_
* Set _variable_ -= _expression_ [;] _Subtraction_
* Set _variable_ *= _expression_ [;] _Multiplication_
* Set _variable_ /= _expression_ [;] _Division_
* Set _variable_ %= _expression_ [;] _Modulo_
* Set _variable_ **= _expression_ [;] _Power_
* Set _variable_ &= _expression_ [;] _Bit And_
* Set _variable_ |= _expression_ [;] _Bit Or_
* Set _variable_ ^= _expression_ [;] _Bit Xor_
* Set _variable_ <<= _expression_ [;] _Bit Shift Left_
* Set _variable_ >>= _expression_ [;] _Bit Shift Right_

Arrow Functions may define zero or more arguments, but unlike those
defined with `Function` are composed entirely in an expression.

When `+=` is used with two lists, the lists are concatenated.

**Examples**
```vgr
Set a To 5
Set b To 3
Set a *= b
Exhibit a b
a = 15
b = 3
```
```vgr
Set fn(a,b) -> a * b
Exhibit fn
fn = (a,b)→a * b
Print fn
a * b
Print @fn(5,3)
15
Set c = fn
Print @c(5,3)
15
```
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
**Reset global state to initial conditions**

* Reset _option_ [, _option_]... [;]

Where _option_ is-
* Data - Resets all user set data except for user arguments
  and the settings for Debug, Verbose, and Echo
* Includes - Clears the list of `@Include` files
* Args - Resets user arguments stored in _args_ list
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
            t_args = get_user_args(ctx)
            dd_init(ctx.dd)
            set_user_args(ctx, t_args)
        if s in ('all', 'includes'):
            ctx.print_verbose('Clearing includes')
            clear_includes()
        if s in ('all', 'args'):
            ctx.print_verbose('Resetting user args')
            set_user_args(ctx, None)
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

Both variables must be mutable
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

* Load _variable_ From [File] _file_ [;]
* Load _variable_ From [File] _file_ CSV [;]
* Load _variable_ From [File] _file_ HCL [;]
* Load _variable_ From [File] _file_ INI [;]
* Load _variable_ From [File] _file_ JSON [Object] [;]
* Load _variable_ From [File] _file_ JSON [Object] Per Line [;]
* Load _variable_ From [File] _file_ Text [;]
* Load _variable_ From [File] _file_ Text Lines [;]
* Load _variable_ From [File] _file_ YAML [;]

The _file_ argument is a string expression for the file to be loaded

If no type—_JSON_, _CSV_, etc—is included, the type is inferred from the file's extension
with _Text_ as the default.

After the file is loaded, the following metadata values are available:

* $load.filename - name of the loaded file
* $load.format - source format: json, yaml, hcl, ini, csv, text
* $load.keys - list of top-level keys if applicable
* $load.records - number of top-level records

`Windows Note`: If you hard code paths, please use the slash as a universal
directory separator. Since the backslash is an escape character, if you use
it in a string, you will either need to double it or use a _raw string_.

"""
    var_path = get_writable_var_path(ctx, statement.children[0])
    fn_child = statement.children[1]
    filename = ctx.eval_filename_expr(fn_child)
    dtype = load_data_type(filename, statement.children[2] if len(statement.children) > 2 else None)
    # TODO need to have an encoding param
    encoding = 'utf-8-sig'
    try:
        with open(filename, 'r', encoding=encoding) as f:
            data, metadata = load_file_as(filename, f, dtype)
            ctx.set_var(data, *var_path)
            # Try to make the meta variable a local if possible
            ctx.dd.declare_var(ctx.dd.in_local_frame, *_LOAD_META_PATH)
            ctx.set_var(metadata, *_LOAD_META_PATH)
    except Exception as e:
        raise VgrRuntimeError(fn_child, OSError(f'While reading {filename!r}: {str(e)}')) from e
    if ctx.verbose:
        length = metadata['records']
        ctx.print_verbose('Loaded', '.'.join(var_path), 'With', length, poly_plural(length, 'Records', 'Record'))
        if len(metadata['keys']) > 0: ctx.print_verbose('Keys :', '', ', '.join(poly_repr(key) for key in metadata['keys']))

def load_data_type(filename: str, token: Token) -> str:
    """Returns one of:

* csv_file
* hcl_file
* json_object
* json_objects
* text_file
* text_lines
* yaml_file
"""
    if token is not None: return token.data
    ext = os.path.splitext(filename)[1].lower()
    return _EXTENSION_MAP.get(ext, 'text_file')

def load_file_as(filename: str, file: TextIOWrapper, dtype: str) -> tuple:
    """Read the file in according to the type, which comes for load_file_type().
Returns a tuple with the data and metadata used for the $load variable:

* $load.filename - name of the loaded file
* $load.format   - logical format: json, yaml, hcl, ini, csv, text
* $load.keys     - list of top-level keys
* $load.records  - number of top-level records

"""
    data = None
    keys = None
    if dtype.startswith('text_'):
        data = file.read()
        data = data.splitlines() if dtype == 'text_lines' else data
    elif dtype == 'json_object':
        data = json.load(file)
    elif dtype == 'json_objects':
        data = [json.loads(line) for line in file if line.strip()]
    elif dtype == 'csv_file':
        reader = csv.DictReader(file)
        keys = reader.fieldnames or []
        data = list(reader)
    elif dtype == 'yaml_file':
        data = yaml.safe_load(file)
    elif dtype == 'hcl_file':
        data = hcl2.load(file)
    elif dtype == 'ini_file':
        parser = configparser.ConfigParser()
        parser.read_file(file)
        data = { section: dict(parser.items(section)) for section in parser.sections() }
    else:
        raise ValueError(f'Unknown file content type {dtype!r}') # SNO
    return (data,
            {
                'filename': filename,
                'format':   dtype.split('_')[0],
                'keys':     poly_getkeys(data) if keys is None else keys,
                'records':  len(data) if isinstance(data, list) else 1
            })
