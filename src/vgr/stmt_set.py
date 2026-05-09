"""
Includes the implemenation for SET/UNSET, MOVE, and LOAD FROM.
"""

from io import TextIOWrapper
from typing import Any
import os

from lark import Tree

from .app_exceptions import VgrRuntimeError
from .builtins import (
    bound_ops,
    parse_csv,
    parse_hcl,
    parse_ini,
    parse_json,
    parse_yaml,
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
from .dd_config import (
    clear_includes,
    dd_init,
    get_user_args,
    set_user_args,
)
from .encoding import parse_encoding
from .evaluate import do_set, do_unset, get_writable_var_path, create_param_list
from .exec_context import ExecContext
from .redir import close_all_redirects
from .user_callable import UserFunction

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

def _inplace_add_shim(x: Any, y: Any) -> Any:
    if isinstance(x, list):
        if isinstance(y, list):
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

@bound_ops("Set")
def execute_set(ctx: ExecContext, statement: Tree) -> None:
    """
**Assign a value to a variable or modify a variable's existing value**

* Set *variable* [= | To] *expression* &emsp; *Assignment*
* Set *variable* += *expression* &emsp; *Addition*
* Set *variable* -= *expression* &emsp; *Subtraction*
* Set *variable* *= *expression* &emsp; *Multiplication*
* Set *variable* /= *expression* &emsp; *Division*
* Set *variable* %= *expression* &emsp; *Modulo*
* Set *variable* **= *expression* &emsp; *Power*
* Set *variable* &= *expression* &emsp; *Bit And*
* Set *variable* |= *expression* &emsp; *Bit Or*
* Set *variable* ^= *expression* &emsp; *Bit Xor*
* Set *variable* <<= *expression* &emsp; *Bit Shift Left*
* Set *variable* >>= *expression* &emsp; *Bit Shift Right*
* Set *variable* (*arg*&hellip;) [-> | →] *expression* &emsp; *Arrow Function*


Not that when `+=` is used with two lists, the lists are concatenated.

```vgr
Set a To 5
Set b To 3
Set a *= b
Exhibit a b
a = 15
b = 3
```

Also see the `Add`, `Subtract`, `Multiply`, and `Divide` statements.

See `Define Function` and `Call` for details on defining and calling *Arrow Functions* with `Set`
"""
    var_path = get_writable_var_path(ctx, statement.children[0])
    if len(statement.children) == 2:
        # <var> <expr> : direct assignment
        new_value = ctx.eval_expr(statement.children[1])
    else:
        # <var> <op> <expr> : modify existing value
        op = _IN_PLACE_OP[statement.children[1].value.lower()]
        new_value = op(ctx.get_var(*var_path), ctx.eval_expr(statement.children[2]))
    do_set(ctx, new_value, *var_path)

def execute_set_arrow(ctx: ExecContext, statement: Tree) -> None:
    """-documentation combined with Function-"""
    var_path = get_writable_var_path(ctx, statement.children[0])
    param_paths = create_param_list(ctx, statement.children[1])
    expr = statement.children[-1]
    do_set(ctx, UserFunction.from_expression(ctx.get_source(expr), expr, param_paths), *var_path)

def execute_compile_arrow(ctx: ExecContext, statement: Tree) -> None:
    """-documentation combined with Function-"""
    var_path = get_writable_var_path(ctx, statement.children[0])
    param_paths = create_param_list(ctx, statement.children[1])
    expr = statement.children[-1]
    do_set(ctx, UserFunction.compile(ctx, ctx.eval_expr(expr), param_paths), *var_path)

@bound_ops("Unset")
def execute_unset(ctx: ExecContext, statement: Tree) -> None:
    """
**Remove one or more variables**

* Unset *variable* [, *variable*]&hellip;

More than setting the variable to `None`, the variable is entirely removed.
To be removed, the variable must be mutable.

```vgr
Set a To 1
Set b To 2
Set c To 3
Exhibit a, b, c
a = 1
b = 2
c = 3

Unset a, c
Exhibit a, b, c
a = -not set-
b = 2
c = -not set-

Set t To {"a": 1, "b": 2, "c": 3}
Unset t.b
Print t
{'a': 1, 'c': 3}
```

Also see `Set` and `Reset`
"""
    for child in statement.children:
        do_unset(ctx, *get_writable_var_path(ctx, child))

@bound_ops("Reset")
def execute_reset(ctx: ExecContext, statement: Tree) -> None:
    """
**Reset global state to initial conditions**

* Reset
* Reset *option* [, *option*]&hellip;

Where *option* is

* Data - Resets all user set data except for user arguments
  and the settings for Debug, Verbose, and Echo
* Includes - Clears the list of `@Include` files
* Args - Resets user arguments stored in *args* list
* Output - Resets all output redirection
* All - Resets all of the above plus `Debug`, `Echo`, and `Verbose` settings

If no options are given, a `Reset All` is performed.

```vgr
Set a To 1
Set b To 2
Set c To 3
Exhibit a, b, c
a = 1
b = 2
c = 3

Reset Data
Exhibit a, b, c
a = -not set-
b = -not set-
c = -not set-
```

Also see `Set` and `Unset`
"""
    def _output():
        ctx.print_verbose('Resetting Output/Error redirection')
        close_all_redirects()
    def _data():
        ctx.print_verbose('Resetting all user data')
        # We preserve args but reset everything else
        t_args = get_user_args(ctx)
        dd_init(ctx.dd)
        set_user_args(ctx, t_args)
    def _includes():
        ctx.print_verbose('Resetting includes')
        clear_includes()
    def _args():
        ctx.print_verbose('Resetting user args')
        set_user_args(ctx, None)
    def _flags():
        ctx.print_verbose('Resetting Debug, Echo, and Verbose settings')
        ctx.debug = False
        ctx.echo = False
        ctx.verbose = False

    if len(statement.children) == 0:
        _output()
        _data()
        _includes()
        _args()
        _flags()
    else:
        for opt in statement.children:
            s = str(opt.data).casefold()
            if s in ('all', 'output'): _output()
            if s in ('all', 'data'): _data()
            if s in ('all', 'includes'): _includes()
            if s in ('all', 'args'): _args()
            if s in ('all'): _flags()

@bound_ops("Swap")
def execute_swap(ctx: ExecContext, statement: Tree) -> None:
    """
**Exchange the values of two variables**

* Swap *variable1* [With | And] *variable2*

Both variables must be mutable.

```vgr
Set a To 1
Set b To 2
Exhibit a, b
a = 1
b = 2

Swap a With b
Exhibit a, b
a = 2
b = 1
```

Also see `Set`
"""
    path1 = get_writable_var_path(ctx, statement.children[0])
    path2 = get_writable_var_path(ctx, statement.children[1])
    temp = ctx.get_var(*path1)
    do_set(ctx, ctx.get_var(*path2), *path1)
    do_set(ctx, temp, *path2)

@bound_ops("Load")
def execute_load_from(ctx: ExecContext, statement: Tree) -> None:
    """
**Assign a value to a variable from a file**

* Load *variable* From [File] *file_name*\\
  &emsp;&emsp;[Type [Is]] *file_type*\\
  &emsp;&emsp;[Encoding [Is] _encoding_]\\


The *file_name* argument is a string expression for the file to be loaded.

If a *file_type* is specified, it must be one of:

* CSV - The CSV data is read as a list of dictionaries, with the
  column headers as attribute names
* HCL - The data is read creating a dictionary
* INI - The INI sections are used to create a dictionary
* JSON [Object] - The data is a single JSON object;
  a dictionary is created
* JSON [Object] Per Line - The data is a text file with one
  JSON object per line; a list of dictionaries is created
* Text - The data is read as a string
* Text Lines - The data is read line-by-line, creating a list of strings
* YAML - The data is read creating a dictionary

If not specified, it is inferred from the file's extension
with _Text_ as the default.

Then optional _encoding_ is a string expression for the character encoding.
If none is specified, then _utf-8-sig_ is used as the default.

Both *file_type* and _encoding_ are optional and can be specified in any order.
For readability, they can be separated with commas.

After the data is loaded, the following metadata values are available:

* $load.filename - name of the loaded file
* $load.format - source format: json, yaml, hcl, ini, csv, text
* $load.keys - list of top-level keys if applicable
* $load.records - number of top-level records

```vgr
**TODO**
```

> **Windows Note**\\
> If you hard code paths, please use the slash as a universal
> directory separator. Since the backslash is an escape character, if you use
> it in a string, you will either need to double it or use a *raw string*.

Also see `ParseCSV()`, `ParseHCL()`, `ParseINI()`, `ParseJSON()`, and `ParseYAML()`
"""
    var_path = get_writable_var_path(ctx, statement.children[0])
    fn_child = statement.children[1]
    filename = ctx.eval_filename_expr(fn_child)
    ftype = None
    encoding = None
    for opt in statement.children[2:]:
        if opt.data == "encoding":
            encoding = parse_encoding(ctx, opt)
        else:
            ftype = opt.data
    try:
        with open(filename, 'r', encoding=encoding or 'utf-8-sig', errors='backslashreplace' if ctx.debug else 'replace') as f:
            data, metadata = load_file_as(filename, f, load_data_type(filename, ftype))
            ctx.set_var(data, *var_path)
            # Try to make the meta variable a local if possible
            ctx.dd.declare_var(ctx.dd.in_local_frame, *_LOAD_META_PATH)
            ctx.set_var(metadata, *_LOAD_META_PATH)
    except Exception as e:
        raise VgrRuntimeError(fn_child, OSError(f'While reading {filename!r}: {str(e)}')) from e
    if ctx.verbose:
        length = metadata['records']
        ctx.print_verbose('Loaded', '.'.join(var_path), 'With', length, poly_plural(length, 'Records', 'Record'))
        if len(metadata['keys']) > 0: ctx.print_verbose('Keys :', ', '.join(poly_repr(key) for key in metadata['keys']))

def load_data_type(filename: str, ftype: str) -> str:
    """Returns one of:

* csv_file
* hcl_file
* json_object
* json_objects
* text_file
* text_lines
* yaml_file
"""
    if ftype is not None: return ftype
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
    data = file.read()
    if dtype == 'text_file':
        pass # data alread read in
    elif dtype == 'text_lines':
        data = data.splitlines()
    elif dtype == 'json_object':
        data = parse_json(data)
    elif dtype == 'json_objects':
        data = [parse_json(line) for line in data.splitlines() if line.strip()]
    elif dtype == 'csv_file':
        data = parse_csv(data)
    elif dtype == 'yaml_file':
        data = parse_yaml(data)
    elif dtype == 'hcl_file':
        data = parse_hcl(data)
    elif dtype == 'ini_file':
        data = parse_ini(data)
    else:
        raise ValueError(f'Unknown file content type {dtype!r}') # SNO
    return (data,
            {
                'filename': filename,
                'format':   dtype.split('_')[0],
                'keys':     poly_getkeys(data),
                'records':  len(data) if isinstance(data, list) else 1
            })
