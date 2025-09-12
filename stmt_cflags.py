"""
Contains the implementation for the ECHO, DEBUG and VERBOSE statements
"""

from lark import Tree, Token

from data_dict import DataDictionary
from evaluate import eval_to_bool, bind_operations
from exec_context import ExecContext
from mathpak import bound_ops
from redir import print_stderr
from tags import control_statement

@control_statement
@bound_ops("Echo")
def execute_echo(ctx: ExecContext, statement: Tree) -> None:
    """
**Turn echo mode on or off**

* Echo;
* Echo [On | Off] [;]
* Echo _expression_ [;]

Without arguments, statement echoing is turned on.
When on, statements are echoed before execution
Note that this command itself never echoes itself.
"""
    ctx.dd.echo = _flag_value(ctx.dd, bind_operations(statement), 'Echo')
    ctx.print_verbose('Echo =', ctx.dd.echo)

@bound_ops("Debug")
def execute_debug(ctx: ExecContext, statement: Tree) -> None:
    """
**Turn debug mode on or off**

* Debug;
* Debug [On | Off] [;]
* Debug _expression_ [;]

Without arguments, debug is turned on.
When on, additional technical output is generated.
"""
    ctx.dd.debug = _flag_value(ctx.dd, statement, 'Debug')
    ctx.print_verbose('Debug =', ctx.dd.debug)

@bound_ops("Verbose")
def execute_verbose(ctx: ExecContext, statement: Tree) -> None:
    """
**Turn verbose mode on or off**

* Verbose;
* Verbose [On | Off] [;]
* Verbose _expression_ [;]

Without arguments, verbose is turned on.
When on, additional operational output is generated.
"""
    o_verbose = ctx.dd.verbose
    ctx.dd.verbose = _flag_value(ctx.dd, statement, 'Verbose')
    if ctx.dd.verbose or o_verbose: print_stderr('Verbose =', ctx.dd.verbose)

def _flag_value(dd: DataDictionary, statement: Tree, name: str) -> bool:
    # default behavior for a flag is a request to turn on
    if not statement.children: return True
    # This is a bit of a hack to allow "<flag> [on|off]"
    # without messing with the grammar -OR- the DD
    # The only thing that could be a problem would be a DD
    # value of "on" or "off" being set...
    first_child = statement.children[0]
    if isinstance(first_child, Tree) and first_child.data == 'var_ref' and len(first_child.children) == 1:
        arg = first_child.children[0]
        if isinstance(arg, Token) and arg.type == 'NAME':
            value = str(arg.value).casefold()
            if value == 'on': return True
            if value == 'off': return False
    rc = eval_to_bool(dd, first_child, name, True)
    return False if rc is None else rc
