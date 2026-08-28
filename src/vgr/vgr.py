"""Main for VGR command line"""

import argparse
import logging
import os
import sys
import traceback

from lark import Lark

from .app_exceptions import (
    VgrException,
    VgrExitingException,
    VgrStatementAbort,
    VgrStatementAssert,
)
from .builtins import (
    poly_repr,
    poly_type,
)
from .data_dict import DataDictionary
from .dd_config import (
    dd_init,
    EXEC_NAME_PATH,
    EXEC_VER_PATH,
    VER_DATE_PATH,
    VER_PATH,
)
from .user_args import set_user_args
from .extn import VgrExtension, VgrExtensionRegistry, VER
from .functions import (
    add_builtin_functions,
    add_functions,
    function_names_pattern,
    get_function_defs,
)
from .interactive import CmdLine
from .log_config import init_logging
from .redir import print_stderr
from .exec_context import ExecContext
from .stmt_exec import (
    create_exec_context,
    STATEMENT_HANDLERS,
)
from .stmt_include import (
    do_include,
    do_source,
    find_vgr_source,
)
from .stmt_log import (
    init_app_log
)
from .var_name import VAR_NAME
from .vscode_extn import create_vscode_extension
from .repl_help import repl_help
from .md_print import (
    md_println,
    md_create_lexer,
)

from . import __version__, __version_date__, __description__

_CMD_LINE_ASSIGN = 'cmd_line_assign'

_LOG = logging.getLogger()

class VGRCmdLine(CmdLine):
    _DEFAULT_HISTORY = '~/.vgr_history'
    _DEFAULT_PROMPT = 'vgr> '

    def __init__(self, ctx: ExecContext):
        assert ctx
        self._ctx = ctx
        self._history_filename = os.getenv("VGR_HISTORY", self._DEFAULT_HISTORY)
        self._max_history_entries = os.getenv("VGR_HISTORY_SIZE", CmdLine._DEFAULT_HISTORY_SIZE)
        super().__init__()

    def run(self) -> int:
        self._ctx.print_verbose("CWD =", os.getcwd())
        md_println("\n", f"`VGR {__version__} ({__version_date__})`", "_Type **help** for more information_")
        self._ctx.set_var(True, 'vgr', 'repl')
        return super().run()

    def execute_statements(self, text: str) -> tuple:
        try:
            self._ctx.execute_statements(text.rstrip(), '<repl>')
        except VgrException as e:
            # An "Exit" terminates the REPL
            # An "Abort" or "Assert" does not
            if isinstance(e, VgrExitingException) and not isinstance(e, (VgrStatementAbort, VgrStatementAssert)):
                return (False, e.exit_code)
            if self._ctx.debug:
                traceback.print_exc(file=sys.stderr)
            else:
                print(str(e))
        except Exception as e: # pylint: disable=broad-exception-caught
            if self._ctx.debug:
                traceback.print_exc(file=sys.stderr)
            else:
                print(str(VgrException(None, e, None, None)))
        return (True, None)

    def print_verbose(self, *args, **kwargs) -> None:
        self._ctx.print_verbose(*args, **kwargs)

    def print_exception(self, e: Exception) -> None:
        if self._ctx.verbose:
            print(e, file=sys.stderr)
        else:
            print(e.args[0] if e.args else f'{poly_type(e)!r}', file=sys.stderr)

    def get_prompt(self) -> str:
        prompt = self._ctx.get_var("env", "VGR_PROMPT")
        return self._DEFAULT_PROMPT if prompt is None else prompt

    def _exec_help(self, *args) -> None:
        repl_help(*args)

def load_extensions(dd: DataDictionary, verbose: bool) -> VgrExtensionRegistry:
    if verbose: print_stderr('Loading extensions...')
    VER.load(dd, __package__, 'extensions.ini')
    extns = []
    for extn_name, extn in VER:
        extns.append((extn_name, f'{extn.__class__.__module__}.{extn.__class__.__qualname__}', extn.adds_statements(), ))
        if extn.adds_statements():
            for name, handler in extn.statement_handlers().items():
                if name in STATEMENT_HANDLERS:
                    raise ValueError(f'Extension {extn_name!r} tried to redefine {name!r}')
                STATEMENT_HANDLERS[name] = handler
        add_functions(extn_name, extn.functions().items())
    dd.set_var(list(list(extn) for extn in extns), *('vgr', 'extensions'))
    return VER

