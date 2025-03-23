
from typing import Any
import csv
import json
import os

from lark import Tree

from data_dict import DataDictionary
from evaluate import eval_expr, eval_filename_expr

def execute_set(dd: DataDictionary, statement: Tree) -> None:
    """Assign a value to a variable.

* SET _variable_ [= | := | TO) _expression_ [;]
* LET _variable_ [= | :=] _expression_ [;]
"""
    var_name, expr = statement.children
    dd.set_var_user(eval_expr(dd, expr), *(name.value for name in var_name.children))

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
    var_name = statement.children[0]
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
        dd.set_var_user(data, *(name.value for name in var_name.children))
