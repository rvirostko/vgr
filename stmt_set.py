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
from evaluate import eval_expr, eval_filename_expr
from mathpak import poly_add, poly_sub, poly_number
from redir import print_verbose, shorten

def execute_set(dd: DataDictionary, statement: Tree) -> None:
    """Assign a value to a variable.

* SET _variable_ [= | := | TO) _expression_ [;]
"""
    path = tuple(name.value for name in statement.children[0].children)
    do_set(dd, eval_expr(dd, statement.children[1]), *path)

def execute_unset(dd: DataDictionary, statement: Tree) -> None:
    """Remove a variable.

* UNSET _variable_ [;]
"""
    path = tuple(name.value for name in statement.children[0].children)
    old_value = dd.unset_var_user(*path)
    if dd.is_verbose():
        print_verbose(dd, "Removed", shorten(repr(old_value)), 'From', '.'.join(path))

def execute_inc(dd: DataDictionary, statement: Tree) -> None:
    """Increment a counter by an amount

* Set _variable_ Up By _expression_ [;]

If the variable does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar opertion.
"""
    path = tuple(name.value for name in statement.children[0].children)
    x = poly_number(dd.get_var_user(*path)) or 0
    y = poly_number(eval_expr(dd, statement.children[1])) or 0
    do_set(dd, poly_add(x, y), *path)

def execute_dec(dd: DataDictionary, statement: Tree) -> None:
    """Deccrement a counter by an amount

* Set _variable_ Down By _expression_ [;]

If the variable does not exist, it is created and initialized to zero.
This is fundamentally an arithmetic, scalar opertion.
"""
    path = tuple(name.value for name in statement.children[0].children)
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
    if isinstance(fc, Token):
        # NB: the only thing defined in the grammar is the
        # corresponding token, but just in case...
        corresponding = fc.value == 'corr'
        start = 1
    src = eval_expr(dd, statement.children[start])
    path = tuple(name.value for name in statement.children[start + 1].children)
    dest = dd.get_var_user(*path) if corresponding else None
    if isinstance(src, dict) and isinstance(dest, dict):
        # should end up here if corresponding was specified,
        # what we are moving is a dictionary, and the
        # destination existed and is also a dictionary
        dest = deepcopy(dest)
        dest.update({k: src[k] for k in src if k in dest})
        do_set(dd, dest, *path)
    else:
        do_set(dd, src, *path)

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
    path = tuple(name.value for name in statement.children[0].children)
    filename = eval_filename_expr(dd, statement.children[1])
    mode = None
    if len(statement.children) > 2:
        mode = statement.children[2].data
    else:
        ext = os.path.splitext(filename)[1].lower()
        mode = 'csv_file' if ext == '.csv' else 'json_object' if ext == '.json' else 'text_file'
    with open(filename, 'r', encoding='utf-8') as f:
        data: Any = None
        if mode == 'text_file': data = f.read()
        elif mode == 'json_object': data = json.load(f)
        elif mode == 'json_objects': data = [json.loads(line) for line in f if line.strip()]
        elif mode == 'csv_file': data = list(csv.DictReader(f))
        else: raise ValueError(f'Unknown mode {mode}') # SNO
        new_value = dd.set_var_user(data, *path)
        if dd.is_verbose():
            if isinstance(new_value, list):
                length = len(new_value)
                print_verbose(dd, "Loaded", '.'.join(path), 'With', length, 'Records' if length != 1 else 'Record')
            else:
                print_verbose(dd, "Loaded", '.'.join(path), 'With', shorten(repr(new_value)))

def do_set(dd: DataDictionary, value: Any, *path) -> None:
    """
    After calculations are done, use this to set a value.
    Generates verbose output.
    """
    new_value = dd.set_var_user(value, *path)
    if dd.is_verbose():
        print_verbose(dd, "Set", '.'.join(path), 'To', shorten(repr(new_value)))
