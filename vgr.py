#! /usr/bin/env python3

from typing import Any
import argparse
import os
import sys
import traceback

from lark import Lark, exceptions

from app_exceptions import ExitingException, format_generic_exception, format_unexpected_input
from data_dict import DataDictionary
from dd_config import dd_init, dd_parse_user_args, dd_set_grammar, DEFAULT_FROM_TYPE_PATH
from functions import get_function_defs
from interactive import CmdLine
from mathpak import poly_bool
from output import expand_filename
from redir import print_debug, print_verbose, print_stderr
from src_mgr import SSM
from stmt_exec import execute_statements
from xtract_vault import VAULT_TARGETS

def print_app_exiting(dd: DataDictionary, e: ExitingException) -> None:
    print_debug(dd, SSM.source_for(e.statement))
    if e.message: print_stderr(e.message)

class VGRCmdLine(CmdLine):
    _VGR_ENV_PREFIX = 'VGR_'
    _VGR_PREFIX = '_vgr' # TODO DUP
    _PROMPT_PATH = (_VGR_PREFIX, 'prompt')
    _HISTORY_PATH = (_VGR_PREFIX, 'history')
    _HISTORY_SIZE_PATH = (_VGR_PREFIX, 'history_size')
    _DEFAULT_HISTORY_SIZE = 100
    _DEFAULT_HISTORY = '~/.vgr_history'
    _DEFAULT_PROMPT = 'vgr> '

    def __init__(self, parser: Lark, dd: DataDictionary):
        self._parser = parser
        self._dd = dd
        self.prompt = self._get_vgr_default(self._PROMPT_PATH[1], self._DEFAULT_PROMPT)
        self.history_filename = self._get_vgr_default(self._HISTORY_PATH[1], self._DEFAULT_HISTORY)
        self.max_history_entries = self._get_vgr_default_int(self._HISTORY_SIZE_PATH[1], self._DEFAULT_HISTORY_SIZE)
        super().__init__()

    def run(self):
        # If this has not been set (command line?) we use our interactive default
        self._dd.set_var_user((self._dd.get_var_user(*DEFAULT_FROM_TYPE_PATH) or 'template-batch').lower(), *DEFAULT_FROM_TYPE_PATH)
        print("Type 'exit' to exit")
        return super().run()

    def execute_statements(self, text: str) -> None:
        try:
            execute_statements(self._parser, self._dd, text)
        except exceptions.UnexpectedInput as e:
            if self.debug:
                traceback.print_exc(file=sys.stderr)
            else:
                print(format_unexpected_input(e))
        except ExitingException as e:
            # The only exit interactive mode "honors" is the actual exit request
            # With assertions, fatal errors, et al, we just continue
            if e.statement.data == 'exit':
                raise e
            print_app_exiting(self._dd, e)
            if self.debug:
                traceback.print_exc(file=sys.stderr)
        except (ValueError, TypeError, OSError) as e:
            if self.debug:
                traceback.print_exc(file=sys.stderr)
            else:
                print(format_generic_exception(e))

    @property
    def debug(self) -> bool: return self._dd.is_debug()

    @property
    def verbose(self) -> bool: return self._dd.is_verbose()

    @verbose.setter
    def verbose(self, value: bool): self._dd.set_verbose(value)

    @property
    def prompt(self) -> str:
        return str(self._dd.get_var(*self._PROMPT_PATH) or self._DEFAULT_PROMPT)

    @prompt.setter
    def prompt(self, value: str):
        self._dd.set_var(value or self._DEFAULT_PROMPT, *self._PROMPT_PATH)

    @property
    def history_filename(self) -> str:
        return expand_filename(str(self._dd.get_var(*self._HISTORY_PATH) or self._DEFAULT_HISTORY))

    @history_filename.setter
    def history_filename(self, value: str) -> None:
        self._dd.set_var(expand_filename(value or self._DEFAULT_HISTORY), *self._HISTORY_PATH)

    @property
    def max_history_entries(self) -> int:
        try:
            return int(self._dd.get_var(*self._HISTORY_SIZE_PATH) or self._DEFAULT_HISTORY_SIZE)
        except ValueError:
            return self._DEFAULT_HISTORY_SIZE

    @max_history_entries.setter
    def max_history_entries(self, value: int) -> None:
        self._dd.set_var(value or self._DEFAULT_HISTORY_SIZE, *self._HISTORY_SIZE_PATH)

    def _get_vgr_default(self, env_var: str, default: Any) -> str:
        """Look for a matching environment variable (uppercase) and return it or the default value"""
        return os.getenv(self._VGR_ENV_PREFIX + env_var.upper(), default)

    def _get_vgr_default_int(self, env_var: str, default: Any) -> str:
        """Look for a matching environment variable (uppercase) and try to convert to an int"""
        try:
            return int(self._get_vgr_default(env_var, default))
        except ValueError:
            return default

def create_parser(dd: DataDictionary, grammar_file: str) -> Lark:
    if not grammar_file:
        grammar_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vgr.ebnf')
    print_debug(dd, 'Grammar file is', grammar_file)
    with open(grammar_file, "r", encoding="utf-8") as file:
        grammar = file.read()
        generated = '\n\n'.join((
            get_function_defs(),
            'VAULT_TARGET: ' + ' | '.join(tuple(f'"{t}"i' for t in VAULT_TARGETS)),
        ))
        print_debug(dd, 'Generated grammar =', generated)
        grammar = grammar.format(GENERATED_CODE=generated)
        dd_set_grammar(dd, grammar)
        return Lark(grammar, start='statements', parser='lalr', debug=True, propagate_positions=True)

