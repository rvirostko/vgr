"""
Other statements
"""

import time

from lark import Tree

from data_dict import DataDictionary
from evaluate import eval_to_number
from stmt_exec import bind_operations

def execute_sleep(dd: DataDictionary, statement: Tree) -> None:
    """Sleep for a given number of seconds

* Sleep [For] _expression_ [Seconds] [;]
"""
    n = eval_to_number(dd, bind_operations(statement.children[0]), 'Sleep time')
    n = min(max(n, 0), 3600)
    if n > 0:
        time.sleep(n)
