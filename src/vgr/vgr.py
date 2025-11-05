
from typing import Any
import argparse
import logging
import os
import re
import sys
import traceback

from lark import Lark
from rapidfuzz.fuzz import ratio

from .app_exceptions import (
    VgrException,
    VgrExitingException,
    VgrStatementAssert,
)
from .data_dict import DataDictionary
from .dd_config import (
    dd_init,
    set_user_args,
    EXEC_NAME_PATH,
    EXEC_VER_PATH,
    VER_DATE_PATH,
    VER_PATH,
)
from .doc_help import (
    create_md_lexer,
    keyword_pattern,
    print_doc,
    print_md,
    search_entries,
    unique_by_func,
)
from .extn import VgrExtension, VgrExtensionRegistry, VER
from .functions import (
    add_builtin_functions,
    add_function,
    function_names_pattern,
    get_function_defs,
    get_function_entries,
    get_operator_entries,
)
from .interactive import CmdLine, ArgumentParser, ParserBuilder
from .log_config import init_logging, set_logging_level
from .mathpak import (
    poly_repr,
    type_str,
)
from .redir import print_stderr
from .exec_context import ExecContext
from .stmt_exec import (
    create_exec_context,
    do_source,
    do_include,
    find_vgr_source,
    get_statement_entries,
    STATEMENT_HANDLERS,
)
from .vscode_extn import create_vscode_extension

from . import __version__, __version_date__, __description__

LOG = logging.getLogger()

class VGRCmdLine(CmdLine):
    _EXIT_PATTERN = re.compile(r"^\s*exit\b", re.IGNORECASE)
    _DEFAULT_HISTORY = '~/.vgr_history'
    _DEFAULT_PROMPT = 'vgr> '

    _SOURCE_PARSER: ArgumentParser = (ParserBuilder()
                    .argument('file', type=str)
                    .parser())

    def __init__(self, ctx: ExecContext):
        assert ctx
        self._ctx = ctx
        self._prompt = self._get_vgr_default('prompt', self._DEFAULT_PROMPT)
        self._history_filename = self._get_vgr_default('history', self._DEFAULT_HISTORY)
        self._max_history_entries = self._get_vgr_default('history_size', CmdLine._DEFAULT_HISTORY_SIZE)
        super().__init__()
        self._help_topics = {
            ("cd",):               lambda _topic, _q: print_doc(self._exec_cd),
            ("function",):         self._print_function_help,
            ("help", "topics", "?", "/h", "/?") : lambda _topic, _q: print_doc(self._exec_help),
            ("history",):          lambda _topic, _q: print_doc(self._exec_history),
            ("multiline",):        lambda _topic, _q: print_doc(self._exec_multiline),
            ("operator", "ops", "op"):  self._print_operator_help,
            ("prompt",):           lambda _topic, _q: print_doc(self._exec_prompt),
            ("pwd",):              lambda _topic, _q: print_doc(self._exec_pwd),
            ("shell",):            lambda _topic, _q: print_doc(self._exec_subshell),
            ("statement", "stmt"): self._print_statement_help,
            ("version", "ver"):    self._print_version,
        }

    def run(self):
        print_md('_Type **exit** to exit_')
        return super().run()

    def execute_statements(self, text: str) -> bool:
        if self._EXIT_PATTERN.match(text): return False
        try:
            self._ctx.execute_statements(text.rstrip(), '<repl>')
        except VgrException as e:
            if self._ctx.debug:
                traceback.print_exc(file=sys.stderr)
            else:
                print(str(e))
        except Exception as e: # pylint: disable=broad-exception-caught
            if self._ctx.debug:
                traceback.print_exc(file=sys.stderr)
            else:
                print(str(VgrException(None, e, None, None)))
        return True

    def print_verbose(self, *args, **kwargs) -> None:
        self._ctx.print_verbose(*args, **kwargs)

    def print_exception(self, e: Exception) -> None:
        if self._ctx.verbose:
            print(e, file=sys.stderr)
        else:
            print(e.args[0] if e.args else f'{type_str(e)}', file=sys.stderr)

    def _get_vgr_default(self, env_var: str, default: Any) -> str:
        """Look for a matching environment variable (uppercase) and return it or the default value"""
        return os.getenv('VGR_' + env_var.upper(), default)

