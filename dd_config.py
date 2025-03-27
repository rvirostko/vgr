
import os
import re

from data_dict import DataDictionary
from mathpak import coerce_value

_VGR_PREFIX = '_vgr'
_GRAMMAR_PATH = (_VGR_PREFIX, 'grammar')
_STATEMENT_PATH = (_VGR_PREFIX, 'statement')

_ARG_PREFIX = 'arg'
OFS_PATH = (_ARG_PREFIX, 'ofs')
ORS_PATH = (_ARG_PREFIX, 'ors')

_OS_PREFIX = 'os'
LINESEP_PATH = (_OS_PREFIX, 'linesep')

def dd_init() -> DataDictionary:
    dd = DataDictionary()
    dd.add_protected_prefix(_ARG_PREFIX)
    dd.add_immutable_prefix(_VGR_PREFIX)
    # Pick up the defaults AWK would use
    # Since we don't allow the env space to be changed,
    # we have to keep our own copies for the user to change with
    # either Set or with command line arguments
    dd.set_var(os.getenv('OFS', ' '), *OFS_PATH)
    dd.set_var(os.getenv('ORS', '\n'), *ORS_PATH)
    return dd

def dd_parse_user_args(dd: DataDictionary, user_args: list) -> None:
    # NB: User args can override debug/echo/verbose...
    for arg in user_args:
        if '=' in arg:
            name, value = re.split(r'\s*=', arg, 1)
            path = tuple(step for step in re.split(r'\s*[.]\s*', name.strip()))
            if path:
                # Strip off the quotes
                match = re.fullmatch(r'\s*"([^"]*)"\s*', value)
                path = (_ARG_PREFIX,) + path
                dd.set_var(match.group(1) if match else coerce_value(value), *path)

def dd_set_statement(dd: DataDictionary, statement_text: str) -> str:
    dd.set_var(statement_text, *_STATEMENT_PATH)

def dd_set_grammar(dd: DataDictionary, grammar: str) -> str:
    dd.set_var(grammar, *_GRAMMAR_PATH)