def create_parser(extn_registry: VgrExtensionRegistry, debug: bool, verbose: bool) -> Lark:
    if verbose: print_stderr('Creating parser...')
    extn_statements = ''
    extn_grammar = ''
    for name, instance in extn_registry:
        # By convention, if an extension says it has statements
        # it should have a like named rule in its grammar
        if instance.adds_statements(): extn_statements += f'| {name}_statements'
        extn_grammar += instance.grammar()
        if not extn_grammar.endswith('/n'): extn_grammar += '\n'
    print_debug(debug, 'EXTN_STATMENTS =', extn_statements)
    print_debug(debug, 'EXTN_GRAMMAR =', extn_grammar)
    grammar = VgrExtension.read_resource_text(__package__, 'vgr.lark')
    # NB: we can't just use str.format() because the grammar
    #     contains "{" and "}"
    for tag, value in (('{EXTN_STATEMENTS}', extn_statements),
                       ('{EXTN_GRAMMAR}', extn_grammar),
                       ('{FUNCTIONS}', get_function_defs()),
                       ('{VAR_NAME}', VAR_NAME)):
        grammar = grammar.replace(tag, value)
    print_debug(debug, 'GRAMMAR =\n', grammar)
    return Lark(grammar,
                start=['opt_statements', 'expr', _CMD_LINE_ASSIGN],
                lexer='contextual',
                parser='lalr',
                debug=True,
                propagate_positions=True,
                cache=True)

class SaveOrderedSources(argparse.Action):
    def __call__(self, *args, **_):
        # unpack here rather than in signature to appease pylint
        _, namespace, values, option = args
        if not hasattr(namespace, "ordered"):
            namespace.ordered = []
        namespace.ordered.append((option.lstrip('-')[0].lower(), values))

def print_debug(debug: bool, /, *args, **kwargs) -> None:
    """If debug is on print to stderr and maybe the log"""
    if debug:
        print_stderr(*args, **kwargs)
        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug(*args, **kwargs)

def log_exception(ctx: ExecContext, log_label: str, e: VgrException) -> None:
    err = str(e)
    print_stderr(err)
    if ctx.debug:
        _LOG.exception(log_label)
        traceback.print_exc(file=sys.stderr)
    elif not isinstance(e, VgrExitingException):
        _LOG.error(f"{log_label}\n{err}")

