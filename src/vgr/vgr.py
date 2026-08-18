
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
    VgrStatementAbort,
    VgrStatementAssert,
)
from .auto_doc import (
    gen_auto_docs,
    read_doc_file,
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
from .doc_help import (
    create_md_lexer,
    constants_pattern,
    keyword_pattern,
    print_doc,
    md_println,
    search_entries,
    unique_by_func,
)
from .extn import VgrExtension, VgrExtensionRegistry, VER
from .functions import (
    add_builtin_functions,
    add_functions,
    function_names_pattern,
    get_function_defs,
    get_function_entries,
)
from .operators import (
    get_operator_entries,
)
from .interactive import CmdLine, ArgumentParser, ParserBuilder
from .dist_meta import (
    read_license_file,
    get_authors,
)
from .log_config import init_logging
from .redir import print_stderr
from .exec_context import ExecContext
from .stmt_exec import (
    create_exec_context,
    get_statement_entries,
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

from . import __version__, __version_date__, __description__

_CMD_LINE_ASSIGN = 'cmd_line_assign'

_LOG = logging.getLogger()

class VGRCmdLine(CmdLine):
    _DEFAULT_HISTORY = '~/.vgr_history'
    _DEFAULT_PROMPT = 'vgr> '

    _SOURCE_PARSER: ArgumentParser = (ParserBuilder()
                    .argument('file', type=str)
                    .parser())

    def __init__(self, ctx: ExecContext):
        assert ctx
        self._ctx = ctx
        self._history_filename = self._get_vgr_default('history', self._DEFAULT_HISTORY)
        self._max_history_entries = self._get_vgr_default('history_size', CmdLine._DEFAULT_HISTORY_SIZE)
        super().__init__()
        self._heading_re = re.compile(r'^(#+)\s+(.*)$', re.MULTILINE)
        self._anchor_link_re = re.compile(r'\[([^\]]+)\]\(#([^)]+)\)')
        self._html_anchor_re = re.compile(r'<a\s+id="[^"]+"></a>', re.IGNORECASE)
        self._collapse_newlines_re = re.compile(r'\n{2,}')
        func_key = ("function", "func",)
        op_key = ("operator", "ops", "op",)
        stmt_key = ("statement", "stmt",)
        self._help_topics = {
            func_key:                  self._print_function_help,
            ("help", "topics", "?",) : lambda _topic, _q: print_doc(self._exec_help),
            op_key:                    self._print_operator_help,
            ("repl",):                 self._print_repl_help,
            stmt_key:                  self._print_statement_help,
            ("running",):              self._print_running_help,
            ("license",):              self._print_license_help,
            ("authors",):              self._print_authors_help,
            ("variables",):            self._print_variables_help,
            ("list",):                 self._print_type_list,
        }
        self._list_topics = {
            func_key:  self._list_functions,
            op_key:    self._list_operators,
            stmt_key:  self._list_statements,
        }

    def run(self) -> int:
        if self._ctx.verbose: self._ctx.print_verbose("CWD =", os.getcwd())
        md_println(f"\n`VGR {__version__} ({__version_date__})`")
        md_println('_Type **help** for more information_')
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

    def _get_vgr_default(self, env_var: str, default: Any) -> str:
        """Look for a matching environment variable (uppercase) and return it or the default value"""
        return os.getenv('VGR_' + env_var.upper(), default)

    def _exec_help(self, *args) -> None:
        """
**Help Topics**

* **functions** : Show help on using functions or search for one by name
* **list [functions | statements | operators]** : List the names of the available items
* **operators** : Show help on using operators or search for one by name
* **repl** : Show help on using the REPL
* **running** : How to run VGR
* **statements** : Show help on using statements or search for one by name
* **variables** : Using variables in VGR
* **license** : The license which governs VGR's use
* **authors** : VGR's authors

If no value is provided with **function**, **operator**, or **statement**,
some general information is displayed.

**help** used with any other value searches through
language features looking for an exact match.

For example **help Add** will return informtion for `Add()` while
**help statement Add** is required to get information for the like-named statement.

"""
        if len(args) < 1:
            topic = "help"
            q = ""
        else:
            topic, *targs = args
            topic = topic.strip().lower()
            q = (' '.join(targs) if targs else '').strip()
        if bool(re.search(r"\([^)]*\)$", topic)):
            self._print_function_help("", topic + ' ' + q)
            return
        for key in sorted(self._help_topics.keys()):
            for topic_key in key:
                # short topics need to be an exact match, longer ones can be fuzzy
                if self._fuzzy_match(topic_key, topic):
                    self._help_topics[key](topic, q)
                    return
        self._default_help_action(topic, q)

    def _fuzzy_match(self, key: str, s: str) -> bool:
        # short items need to be an exact match, longer ones can be fuzzy
        return key == s  if len(s) <= 4 else ratio(key, s) >= 70.0

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
                    md_println('_Use **help topics** to list topics_')
                    print()

    def _md_fixup(self, text: str) -> str:
        text = self._anchor_link_re.sub(r'`\1`', text)
        text = self._html_anchor_re.sub('', text)
        text = self._heading_re.sub(lambda m: f"**{m.group(2).strip()}**", text)
        return self._collapse_newlines_re.sub('\n\n', text)

    def _print_md_doc(self, filename: str) -> None:
        print()
        md_println(self._md_fixup(read_doc_file(filename)))
        print()

    def _print_running_help(self, _topic: str, _q: str) -> None:
        self._print_md_doc("running.md")

    def _print_license_help(self, _topic: str, _q: str) -> None:
        print()
        md_println(self._md_fixup(read_license_file()))
        print()

    def _print_authors_help(self, _topic: str, _q: str) -> None:
        md_println(self._md_fixup(get_authors()))
        print()

    def _print_variables_help(self, _topic: str, _q: str) -> None:
        self._print_md_doc("variables.md")

    def _print_type_list(self, _topic: str, q: str) -> None:
        sub_topic = q
        for key in sorted(self._list_topics.keys()):
            for list_key in key:
                if self._fuzzy_match(list_key, sub_topic):
                    self._list_topics[key]()
                    return
        self._default_help_action('', q)

    def _print_repl_help(self, _topic: str, _q: str) -> None:
        self._print_md_doc("repl.md")

    def _print_statement_help(self, _topic: str, q: str) -> None:
        if q:
            self._display_statement_help(q, self._get_statement_help(q))
        else:
            self._print_md_doc("statements.md")

    def _list_statements(self) -> None:
        all_stmts = self._all_help(get_statement_entries())
        all_stmts.sort(key=lambda t: t[0])
        self._display_statement_help(None, all_stmts)

    def _print_function_help(self, _topic: str, q: str) -> None:
        if q:
            self._display_function_help(q, self._get_function_help(q))
        else:
            self._print_md_doc("functions.md")

    def _list_functions(self) -> None:
        all_funcs = self._all_help(get_function_entries())
        all_funcs.sort(key=lambda t: t[0])
        self._display_function_help(None, all_funcs)

    def _print_operator_help(self, _topic: str, q: str) -> None:
        if q:
            self._display_operator_help(q, self._get_operator_help(q))
        else:
            self._print_md_doc("operators.md")

    def _list_operators(self) -> None:
        all_ops = self._all_help(get_operator_entries())
        all_ops.sort(key=lambda t: t[1].bound_ops[0])
        self._display_operator_help(None, all_ops)

    def _all_help(self, entries: list) -> list:
        return unique_by_func([(name, entries[name][0]) for name in entries.keys()])

    def _get_operator_help(self, q: str) -> list:
        return search_entries(get_operator_entries(), q)

    def _get_statement_help(self, q: str) -> list:
        return search_entries(get_statement_entries(), q)

    def _get_function_help(self, q: str) -> list:
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
            md_println(f'_Nothing matches{" " + repr(q) if q else ""}_')
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
            md_println('\n'.join(lines))
            print()

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
    clp.add_argument('--gen-doc', action='store_true',
                     help='Generate documentation and exit')
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
    create_md_lexer(parser)

    if args.gen_doc: gen_auto_docs()
    if args.gen_vsc_extn:
        create_vscode_extension(args.debug,
                                keyword_pattern(parser),
                                constants_pattern(parser),
                                function_names_pattern())
    if args.gen_doc or args.gen_vsc_extn: sys.exit(VgrExitingException.EXIT_SUCCESS)

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
