#! /usr/bin/env python3

from typing import Any
import argparse
import os
import sys
import traceback

from lark import Lark, exceptions

from app_exceptions import VgrExitingException, format_generic_exception, format_unexpected_input, VgrException
from data_dict import DataDictionary
from dd_config import dd_init, dd_parse_user_args
from dd_config import DEFAULT_FOR_TYPE_PATH, SHELL_HISTORY_PATH, SHELL_HISTORY_SIZE_PATH, SHELL_PROMPT_PATH
from doc_help import print_md, search_functions, is_probably, print_doc
from extn import VgrExtensionRegistry, VER
from functions import get_function_defs, add_builtin_functions, add_function
from interactive import CmdLine, ArgumentParser, ParserBuilder
from log_config import init_logging, set_logging_level
from mathpak import poly_bool
from output import expand_filename
from redir import print_stderr
from stmt_exec import STATEMENT_HANDLERS, execute_statements

class VGRCmdLine(CmdLine):
    _DEFAULT_HISTORY_SIZE = 100
    _DEFAULT_HISTORY = '~/.vgr_history'
    _DEFAULT_PROMPT = 'vgr> '

    _SOURCE_PARSER: ArgumentParser = (ParserBuilder()
                    .argument('file', type=str)
                    .parser())

    def __init__(self, parser: Lark, dd: DataDictionary):
        self._parser = parser
        self._dd = dd
        self.prompt = self._get_vgr_default(SHELL_PROMPT_PATH[1], self._DEFAULT_PROMPT)
        self.history_filename = self._get_vgr_default(SHELL_HISTORY_PATH[1], self._DEFAULT_HISTORY)
        self.max_history_entries = self._get_vgr_default_int(SHELL_HISTORY_SIZE_PATH[1], self._DEFAULT_HISTORY_SIZE)
        super().__init__()

    def run(self):
        # If this has not been set (command line?) we use our interactive default
        self._dd.set_var_user((self._dd.get_var_user(*DEFAULT_FOR_TYPE_PATH) or 'template-batch').lower(),
                              *DEFAULT_FOR_TYPE_PATH)
        print_md('_Type `exit` to exit_')
        return super().run()

    def execute_statements(self, text: str) -> bool:
        try:
            execute_statements(self._parser, self._dd, text, '<shell>')
        except exceptions.UnexpectedInput as e:
            if self.debug:
                traceback.print_exc(file=sys.stderr)
            else:
                print(format_unexpected_input(e))
        except VgrException as e:
            # The only exit interactive mode "honors" is the actual exit request
            # With assertions, fatal errors, et al, we just continue
            if isinstance(e, VgrExitingException):
                t: VgrExitingException = e
                if t.statement.data == 'exit':
                    return False
            if self.debug:
                traceback.print_exc(file=sys.stderr)
            else:
                print(str(e))
        except Exception as e:
            if self.debug:
                traceback.print_exc(file=sys.stderr)
            else:
                print(format_generic_exception(e))
        return True

    @property
    def debug(self) -> bool:
        return self._dd.debug

    @property
    def verbose(self) -> bool:
        return self._dd.verbose

    @verbose.setter
    def verbose(self, value: bool):
        self._dd.verbose = value

    @property
    def prompt(self) -> str:
        return str(self._dd.get_var(*SHELL_PROMPT_PATH) or self._DEFAULT_PROMPT)

    @prompt.setter
    def prompt(self, value: str):
        self._dd.set_var(value or self._DEFAULT_PROMPT, *SHELL_PROMPT_PATH)

    @property
    def history_filename(self) -> str:
        return expand_filename(str(self._dd.get_var(*SHELL_HISTORY_PATH) or self._DEFAULT_HISTORY))

    @history_filename.setter
    def history_filename(self, value: str) -> None:
        self._dd.set_var(expand_filename(value or self._DEFAULT_HISTORY), *SHELL_HISTORY_PATH)

    @property
    def max_history_entries(self) -> int:
        try:
            return int(self._dd.get_var(*SHELL_HISTORY_SIZE_PATH) or self._DEFAULT_HISTORY_SIZE)
        except ValueError:
            return self._DEFAULT_HISTORY_SIZE

    @max_history_entries.setter
    def max_history_entries(self, value: int) -> None:
        self._dd.set_var(value or self._DEFAULT_HISTORY_SIZE, *SHELL_HISTORY_SIZE_PATH)

    def _get_vgr_default(self, env_var: str, default: Any) -> str:
        """Look for a matching environment variable (uppercase) and return it or the default value"""
        return os.getenv('VGR_' + env_var.upper(), default)

    def _get_vgr_default_int(self, env_var: str, default: Any) -> str:
        """Look for a matching environment variable (uppercase) and try to convert to an int"""
        try:
            return int(self._get_vgr_default(env_var, default))
        except ValueError:
            return default

    def _exec_help(self, *args) -> None:
        """
**Help Topics**

* `cd` : Change the current working directory
* `function` : Help for functions
* `history` : Display or control command line history
* `multiline` : Turn on multiline editing mode
* `operator` : Help for operators
* `prompt` : Define the input input prompt
* `pwd` : Print the current working directory
* `statement` : Help for statements

Run any of these with _help_ for more information
"""
        if len(args) < 1:
            print_doc(self._exec_help)
        else:
            topic = args[0]
            targs = args[1:]
            if is_probably("cd", topic): print_doc(self._exec_cd)
            elif is_probably("pwd", topic): print_doc(self._exec_pwd)
            elif is_probably("history", topic): print_doc(self._exec_history)
            elif is_probably("multiline", topic): print_doc(self._exec_multiline)
            elif is_probably("prompt", topic): print_doc(self._exec_prompt)
            elif is_probably("function", topic): self._function_help(*targs)
            elif is_probably("operator", topic): self._operator_help(*targs)
            elif is_probably("statement", topic): self._statement_help(*targs)
            else: print_doc(self._exec_help)

    def _function_help(self, *args) -> None:
        q = args[0] if args else ''
        functions = search_functions(q)
        if len(functions) == 0:
            # We could not find anything
            print()
            print_md(f'_No function like {args[0]}_')
            print()
        elif len(functions) == 1:
            # We got an exact match
            # Show the function specific help
            print_doc(functions[0][1])
        else:
            # Multiple results
            # Show as a list with a summary
            lines = []
            lines.append(f'**{"Search Results" if q else "Functions"}-**')
            for name, func in functions:
                doc = (func.__doc__ or "").strip()
                if doc:
                    # Display first non-blank line, stripped of bolding (the convention) and no sentence
                    lines.append(f'* `{name}()` - {doc.splitlines()[0].strip().strip("*").rstrip(".")}')
                else:
                    lines.append(f'* `{name}()`')
            print()
            print_md('\n'.join(lines))
            print()

    def _operator_help(self, *args) -> None:
        # TODO
        print(args)

    def _statement_help(self, *args) -> None:
        # TODO
        print(args)