# TODO we can start to carve up the READ-ME into parts to add to
# language topics.
    def _exec_help(self, *args) -> None:
        """
**Language Topics**

* **function** : Search functions for help
* **operator** : Search operators for help
* **statement** : Search statements for help

If no value is provided with **function**, **operator**, or **statement**, a list
of the associated items is displayed.

**help** used with any other value searches through
language features looking for an exact match.

For example **help Add** with return informtion for `Add()` while
**help statement Add** is required to get information for the like-named statement.

**REPL Topics**

* **cd** : Change the current working directory
* **history** : Display or control command line history
* **multiline** : Turn on multiline editing mode
* **prompt** : Define the input input prompt
* **pwd** : Print the current working directory
* **shell** : Work with the OS sub-shell
* **topics** : This help information
* **version** : Print version informtion

"""
        if len(args) < 1:
            topic = "help"
            q = ""
        else:
            topic = args[0].strip().lower()
            targs = args[1:]
            q = (' '.join(targs) if targs else '').strip()
        if bool(re.search(r"\([^)]*\)$", topic)):
            self._print_function_help("", topic + ' ' + q)
            return
        for key in sorted(self._help_topics.keys()):
            for topic_key in key:
                # short topics need to be an exact match, longer ones can be fuzzy
                if topic_key == topic  if len(topic) <= 4 else ratio(topic_key, topic) >= 70.0:
                    self._help_topics[key](topic, q)
                    return
        self._default_help_action(topic, q)

    def _default_help_action(self, topic: str, q: str) -> None:
        # If no explicit topic that matches, then see what we can find
        # in statements, functions, and operators
        q = topic + ' ' + q
        func_help = self._get_function_help(q)
        if len(func_help) == 1:
            self._display_function_help(q, func_help)
        else:
            op_help = self._get_operator_help(q)
            if len(op_help) == 1:
                self._display_operator_help(q, op_help)
            else:
                stmt_help = self._get_statement_help(q)
                if stmt_help:
                    self._display_statement_help(q, stmt_help)
                else:
                    print()
                    print_md('_Use **help topics** to list topics_')
                    print()

    def _print_statement_help(self, topic: str, q: str) -> None:
        results = self._get_statement_help(q) if q else self._all_help(get_statement_entries())
        self._display_statement_help(q, results)

    def _print_function_help(self, topic: str, q: str) -> None:
        results = self._get_function_help(q) if q else self._all_help(get_function_entries())
        self._display_function_help(q, results)

    def _print_operator_help(self, topic: str, q: str) -> None:
        results = self._get_operator_help(q) if q else self._all_help(get_operator_entries())
        self._display_operator_help(q, results)

    def _print_version(self, topic: str, q: str) -> None:
        print_md(f'**{__version__} {__version_date__}**')

    def _all_help(self, entries: list) -> list:
        return unique_by_func([(name, entries[name][0]) for name in sorted(entries.keys())])

    def _get_operator_help(self, q) -> list:
        return search_entries(get_operator_entries(), q)

    def _get_statement_help(self, q) -> list:
        return search_entries(get_statement_entries(), q)

    def _get_function_help(self, q) -> list:
        return search_entries(get_function_entries(), q)

    def _display_operator_help(self, q, results) -> None:
        results = [(func.bound_ops[0], func) for _name, func in results]
        self._display_help_results("Operators", q, results)

    def _display_statement_help(self, q, results) -> None:
        self._display_help_results("Statements", q, results)

    def _display_function_help(self, q, results) -> None:
        results = [(name + "()", func) for name, func in results]
        self._display_help_results("Functions", q, results)

    def _display_help_results(self, search_type: str, q: str, results: list) -> None:
        if len(results) == 0:
            # We could not find anything
            print()
            print_md(f'_Nothing matches{" " + repr(q) if q else ""}_')
            print()
        elif len(results) == 1:
            # We got an single match
            # Show the help for the item
            print_doc(results[0][1])
        else:
            # Multiple results
            # Show as a list with a summary
            lines = []
            lines.append(f'**{"Search Results" if q else search_type}-**')
            for name, func in results:
                doc = (func.__doc__ or "").strip()
                if doc:
                    # Display first non-blank line, stripped of bolding (the convention) and no sentence
                    lines.append(f'* `{name}` - {doc.splitlines()[0].strip().strip("*").rstrip(".")}')
                else:
                    lines.append(f'* `{name}`')
            print()
            print_md('\n'.join(lines))
            print()

