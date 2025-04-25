"""
Includes the implemenation for SET/UNSET, MOVE, and LOAD FROM.
"""

from typing import Any
import csv
import json
import os

from lark import Tree, Token

from data_dict import DataDictionary
from dd_config import dd_path, do_assignment, do_unset
from evaluate import eval_expr, eval_filename_expr
from redir import print_stderr, shorten

def execute_set(dd: DataDictionary, statement: Tree) -> None:
    """Assign a value to a variable.

* Set _variable_ [= | := | TO) _expression_ [;]
"""
    path = dd_path(statement.children[0])
    expr = statement.children[1]
    do_assignment(dd, expr, eval_expr(dd, expr), path)

def execute_unset(dd: DataDictionary, statement: Tree) -> None:
    """Remove a variable.

* Unset _variable_ [, _variable_]... [;]
"""
    for item in statement.children:
        path = dd_path(item)
        do_unset(dd, *path)

def execute_load_from(dd: DataDictionary, statement: Tree) -> None:
    """Assign a value to a variable from a file.

* Load _variable_ From [File] _expression_ [;]
* Load _variable_ From [File] _expression_ JSON [Object] [;]
* Load _variable_ From [File] _expression_ JSON [Object] Per Line [;]
* Load _variable_ From [File] _expression_ CSV [;]
* Load _variable_ From [File] _expression_ Text [;]

The _expression_ is resolved to string as file to be loaded

If no type is included, the type is inferred from the extension of the file
name with Text as the default.
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