def create_dd(args) -> DataDictionary:
    # Since it's startup, and everything else relies on the DD...
    if args.verbose: print('Creating data dictionary...', file=sys.stderr)
    dd = dd_init()
    dd.debug = args.debug
    dd.verbose = args.verbose
    dd.echo = args.echo
    return dd

def load_extensions(dd: DataDictionary, extn_file: str) -> VgrExtensionRegistry:
    print_verbose(dd, 'Loading extensions...')
    if not extn_file:
        extn_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extensions.ini')
    print_debug(dd, 'Extension file is', extn_file)
    VER.load(dd, extn_file)
    extns=[]
    for extn_name, extn in VER:
        extns.append((extn_name, f'{extn.__class__.__module__}.{extn.__class__.__qualname__}',extn.adds_statements(), extn.extends_select(), ))
        if extn.adds_statements():
            for name, handler in extn.statement_handlers().items():
                if name in STATEMENT_HANDLERS:
                    raise ValueError(f'Extension {repr(extn_name)} tried to redefine {repr(name)}')
                STATEMENT_HANDLERS[name] = handler
        for func_name, func in extn.functions().items():
            add_function(extn_name, func_name, func)
    dd.set_var(extns, *('vgr', 'extensions'))
    return VER

def create_parser(dd: DataDictionary, grammar_file: str, extn_registry: VgrExtensionRegistry) -> Lark:
    print_verbose(dd, 'Creating parser...')
    if not grammar_file:
        grammar_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vgr.ebnf')
    extn_from = ''
    extn_statements = ''
    extn_grammar = ''
    for name, instance in extn_registry:
        # By convention, if an extension says it has statements or extends the From clause
        # it should have a like named rule in its grammar
        if instance.extends_select(): extn_from += f' | {name}_from'
        if instance.adds_statements(): extn_statements += f'| {name}_statements'
        extn_grammar += instance.grammar()
        if not extn_grammar.endswith('/n'): extn_grammar += '\n'
    if dd.debug:
        print_debug(dd, f'EXTN_STATMENTS={extn_statements}')
        print_debug(dd, f'EXTN_FROM={extn_from}')
        print_debug(dd, f'EXTN_GRAMMAR={extn_grammar}')
    print_debug(dd, 'Grammar file is', grammar_file)
    with open(grammar_file, 'r', encoding='utf-8-sig') as file:
        grammar = file.read()
    # NB: we can't just use str.format() because the grammar
    #     contains "{" and "}"
    for tag, value in (('{EXTN_STATEMENTS}', extn_statements),
                       ('{EXTN_FROM}', extn_from),
                       ('{EXTN_GRAMMAR}', extn_grammar),
                       ('{FUNCTIONS}', get_function_defs())):
        grammar = grammar.replace(tag, value)
    return Lark(grammar,
                start='statements',
                lexer='contextual',
                parser='lalr',
                debug=True,
                propagate_positions=True)

