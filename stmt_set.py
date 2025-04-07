"""
Includes the implemenation for SET/UNSET, MOVE, and LOAD FROM.
"""

from copy import deepcopy
from typing import Any
import csv
import json
import os

from lark import Tree, Token

from data_dict import DataDictionary
from dd_config import dd_path
from evaluate import eval_expr, eval_filename_expr
from mathpak import poly_add, poly_sub, poly_number
from redir import print_stderr, shorten

def execute_set(dd: DataDictionary, statement: Tree) -> None:
    """Assign a value to a variable.

* SET _variable_ [= | := | TO) _expression_ [;]
"""
    path = dd_path(statement.children[0])
    expr = statement.children[1]
    do_assignment(dd, expr, eval_expr(dd, expr), path)

def do_assignment(dd: DataDictionary, expr: Tree, value: Any, path: tuple[str]) -> None:
    """
    Use when you are doing an assignment (set) where you cannot be sure
    that the result is a reference to another mutable variable such as a list or dict.
    When it is, we need to make a copy before setting the value in the DD.
    """
    if isinstance(expr, Tree) and expr.data == 'var_ref' and isinstance(value, (list, dict)):
        value = deepcopy(value)
    do_set(dd, value, *path)

def execute_unset(dd: DataDictionary, statement: Tree) -> None:
    """Remove a variable.

* UNSET _variable_ [, _variable_]... [;]
"""
    for item in statement.children:
        path = dd_path(item)
        old_value = dd.unset_var_user(*path)
        if dd.verbose: print_stderr(dd, 'Removed', shorten(repr(old_value)), 'From', '.'.join(path))

def execute_inc(dd: DataDictionary, statement: Tree) -> None:
    """Increment a counter by an amount

* Set _variable_ Up By _expression_ [;]

If the variable does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar opertion.
"""
    path = dd_path(statement.children[0])
    x = poly_number(dd.get_var_user(*path)) or 0
    y = poly_number(eval_expr(dd, statement.children[1])) or 0
    do_set(dd, poly_add(x, y), *path)

def execute_dec(dd: DataDictionary, statement: Tree) -> None:
    """Deccrement a counter by an amount

* Set _variable_ Down By _expression_ [;]

If the variable does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar opertion.
"""
    path = dd_path(statement.children[0])
    x = poly_number(dd.get_var_user(*path)) or 0
    y = poly_number(eval_expr(dd, statement.children[1])) or 0
    do_set(dd, poly_sub(x, y), *path)

def execute_move_to(dd: DataDictionary, statement: Tree) -> None:
    """Assign a value to a variable.

* MOVE _expression_ TO _variable_ [;]
* MOVE CORRESPONDING _expression_ TO _variable_ [;]

The first form is equivalent to a SET operation.
The second form works with dictionaries, copying attribute from the
evaluated _expression_ to _variable_. If the variable does not exist,
is None or not a dictionary, a regular move is performed.
If _expression_ does not resolve to a dictionary, the corresponding
request is ignored and a regular move is performed.
"""
    corresponding = False
    start = 0
    fc = statement.children[0]
    if isinstance(fc, Token) and fc.value == 'corr':
        corresponding = True
        start = 1
    expr = statement.children[start]
    path = dd_path(statement.children[start + 1])
    src = eval_expr(dd, expr)
    dest = dd.get_var_user(*path) if corresponding else None
    if isinstance(src, dict) and isinstance(dest, dict):
        # Should end up here if corresponding was specified,
        # what we are moving is a dictionary, and the
        # destination existed and is also a dictionary
        dest.update({k: src[k] for k in src if k in dest.keys()})
        # This isn't strictly needed as we've done a modification in place
        # However, it does print out something in verbose, so we execute
        # for that side effect
        do_set(dd, dest, *path)
    else:
        # Either no corresponding, or either the src/dest is not a dict
        # This is like a "regular" set
        do_assignment(dd, expr, src, path)

def execute_load_from(dd: DataDictionary, statement: Tree) -> None:
    """Assign a value to a variable from a file.

* LOAD _variable_ FROM [FILE] _expression_ [;]
* LOAD _variable_ FROM [FILE] _expression_ JSON [OBJECT] [;]
* LOAD _variable_ FROM [FILE] _expression_ JSON [OBJECT] PER LINE [;]
* LOAD _variable_ FROM [FILE] _expression_ CSV [;]
* LOAD _variable_ FROM [FILE] _expression_ TEXT [;]

The _expression_ is resolved to string as file to be loaded

If no type is included, the type is inferred from the extension of the file
name with TEXT as the default.
"""
    path = dd_path(statement.children[0])
    filename = eval_filename_expr(dd, statement.children[1])
    dtype = load_data_type(filename, statement.children[2] if len(statement.children) > 2 else None)
    with open(filename, 'r', encoding='utf-8') as f:
        data, fieldnames = load_file_as(f, dtype)
        dd.set_var_user(data, *path)
    if dd.verbose:
        if isinstance(data, list):
            length = len(data)
            print_stderr(dd, 'Loaded', '.'.join(path), 'With', length, 'Records' if length != 1 else 'Record')
        else:
            print_stderr(dd, 'Loaded', '.'.join(path), 'With', shorten(repr(data)))
        if fieldnames: print_stderr(dd, 'Fieldnames :', '', ''.join(repr(f) for f in fieldnames))

def load_data_type(filename: str, token: Token) -> str:
    """Returns one of:
    * text_file
    * json_object
    * json_objects
    * csv_file
    """
    if token is not None: return token.data
    ext = os.path.splitext(filename)[1].lower()
    return 'csv_file' if ext == '.csv' else 'json_object' if ext == '.json' else 'text_file'

def load_file_as(file, dtype: str) -> tuple:
    """Read the file in according to the type, which comes for load_file_type()"""
    if dtype == 'text_file':
        return (file.read(), [])
    if dtype == 'json_object':
        return _info_from_json(json.load(file))
    if dtype == 'json_objects':
        return _info_from_json([json.loads(line) for line in file if line.strip()])
    if dtype == 'csv_file':
        return _info_from_csv(csv.DictReader(file))
    raise ValueError(f'Unknown file content type {repr(dtype)}') # SNO

def do_set(dd: DataDictionary, value: Any, *path) -> None:
    """
    After calculations are done, use this to set a value.
    Generates verbose output.
    """
    new_value = dd.set_var_user(value, *path)
    if dd.verbose: print_stderr(dd, 'Set', '.'.join(path), 'To', shorten(repr(new_value)))

def _info_from_csv(reader: csv.DictReader) -> tuple:
    return (list(reader), reader.fieldnames or [])

def _info_from_json(data: Any) -> tuple:
    sample = data[0] if isinstance(data, list) and data else data
    return (data, list(sample.keys()) if isinstance(sample, dict) else [])
