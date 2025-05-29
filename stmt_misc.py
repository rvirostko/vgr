"""
Other statements: SLEEP
"""

import time

from lark import Tree

from data_dict import DataDictionary
from evaluate import eval_to_number
from redir import print_stderr

def execute_sleep(dd: DataDictionary, statement: Tree) -> None:
    """
**Sleep for a given number of seconds**

* Sleep [For] _expression_ [Second | Seconds] [;]

Values may be floating point, e.g. .01 to delay for ten milliseconds.
Negative and zero values are ignored. Maximum sleep time is five minutes.
"""
    n = eval_to_number(dd, statement.children[0], 'Sleep time')
    n = min(max(n, 0), 300)
    if n > 0:
        if dd.verbose: print_stderr('Sleeping for', n, "seconds")
        time.sleep(n)
    else:
        if dd.verbose: print_stderr('Sleep skipped')
