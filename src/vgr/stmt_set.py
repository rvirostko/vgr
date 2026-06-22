"""
Includes the implemenation for SET/UNSET, MOVE, and LOAD FROM.
"""

from io import TextIOWrapper
from typing import Any
import os

from lark import Tree, Token

from .app_exceptions import VgrRuntimeError
from .builtins import (
    bound_ops,
    dict_remove_key,
    dict_set_key_value,
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
    poly_get_keys,
    poly_mod,
    poly_mul,
    poly_number,
    poly_plural,
    poly_pow,
    poly_repr,
    poly_shl,
    poly_shorten,
    poly_shr,
    poly_sub,
    poly_type,
)
from .dd_config import (
    clear_includes,
    dd_init,
    get_user_args,
    set_user_args,
)
from .encoding import parse_encoding
from .evaluate import do_set, do_unset, get_writable_var_path
from .exec_context import ExecContext
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

def _inplace_add_shim(x: Any, y: Any) -> Any:
    if isinstance(x, list):
        if isinstance(y, list):
            x.extend(y)
        else:
            x.append(y)
        return x
    return poly_add(x, y)

_SET_OP = {
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
**Modify a variable's existing value**

* Set *variable* [= | To] *expression* &emsp; *Assignment*
* Set *variable* += *expression* &emsp;  *Addition*
* Set *variable* -= *expression* &emsp;  *Subtraction*
* Set *variable* *= *expression* &emsp;  *Multiplication*
* Set *variable* /= *expression* &emsp;  *Division*
* Set *variable* %= *expression* &emsp;  *Modulo*
* Set *variable* **= *expression* &emsp; *Power*
* Set *variable* &= *expression* &emsp;  *Bit And*
* Set *variable* |= *expression* &emsp;  *Bit Or*
* Set *variable* ^= *expression* &emsp;  *Bit Xor*
* Set *variable* <<= *expression* &emsp; *Bit Shift Left*
* Set *variable* >>= *expression* &emsp; *Bit Shift Right*

Not that when `+=` is used with two lists, the lists are concatenated.

Multiple assingments can be performed by separating them with commas.

```vgr
Set a To 5, b To 3
Set a *= b
Exhibit a b
a = 15
b = 3
```

Also see the `Assign`, `Add`, `Subtract`, `Multiply`, and `Divide` statements.
"""
    i = 0
    last = len(statement.children)
    while i < last:
        var_path = get_writable_var_path(ctx, statement.children[i])
        i += 1
        if isinstance(statement.children[i], Token) and statement.children[i].type == 'SET_OP':
            op = _SET_OP[statement.children[i].value.lower()]
            i += 1
            new_value = op(ctx.get_var(*var_path), ctx.eval_expr(statement.children[i]))
        else:
            new_value = ctx.eval_expr(statement.children[i])
        i += 1
        do_set(ctx, new_value, *var_path)

@bound_ops("Assign")
def execute_assign(ctx: ExecContext, statement: Tree) -> None:
    """
**Modify a variable's existing value**

* Assign *expression* To *variable*
* Assign *expression* To *variable*[, *expression* To *variable*]&hellip;

```vgr
Assign 5 To a, 3 To b
Set a *= b
Exhibit a b
a = 15
b = 3
```

Also see the `Set` statement.
"""
    for i in range(0, len(statement.children), 2):
        var_path = get_writable_var_path(ctx, statement.children[i + 1])
        new_value = ctx.eval_expr(statement.children[i])
        do_set(ctx, new_value, *var_path)

@bound_ops("Set Corresponding")
def execute_set_corresponding(ctx: ExecContext, statement: Tree) -> None:
    """
**Assign elements of one dictionary to another**

* Set Corresponding *expression* In [Dictionary] *variable*

This works with dictionaries, copying attributes from the
evaluated *expression* to *variable* if the attribute already exists
in *variable*.

If *variable* does not exist or `None` the operation is skipped.
Also, if *expression* does not resolve to a dictionary, the
operation is skipped.

```vgr
Assign {"x": 1, "y": 2, "z": 3} To a
Assign {"w": 5, "x": 10} To b
Set Corresponding b In a
Exhibit a
a.x = 10
a.y = 2
a.z = 3
```

Also see `Set` and `Add()` for combining dictionaries
"""
    src_value = ctx.eval_expr(statement.children[0])
    var_path = get_writable_var_path(ctx, statement.children[1])
    dest_value = ctx.get_var(*var_path)
    if isinstance(src_value, dict) and isinstance(dest_value, dict):
        dest_value.update({k: src_value[k] for k in src_value if k in dest_value.keys()})
        do_set(ctx, dest_value, *var_path)

@bound_ops("Set Up")
def execute_set_up(ctx: ExecContext, statement: Tree) -> None:
    """
**Increment a counter by an amount**

* Set *variable* Up By *expression*

If *variable* does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar operation.

```vgr
Set counter To 5
Repeat 4 Times
    Print counter, ":", counter ** 2
    Set counter Up By counter * 1.5
End-Repeat

5 : 25
12.5 : 156.25
31.25 : 976.5625
78.125 : 6103.515625
```

Also see `Set Down`, `-`, and `Set`
"""
    var_path = get_writable_var_path(ctx, statement.children[0])
    x = poly_number(ctx.get_var(*var_path)) or 0
    y = poly_number(ctx.eval_expr(statement.children[1])) or 0
    do_set(ctx, poly_add(x, y), *var_path)

@bound_ops("Set Down")
def execute_set_down(ctx: ExecContext, statement: Tree) -> None:
    """
**Deccrement a counter by an amount**

* Set *variable* Down By *expression*

If *variable* does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar operation.

```vgr
Set counter To 5
Repeat 4 Times
    Print counter, ":", counter ** 2
    Set counter Down By counter * .5
End

5 : 25
2.5 : 6.25
1.25 : 1.5625
0.625 : 0.390625
```

Also see `Set Up`, `+`, and `Set`
"""
    var_path = get_writable_var_path(ctx, statement.children[0])
    x = poly_number(ctx.get_var(*var_path)) or 0
    y = poly_number(ctx.eval_expr(statement.children[1])) or 0
    do_set(ctx, poly_sub(x, y), *var_path)

@bound_ops("Set-Key")
def execute_set_key_value(ctx: ExecContext, statement: Tree) -> None:
    """
**Traverse a path in a dictionary and sets a value**

* Set-Key *path* In [Dictionary] *variable*
* Set-Key *path* In [Dictionary] *variable* [= | To] *expression*

The *variable* must either be a dictionary or list.
If it does not exist, it will be created as a dictionary.

If no *expression* is provided, the value `None` will be used.

The *path* can be:

* A string, boolean, integer, or float
* A list composed of path components

> **Note**\\
> The `Set-Key` statement operates directly on data.
> While `SetKeyValue()` performs the same operations, it
> will create and return a *copy* of the original contents.

```vgr
Set d To {"a": 1}
Set-Key "b" In d To 2 → {"a": 1, "b": 2}
Set-Key "c.d" In d To 3 → {"a": 1, "b": 2, "c": {"d": 3}}

Set a To [ {"a": 1}, {"b": 2} ]
Set-Key ["c", "d"] In a To 3 →
    [{"a": 1, "c": {"d": 3}}, {"b": 2, "c": {"d": 3}}]
```

Also see `Remove-Key` and `SetKeyValue()`
"""
    key_path_expr = statement.children[0]
    key_path = ctx.eval_expr_or_const(key_path_expr)
    var_path_expr = statement.children[1]
    var_path = get_writable_var_path(ctx, var_path_expr)
    new_value = ctx.eval_expr(statement.children[2]) if len(statement.children) > 2 else None
    exists, _true_path, data = ctx.var_exists(*var_path)
    if not exists or data is None:
        data = {}
        do_set(ctx, data, *var_path)
    else:
        if not isinstance(data, (list, dict)):
            raise VgrRuntimeError(var_path_expr, TypeError(f"Cannot alter keys in type {poly_type(data)!r}"))
    try:
        dict_set_key_value(data, key_path, new_value, False)
    except TypeError as e:
        # as we have checked the var_path and the value can be anything
        # the key_path is the likely culprit
        raise VgrRuntimeError(key_path_expr, e) from e
    if ctx.verbose: ctx.print_verbose('Set Key', repr(key_path), 'In', '.'.join(var_path), 'To', poly_shorten(repr(new_value)))

@bound_ops("Remove-Key")
def execute_remove_key(ctx: ExecContext, statement: Tree) -> None:
    """
**Remove a key from a dictionary**

* Remove-Key *path* From [Dictionary] *variable*

The *value* must either be a dictionary, a list, or `None`.

The *path* can be:

* A string, boolean, intger, or float
* A list composed of path components

> **Note**\\
> The `Remove-Key` statement operates directly on data.
> While `RemoveKey()` performs the same operations, it
> will create and return a *copy* of the original contents.

```vgr
Set d To {"a": 1, "b": 2}
Remove-Key "a" From d → {"b": 2}

Set a To [ {"a": 1}, {"b": 2} ]
Remove-Key "b" From a → [{"a": 1}, {}]
```

Also see `Set-Key` and `RemoveKey()`
"""
    key_path_expr = statement.children[0]
    key_path = ctx.eval_expr_or_const(key_path_expr)
    var_path_expr = statement.children[1]
    var_path = get_writable_var_path(ctx, var_path_expr)
    exists, _true_path, data = ctx.var_exists(*var_path)
    if exists and data is not None:
        if not isinstance(data, (list, dict)):
            raise VgrRuntimeError(var_path_expr, TypeError(f"Cannot alter keys in type {poly_type(data)!r}"))
        try:
            dict_remove_key(data, key_path, False)
        except TypeError as e:
            # as we have checked the var_path and the value can be anything
            # the key_path is the likely culprit
            raise VgrRuntimeError(key_path_expr, e) from e
        if ctx.verbose: ctx.print_verbose('Removed Key', repr(key_path), 'From', '.'.join(var_path))

@bound_ops("Unset")
def execute_unset(ctx: ExecContext, statement: Tree) -> None:
    """
**Remove one or more variables**

* Unset *variable*[, *variable*]&hellip;

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
* Reset *option*[, *option*]&hellip;

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
                'keys':     poly_get_keys(data),
                'records':  len(data) if isinstance(data, list) else 1
            })
