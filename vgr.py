#! /usr/bin/env python3

from typing import Any
import argparse
import os
import sys

from lark import Lark, exceptions

from app_exceptions import ExitingException, format_generic_exception, format_unexpected_input
from data_dict import DataDictionary
from dd_config import dd_init, dd_parse_user_args, dd_set_grammar
from functions import get_function_defs
from interactive import CmdLine
from output import expand_filename
from redir import print_debug, print_verbose, print_stderr
from src_mgr import SSM
from stmt_select import VALID_TARGETS
from stmt_exec import execute_statements

def print_app_exiting(dd: DataDictionary, e: ExitingException) -> None:
    print_debug(dd, SSM.source_for(e.statement))
    if e.message: print_stderr(e.message)
    print_verbose(dd, 'Exit Code =', e.exit_code)

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

    def execute_statements(self, text: str) -> None:
        try:
            execute_statements(self._parser, self._dd, text)
        except exceptions.UnexpectedInput as e:
            print(format_unexpected_input(e))
        except ExitingException as e:
            print_app_exiting(self._dd, e)
            # The only exit interactive mode "honors" is the actual exit request
            # With assertions, fatal errors, et al, we just continue
            if e.statement.data == 'exit':
                sys.exit(e.exit_code)
        except (ValueError, TypeError, OSError) as e:
            print(format_generic_exception(e))

    @property
    def debug(self) -> bool: return self._dd.is_debug()

    @property
    def verbose(self) -> bool: return self._dd.is_verbose()

    @verbose.setter
    def verbose(self, value: bool): self._dd.set_verbose(value)

    @property
    def prompt(self) -> str:
        return str(self._dd.get_var(None, *self._PROMPT_PATH) or self._DEFAULT_PROMPT)

    @prompt.setter
    def prompt(self, value: str):
        self._dd.set_var(None, value or self._DEFAULT_PROMPT, *self._PROMPT_PATH)

    @property
    def history_filename(self) -> str:
        return expand_filename(str(self._dd.get_var(None, *self._HISTORY_PATH) or self._DEFAULT_HISTORY))

    @history_filename.setter
    def history_filename(self, value: str) -> None:
        self._dd.set_var(None, expand_filename(value or self._DEFAULT_HISTORY), *self._HISTORY_PATH)

    @property
    def max_history_entries(self) -> int:
        try:
            return int(self._dd.get_var(None, *self._HISTORY_SIZE_PATH) or self._DEFAULT_HISTORY_SIZE)
        except ValueError:
            return self._DEFAULT_HISTORY_SIZE

    @max_history_entries.setter
    def max_history_entries(self, value: int) -> None:
        self._dd.set_var(None, value or self._DEFAULT_HISTORY_SIZE, *self._HISTORY_SIZE_PATH)

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
            'TARGET: ' + ' | '.join(tuple(f'"{t}"i' for t in VALID_TARGETS)),
        ))
        print_debug(dd, 'Generated grammar =', generated)
        grammar = grammar.format(GENERATED_CODE=generated)
        dd_set_grammar(dd, grammar)
        return Lark(grammar, start='statements', parser='lalr', debug=True, propagate_positions=True)

def main():
    cmd_line_parser = argparse.ArgumentParser(
        description="Generic Reporting for Hashicorp Vault - prototype"
    )
    cmd_line_parser.add_argument('-e', '--execute', action='append', metavar='STATEMENTS', default=[], help='Execute the given statements')
    cmd_line_parser.add_argument('-f', '--file', action='append', metavar='FILE', default=[], help='Execute statements stored in a file')
    cmd_line_parser.add_argument('--verbose', action='store_true', help="Enable verbose mode")
    cmd_line_parser.add_argument('--debug', action='store_true', help="Enable debug mode")
    cmd_line_parser.add_argument('--echo', action='store_true', help="Enable statement echo")
    cmd_line_parser.add_argument('--grammar',  metavar="FILE", type=str, help='Grammar definition')
    cmd_line_parser.add_argument('user_args', nargs='*', metavar='NAME=VALUE', help='Additional arguments')
    args = cmd_line_parser.parse_args()

    dd = dd_init()
    dd.set_debug(args.debug)
    dd.set_verbose(args.verbose)
    dd.set_echo(args.echo)
    dd_parse_user_args(dd, args.user_args)
    parser = create_parser(dd, args.grammar)

    # The user can execute statements through multiple methods,
    # including all at once. However, if they haven't, and there is
    # an interactive source for text, we drop into a tiny shell
    # that can be used for interactive testing.
    try:
        # For simple statements directly on the command line
        for statement in args.execute:
            execute_statements(parser, dd, statement, '<arg>')
        # NB: we don't "sandbox" these files like we do with others
        for filepath in args.file:
            # For statements stored in a file
            statement_text = None
            with open(filepath, 'r', encoding='utf-8') as f:
                statement_text = f.read()
            execute_statements(parser, dd, statement_text, filepath)
        if sys.stdin.isatty():
            if not args.execute and not args.file:
                print("Type 'exit' to exit")
                VGRCmdLine(parser, dd).run()
        else:
            # Read from stdin, most likely from a "here" document
            # but can be from a pipe or just a "<"
            execute_statements(parser, dd, sys.stdin.read(), '<stdin>')
        sys.exit(ExitingException.EXIT_SUCCESS)
    except ExitingException as e:
        print_app_exiting(dd, e)
        sys.exit(e.exit_code)
    except exceptions.UnexpectedInput as e:
        print_stderr(format_unexpected_input(e))
        print_debug(dd, e)
        sys.exit(ExitingException.EXIT_FAILED)
    except (ValueError, TypeError, OSError) as e:
        print_stderr(format_generic_exception(e))
        print_debug(dd, e)
        sys.exit(ExitingException.EXIT_FAILED)

if __name__ == '__main__':
    main()
