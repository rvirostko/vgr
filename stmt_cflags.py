
from lark import Tree

from data_dict import DataDictionary
from evaluate import eval_to_bool
from redir import print_verbose

def execute_echo(dd: DataDictionary, statement: Tree) -> None:
    """Turn echo mode on or off

* ECHO [;]
* ECHO _expression_ [;]

When on, statements are echoed before execution
"""
    dd.set_echo(_flag_value(dd, statement, 'Echo'))
    print_verbose(dd, 'Echo =', dd.is_echo())

def execute_debug(dd: DataDictionary, statement: Tree) -> None:
    """Turn debug mode on or off

* DEBUG [;]
* DEBUG _expression_ [;]

When on, additional technical output is generated.
"""
    dd.set_debug(_flag_value(dd, statement, 'Debug'))
    print_verbose(dd, 'Debug =', dd.is_debug())

def execute_verbose(dd: DataDictionary, statement: Tree) -> None:
    """Turn verbose mode on or off

* VERBOSE [;]
* VERBOSE _expression_ [;]

When on, additional operational output is generated.
"""
    dd.set_verbose(_flag_value(dd, statement, 'Verbose'))
    print_verbose(dd, 'Verbose =', dd.is_verbose()) # Yeah... can only print true

def _flag_value(dd: DataDictionary, statement: Tree, name: str) -> bool:
    # default for a flag is a request to turn on
    if not statement.children: return True
    return eval_to_bool(dd, statement.children[0], name)
