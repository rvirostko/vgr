"""
Contains the implementation for the ECHO, DEBUG and VERBOSE statements
"""

from lark import Tree

from data_dict import DataDictionary
from evaluate import eval_to_bool
from redir import print_stderr

def execute_echo(dd: DataDictionary, statement: Tree) -> None:
    """Turn echo mode on or off

* Echo;
* Echo _expression_ [;]

Without arguments, echo is turned on.
When on, statements are echoed before execution
"""
    dd.echo = _flag_value(dd, statement, 'Echo')
    if dd.verbose: print_stderr('Echo =', dd.echo)

def execute_debug(dd: DataDictionary, statement: Tree) -> None:
    """Turn debug mode on or off

* Debug;
* Debug _expression_ [;]

Without arguments, debug is turned on.
When on, additional technical output is generated.
"""
    dd.debug = _flag_value(dd, statement, 'Debug')
    if dd.verbose: print_stderr('Debug =', dd.debug)

def execute_verbose(dd: DataDictionary, statement: Tree) -> None:
    """Turn verbose mode on or off

* Verbose;
* Verbose _expression_ [;]

Without arguments, verbose is turned on.
When on, additional operational output is generated.
"""
    dd.verbose = _flag_value(dd, statement, 'Verbose')
    if dd.verbose: print_stderr('Verbose =', dd.verbose) # Yeah... can only print true

def _flag_value(dd: DataDictionary, statement: Tree, name: str) -> bool:
    # default behavior for a flag is a request to turn on
    if not statement.children: return True
    rc = eval_to_bool(dd, statement.children[0], name, True)
    return False if rc is None else rc