class SaveOrderedSources(argparse.Action):
    def __call__(self, *args, **_):
        # unpack here rather than in signature to appease pylint
        _, namespace, values, option = args
        if not hasattr(namespace, "ordered"):
            namespace.ordered = []
        namespace.ordered.append((option.lstrip('-')[0].lower(), values))

def print_debug(dd: DataDictionary, /, *args, **kwargs) -> None:
    """If debug is on print to stderr"""
    if dd.debug: print_stderr(*args, **kwargs)

def print_verbose(dd: DataDictionary, /, *args, **kwargs) -> None:
    """If verbose is on print to stderr"""
    if dd.verbose: print_stderr(*args, **kwargs)

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
    clp.add_argument('--logfile', type=str, default=None,
                    help='Path to the log file')
    clp.add_argument('--loglevel', type=str, default='info',
                    help='Logging level (debug, info, warning, error, critical)')
    clp.add_argument('--logoverwrite', action='store_true',
                    help='Overwrite log file instead of appending')
    clp.add_argument('--grammar',  metavar="FILE", type=str,
                    default=None, help='Grammar definition: developement option only')
    clp.add_argument('--extensions',  metavar="FILE", type=str,
                    default=None, help='Extensions file')
    clp.add_argument('user_args', nargs='*', metavar='NAME=VALUE',
                    default=[], help='Additional arguments. Values maybe booleans, numbers, or strings')
    args = clp.parse_args()

    init_logging(args.logfile, args.logoverwrite)
    set_logging_level(args.loglevel)

    dd = create_dd(args)
    add_builtin_functions()
    extensions = load_extensions(dd, args.extensions)
    parser = create_parser(dd, args.grammar, extensions)
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
                    print_verbose(dd, 'Executing statements from ', repr(filepath), '...')
                    statements = None
                    with open(filepath, 'r', encoding='utf-8-sig') as f:
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
        exit_code = VgrExitingException.EXIT_SUCCESS
    except VgrExitingException as e:
        print(str(e))
        exit_code = e.exit_code
    except VgrException as e:
        # TODO log it
        if dd.debug:
            traceback.print_exc(file=sys.stderr)
        print_stderr(str(e))
        print_debug(dd, e)
        exit_code = VgrExitingException.EXIT_FAILED
    except exceptions.UnexpectedInput as e:
        # TODO log it
        if dd.debug:
            traceback.print_exc(file=sys.stderr)
        print_stderr(format_unexpected_input(e))
        print_debug(dd, e)
        exit_code = VgrExitingException.EXIT_FAILED
    except Exception as e:
        # TODO log it
        if dd.debug:
            traceback.print_exc(file=sys.stderr)
        print_stderr(format_generic_exception(e))
        print_debug(dd, e)
        exit_code = VgrExitingException.EXIT_FAILED
    print_verbose(dd, f'Exit code is {exit_code}')
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