def main():
    clp = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='vgr',
        description=f'Version {__version__} ({__version_date__})',
        epilog="""Statements added with --execute, --file, --include, and --assign are executed in the order they are given.

Following that, statements are read from stdin if they are available.

If no --execute, --file, --stdin arguments are given, and stdin is interactive, the REPL is started.

Additional arguments are added as strings to the "args" list variable.

--verbose, --debug, and --echo control initial settings only. Commands in --execute, --file, and --assign can change them.

Environment variables:
  - OFS/ORS - output field and record separators for the Print statement
  - VGR_PATH - Path used by Source and @Include statements
  - VGR_PROMPT - REPL prompt with limited Bash-like escapes supported
  - VGR_HISTORY - path to REPL's history file
  - VGR_HISTORY_SIZE - max number of lines stored in history
"""
    )
    clp.add_argument('--version', '-V', action='version', version=f'{__version__} {__version_date__}',
                     help='Display version information and exit')
    clp.add_argument('--execute', '-e', metavar='STATEMENTS', action=SaveOrderedSources,
                     help='Execute the given statements')
    clp.add_argument('--file', '-f', metavar='FILE', action=SaveOrderedSources,
                     help="Execute statements stored in a file")
    clp.add_argument('--include', '-i', metavar='FILE', action=SaveOrderedSources,
                     help="Load statements stored in a file once")
    clp.add_argument('--assign', '-v', metavar='var=expr', action=SaveOrderedSources,
                     help="Assign a value to a variable")
    clp.add_argument('--verbose', action='store_true',
                     help='Enable verbose mode')
    clp.add_argument('--debug', '-D', action='store_true',
                     help='Enable debug mode')
    clp.add_argument('--echo', action='store_true',
                     help='Enable statement echo')
    clp.add_argument('--stdin', action='store_true',
                     help='Execute commands read from stdin after all other actions')
    clp.add_argument('--logfile', type=str, default=None,
                     help='Path to the log file')
    clp.add_argument('--loglevel', type=str, default='info',
                     help='Root logging level (debug, info, warning, error, critical, or off)')
    clp.add_argument('--logoverwrite', action='store_true',
                     help='Overwrite log file instead of appending')
    clp.add_argument('--gen-vsc-extn', action='store_true',
                     help='Generate a Visual Studio Code extension and exit')
    clp.add_argument('args', nargs='*', metavar='arg', default=[],
                     help='Additional arguments. Values maybe booleans, numbers, or strings')
    args = clp.parse_args()

    logfile_path = init_logging(args.logfile, args.loglevel, args.logoverwrite)
    _LOG.info('Starting')
    # Since it's startup, and everything else relies on the DD...
    if args.verbose: print('Creating data dictionary...', file=sys.stderr)
    dd = DataDictionary()
    dd_init(dd)
    add_builtin_functions() # Done prior to loading extensions to prevent them overwriting
    extensions = load_extensions(dd, args.verbose)
    parser = create_parser(extensions, args.debug, args.verbose)
    md_create_lexer(parser)

    if args.gen_vsc_extn:
        create_vscode_extension(args.debug, parser, function_names_pattern())
        sys.exit(VgrExitingException.EXIT_SUCCESS)

    ctx = create_exec_context(parser, dd)
    ctx.debug = args.debug
    ctx.verbose = args.verbose
    ctx.echo = args.echo
    init_app_log(ctx, logfile_path, args.loglevel)
    ctx.print_verbose('Setting user args...')
    set_user_args(ctx, args.args)
    # Dump some basics for diagnostic purposes
    for path in [EXEC_NAME_PATH, EXEC_VER_PATH, VER_PATH, VER_DATE_PATH]:
        value = ctx.get_var(*path)
        var = '.'.join(path)
        ctx.print_verbose(var, '=', poly_repr(value))
        _LOG.info('%s = %s', var, poly_repr(value))
    # These control how some requests are made, so
    # it is good to know their values when there are
    # issues with certificates
    for var in ['REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE']:
        value = os.environ.get(var)
        if value:
            ctx.print_verbose(var, '=', poly_repr(value))
            _LOG.info('%s = %s', var, poly_repr(value))
    _LOG.info('Ready')

    # NB: args.execute and args.file will always be None
    #     as there values have been accumulated in
    #     args.ordered so they can be handled in the order
    #     received. Additionally, each option can be
    #     an ordered list.
    exit_code: int = VgrExitingException.EXIT_SUCCESS
    try:
        ordered_args = args.ordered if hasattr(args, "ordered") else []
        # Execute accumulated -e, -f, et al options in the order given
        cmds_provided = False
        for opt in ordered_args:
            stype, svalue = opt
            try:
                if stype  == 'e': # -e or --execute
                    # Simple statements directly on the command line
                    ctx.print_verbose('Executing statements from command line...')
                    ctx.execute_statements(svalue, '<cmd-line>')
                    cmds_provided = True
                    continue
                if stype == 'f': # -f or --file
                    # NB: we don't "sandbox" these input files like we do with others
                    do_source(ctx, find_vgr_source(svalue))
                    cmds_provided = True
                    continue
                # NB: include and assign are NOT counted as commands,
                #     as the former is assumed to be sourced for function definitions]
                #     not executed for side effects, and assignments are for
                #     internal state change
                if stype == 'i': # -i or --include
                    # Files to be included once
                    do_include(ctx, find_vgr_source(svalue))
                    continue
                if stype in ['v', 'a']: # -v or --assign
                    ctx.execute_statements(svalue, '<cmd-line>', _CMD_LINE_ASSIGN)
                    continue
            except VgrException as e:
                raise e
            except Exception as e:
                raise VgrException(None, e, '<cmd-line>', svalue) from e
            # SNO
            raise NotImplementedError(f'Statement source {stype!r} not implemented') # pragma no cover
        if args.stdin:
            # Read from stdin, most likely from a "here" document
            # but can be from a pipe or just a "<"
            ctx.print_verbose('Executing statements from stdin...')
            ctx.execute_statements(sys.stdin.read(), '<stdin>')
        else:
            if sys.stdin.isatty() and not cmds_provided:
                ctx.print_verbose('Starting the REPL...')
                exit_code = VGRCmdLine(ctx).run()
                ctx.print_verbose('REPL exited')
    except VgrExitingException as e:
        exit_code = e.exit_code
        if isinstance(e, VgrStatementAbort):
            log_exception(ctx, 'Aborted', e)
        if isinstance(e, VgrStatementAssert):
            log_exception(ctx, 'Assertion', e)
    except VgrException as e:
        exit_code = VgrExitingException.EXIT_FAILED
        log_exception(ctx, 'Exception', e)
    except Exception as e: # pylint: disable=broad-exception-caught
        # Last resort catch: log it and exit
        exit_code = VgrExitingException.EXIT_FAILED
        log_exception(ctx, 'Exception', VgrException(None, e, None, None))
    ctx.print_verbose('Exit code is', exit_code)
    _LOG.info('Exiting')
    sys.exit(exit_code)