class SaveOrderedSources(argparse.Action):
    def __call__(self, *args, **_):
        # unpack here rather than in signature to appease pylint
        _, namespace, values, option = args
        if not hasattr(namespace, "ordered"):
            namespace.ordered = []
        namespace.ordered.append((option.lstrip('-')[0].lower(), values))

def main():
    clp = argparse.ArgumentParser(
        description='Generic Reporting for Hashicorp Vault - WIP',
        epilog="""Statements added with --execute and statements loaded by --file
are executed in the order they are given. Following that, statements are read from
stdin if they are available. If no --execute and --file arguments are given, and
stdin is interactive, the shell is started.

Environment variables:
  - OFS/ORS - output field and record separators as defined by AWK
  - VGR_PROMPT - shell prompt; limited Bash-like escapes supported
  - VGR_HISTORY - path to shell's history file
  - VGR_HISTORY_SIZE - max number of lines stored in history
"""
    )
    clp.add_argument('-e', '--execute', nargs='*', metavar='STATEMENTS', action=SaveOrderedSources,
                    help='Execute the given statements')
    clp.add_argument('-f', '--file', nargs='*', metavar='FILE', action=SaveOrderedSources,
                     help="Execute statements stored in a file")
    clp.add_argument('--verbose', nargs='?', const=True, metavar='BOOL', type=poly_bool,
                    help='Enable/disable verbose mode')
    clp.add_argument('--debug', nargs='?', const=True, metavar='BOOL', type=poly_bool,
                    help='Enable/disable debug mode')
    clp.add_argument('--echo', nargs='?', const=True, metavar='BOOL', type=poly_bool,
                    help='Enable/disable statement echo')
    clp.add_argument('--shell', nargs='?', const=True, metavar='BOOL', type=poly_bool,
                    help='Request/prohibit the shell. Shell starts if --execute/--file are not used')
    clp.add_argument('--grammar',  metavar="FILE", type=str,
                    default=None, help='Grammar definition: developement option only')
    clp.add_argument('user_args', nargs='*', metavar='NAME=VALUE',
                    default=[], help='Additional arguments. Values maybe booleans, numbers, or strings')
    args = clp.parse_args()

    # Since it's startup, and everything else relies on the DD...
    if args.verbose: print('Creating data dictionary...', file=sys.stderr)
    dd = dd_init()
    dd.set_debug(args.debug)
    dd.set_verbose(args.verbose)
    dd.set_echo(args.echo)
    print_verbose(dd, 'Creating parser...')
    parser = create_parser(dd, args.grammar)
    if args.user_args:
        print_verbose(dd, 'Parsing user args...')
        dd_parse_user_args(dd, args.user_args)

    # NB: args.execute and args.file will always be None
    #     as there values have been accumulated in
    #     args.ordered so they can be handled in the order
    #     received. Additionally, each option can be
    #     an ordered list.
    exit_code: int = None
    try:
        ordered_args = args.ordered if hasattr(args, "ordered") else []
        # Accumulated -e/-f options, stored in the order given
        for opt in ordered_args:
            stype, svalue = opt
            if stype == 'e':
                # Simple statements directly on the command line
                for statements in svalue:
                    print_verbose(dd, 'Executing statements from command line...')
                    execute_statements(parser, dd, statements, '<cmd-line>')
                continue
            if stype == 'f':
                # Statements stored in a file
                for filename in svalue:
                    # NB: we don't "sandbox" these files like we do with others
                    filepath = expand_filename(filename)
                    print_verbose(dd, f'Executing statements from {repr(filepath)}...')
                    statements = None
                    with open(filepath, 'r', encoding='utf-8') as f:
                        statements = f.read()
                    execute_statements(parser, dd, statements, filename)
                continue
            raise NotImplementedError(f'Statement source {repr(stype)} not implemented') # SNO
        if sys.stdin.isatty():
            # "--shell" forces opening a shell
            # "--shell false" prevents opening it
            # when not given, we look to having previously executed -e/f commands
            if args.shell is True or (args.shell is None and not ordered_args):
                print_verbose(dd, 'Starting the shell...')
                VGRCmdLine(parser, dd).run()
                print_verbose(dd, 'Shell exited')
        else:
            # Read from stdin, most likely from a "here" document
            # but can be from a pipe or just a "<"
            print_verbose(dd, 'Executing statements from stdin...')
            execute_statements(parser, dd, sys.stdin.read(), '<stdin>')
        sys.exit(ExitingException.EXIT_SUCCESS)
    except ExitingException as e:
        print_app_exiting(dd, e)
        exit_code = e.exit_code
    except exceptions.UnexpectedInput as e:
        if dd.is_debug():
            traceback.print_exc(file=sys.stderr)
        print_stderr(format_unexpected_input(e))
        print_debug(dd, e)
        exit_code = ExitingException.EXIT_FAILED
    except (ValueError, TypeError, OSError) as e:
        if dd.is_debug():
            traceback.print_exc(file=sys.stderr)
        print_stderr(format_generic_exception(e)) # TODO statment mgr
        print_debug(dd, e)
        exit_code = ExitingException.EXIT_FAILED
    print_verbose(dd, f'Exit code is {exit_code}')
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