def load_extensions(dd: DataDictionary, verbose: bool) -> VgrExtensionRegistry:
    if verbose: print_stderr('Loading extensions...')
    VER.load(dd, __package__, 'extensions.ini')
    extns = []
    for extn_name, extn in VER:
        extns.append((extn_name, f'{extn.__class__.__module__}.{extn.__class__.__qualname__}',extn.adds_statements(), extn.extends_select(), ))
        if extn.adds_statements():
            for name, handler in extn.statement_handlers().items():
                if name in STATEMENT_HANDLERS:
                    raise ValueError(f'Extension {extn_name!r} tried to redefine {name!r}')
                STATEMENT_HANDLERS[name] = handler
        for func_name, func in extn.functions().items():
            add_function(extn_name, func_name, func)
    dd.set_var(extns, *('vgr', 'extensions'))
    return VER

def create_parser(extn_registry: VgrExtensionRegistry, debug: bool, verbose: bool) -> Lark:
    if verbose: print_stderr('Creating parser...')
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
    print_debug(debug, 'EXTN_STATMENTS =', extn_statements)
    print_debug(debug, 'EXTN_FROM =', extn_from)
    print_debug(debug, 'EXTN_GRAMMAR =', extn_grammar)
    grammar = VgrExtension.read_resource_text(__package__, 'vgr.ebnf')
    # NB: we can't just use str.format() because the grammar
    #     contains "{" and "}"
    for tag, value in (('{EXTN_STATEMENTS}', extn_statements),
                       ('{EXTN_FROM}', extn_from),
                       ('{EXTN_GRAMMAR}', extn_grammar),
                       ('{FUNCTIONS}', get_function_defs())):
        grammar = grammar.replace(tag, value)
    print_debug(debug, 'GRAMMAR =\n', grammar)
    return Lark(grammar,
                start=['opt_statements', 'expr'],
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
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug(*args, **kwargs)

def log_exception(ctx: ExecContext, log_label: str, e: VgrException) -> None:
    LOG.exception(log_label)
    print_stderr(str(e))
    if ctx.debug:
        traceback.print_exc(file=sys.stderr)
        print_debug(ctx.debug, e)

def main():
    clp = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=f'Version {__version__} ({__version_date__})',
        epilog="""Statements added with --source and --file are executed in the order they are given.

Following that, statements are read from stdin if they are available.

If no --source and --file arguments are given, and stdin is interactive, by default the REPL is started. Using --repl false prevents it from opening.

Additional arguments are added to the "args" variable. Only simple data types can be set. Quotes are not required for strings.

--verbose, --debug, and --echo control only the initial settings. Commands in --source and --file arguments can still change them when running.

Environment variables:
  - OFS/ORS - output field and record separators as defined by AWK
  - VGR_PATH - Path used by Source and @Include in a manner similar to AWK
  - VGR_PROMPT - REPL prompt; limited Bash-like escapes supported
  - VGR_HISTORY - path to REPL's history file
  - VGR_HISTORY_SIZE - max number of lines stored in history
"""
    )
    clp.add_argument('--version', '-V', action='version', version=f'{__version__} {__version_date__}')
    clp.add_argument('--source', '-e', metavar='STATEMENTS', action=SaveOrderedSources,
                    help='Execute the given statements')
    clp.add_argument('--file', '-f', metavar='FILE', action=SaveOrderedSources,
                     help="Execute statements stored in a file")
    clp.add_argument('--include', '-i', metavar='FILE', action=SaveOrderedSources,
                     help="Load statements stored in a file once")
    clp.add_argument('--verbose', action='store_true', help='Enable/disable verbose mode')
    clp.add_argument('--debug', '-D', action='store_true', help='Enable/disable debug mode')
    clp.add_argument('--echo', action='store_true', help='Enable/disable statement echo')
    clp.add_argument('--repl', action='store_true', help='Request REPL. REPL automatically starts if --source/--file are not used')
    clp.add_argument('--logfile', type=str, default=None,
                    help='Path to the log file')
    clp.add_argument('--loglevel', type=str, default='info',
                    help='Logging level (debug, info, warning, error, critical)')
    clp.add_argument('--logoverwrite', action='store_true',
                    help='Overwrite log file instead of appending')
    clp.add_argument('--gen-vsc-extn', action='store_true',
                     help='Generate a VSCode extension for syntax highlighting')
    clp.add_argument('args', nargs='*', metavar='arg',
                    default=[], help='Additional arguments. Values maybe booleans, numbers, or strings')
    args = clp.parse_args()

    init_logging(args.logfile, args.logoverwrite)
    set_logging_level(args.loglevel)
    LOG.info('Starting')
    # Since it's startup, and everything else relies on the DD...
    if args.verbose: print('Creating data dictionary...', file=sys.stderr)
    dd = DataDictionary()
    dd_init(dd)
    add_builtin_functions() # Done prior to loading extensions to prevent them overwriting
    extensions = load_extensions(dd, args.verbose)
    parser = create_parser(extensions, args.debug, args.verbose)

    if args.gen_vsc_extn:
        create_vscode_extension(keyword_pattern(parser), function_names_pattern())
        sys.exit(VgrExitingException.EXIT_SUCCESS)
    create_md_lexer(parser)

    ctx = create_exec_context(parser, dd)
    ctx.debug = args.debug
    ctx.verbose = args.verbose
    ctx.echo = args.echo
    ctx.print_verbose('Setting user args...')
    set_user_args(ctx, args.args)
    # Dump some basics for diagnostic purposes
    for path in [EXEC_NAME_PATH, EXEC_VER_PATH, VER_PATH, VER_DATE_PATH]:
        value = ctx.get_var(*path)
        var = '.'.join(path)
        ctx.print_verbose(var, '=', poly_repr(value))
        LOG.info('%s = %s', var, poly_repr(value))
    # These control how some requests are made, so
    # it is good to know their values when there are
    # issues with certificates
    for var in ['REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE']:
        value = os.environ.get(var)
        if value:
            ctx.print_verbose(var, '=', poly_repr(value))
            LOG.info('%s = %s', var, poly_repr(value))
    LOG.info('Ready')

    # NB: args.execute and args.file will always be None
    #     as there values have been accumulated in
    #     args.ordered so they can be handled in the order
    #     received. Additionally, each option can be
    #     an ordered list.
    exit_code: int = VgrExitingException.EXIT_SUCCESS
    try:
        ordered_args = args.ordered if hasattr(args, "ordered") else []
        # Accumulated -e/-f options, stored in the order given
        for opt in ordered_args:
            stype, svalue = opt
            if stype in ['e', 's']: # -e or --source
                # Simple statements directly on the command line
                ctx.print_verbose('Executing statements from command line...')
                ctx.execute_statements(svalue, '<cmd-line>')
                continue
            try:
                if stype == 'f': # -f or --file
                    # NB: we don't "sandbox" these files like we do with others
                    do_source(ctx, find_vgr_source(svalue))
                    continue
                if stype == 'i': # -i or --include
                    # Files to be included once
                    do_include(ctx, find_vgr_source(svalue))
                    continue
            except VgrException as e:
                raise e
            except Exception as e:
                raise VgrException(None, e, '<cmd-line>', svalue) from e
            raise NotImplementedError(f'Statement source {stype!r} not implemented') # SNO
        if sys.stdin.isatty():
            if args.repl is True or not ordered_args:
                ctx.print_verbose('Starting the REPL...')
                VGRCmdLine(ctx).run()
                ctx.print_verbose('REPL exited')
        else:
            # Read from stdin, most likely from a "here" document
            # but can be from a pipe or just a "<"
            ctx.print_verbose('Executing statements from stdin...')
            ctx.execute_statements(sys.stdin.read(), '<stdin>')
    except VgrExitingException as e:
        exit_code = e.exit_code
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
    LOG.info('Exiting')
    sys.exit(exit_code)
