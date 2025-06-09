"""
Contains the implementation for the ECHO, DEBUG and VERBOSE statements
"""

from lark import Tree, Token

from data_dict import DataDictionary
from evaluate import eval_to_bool
from redir import print_stderr

def execute_echo(dd: DataDictionary, statement: Tree) -> None:
    """
**Turn echo mode on or off**

* Echo;
* Echo [On | Off] [;]
* Echo _expression_ [;]

Without arguments, echo is turned on.
When on, statements are echoed before execution
"""
    dd.echo = _flag_value(dd, statement, 'Echo')
    if dd.verbose: print_stderr('Echo =', dd.echo)

def execute_debug(dd: DataDictionary, statement: Tree) -> None:
    """
**Turn debug mode on or off**

* Debug;
* Debug [On | Off] [;]
* Debug _expression_ [;]

Without arguments, debug is turned on.
When on, additional technical output is generated.
"""
    dd.debug = _flag_value(dd, statement, 'Debug')
    if dd.verbose: print_stderr('Debug =', dd.debug)

def execute_verbose(dd: DataDictionary, statement: Tree) -> None:
    """
**Turn verbose mode on or off**

* Verbose;
* Verbose [On | Off] [;]
* Verbose _expression_ [;]

Without arguments, verbose is turned on.
When on, additional operational output is generated.
"""
    o_verbose = dd.verbose
    dd.verbose = _flag_value(dd, statement, 'Verbose')
    if dd.verbose or o_verbose: print_stderr('Verbose =', dd.verbose)

def _flag_value(dd: DataDictionary, statement: Tree, name: str) -> bool:
    # default behavior for a flag is a request to turn on
    if not statement.children: return True
    # This is a bit of a hack to allow "<flag> [on|off]"
    # without messing with the grammar -OR- the DD
    # The only thing that could be a problem would be a DD
    # value of "on" or "off" being set...
    if statement.children[0].data == 'var_ref' and len(statement.children[0].children) == 1:
        arg = statement.children[0].children[0]
        if isinstance(arg, Token) and arg.type == 'NAME':
            value = str(arg.value).casefold()
            if value == 'on': return True
            if value == 'off': return False
    rc = eval_to_bool(dd, statement.children[0], name, True)
    return False if rc is None else rc
