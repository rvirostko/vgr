from abc import ABC, abstractmethod
from argparse import ArgumentParser, ArgumentError, ArgumentTypeError, Namespace, OPTIONAL
from shutil import which
from typing import Iterable
import ast
import os
import re
import signal
import socket
import subprocess
import time
import sys
import traceback

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from .builtins import poly_to_boolean, expand_filename

from .app_exceptions import (
    VgrException,
    VgrExitingException,
    VgrStatementAbort,
    VgrStatementAssert,
)
from .builtins import poly_type
from .exec_context import ExecContext
from .md_print import md_println
from .repl_help import repl_help

from . import __version__, __version_date__, __description__

class CustomArgParser(ArgumentParser):
    """A non-exiting argument parser"""
    def error(self, message):
        """Format a ValueError the way we want and don't exit"""
        raise ValueError(message[0].upper() + message[1:] )

class ParserBuilder(ABC):
    """Helper for fluent building of ArgumentParser instances"""
    def __init__(self):
        self._parser = CustomArgParser(add_help=False, exit_on_error=False, prog='', description=None, usage=None)

    def parser(self) -> ArgumentParser:
        """Return the parser we just built"""
        return self._parser

    def argument(self, *args, **kwargs) -> "ParserBuilder":
        """Add the argument and continue"""
        self._parser.add_argument(*args, **kwargs)
        return self

class LimitedFileHistory(FileHistory):
    """A file-based history that enforces a max line limit"""
    def __init__(self, filename: str='.history', max_history: int=100):
        super().__init__(filename)
        self.max_length = max_history

    @property
    def max_length(self):
        return self._max_length

    @max_length.setter
    def max_length(self, value):
        self._max_length = min(max(2, value), 2048)
        if self._loaded: self.store_string(None)

    def load_history_strings(self) -> Iterable[list]:
        if not os.path.exists(self.filename): return
        count = 0
        with open(self.filename, "r", encoding="utf-8", errors='backslashreplace') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        yield ast.literal_eval(line)
                        count += 1
                        if count >= self._max_length: return
                    except (SyntaxError, ValueError):
                        continue

    def store_string(self, _string: str) -> None:
        if len(self._loaded_strings) > self.max_length:
            self._loaded_strings = self._loaded_strings[:self.max_length]
        with open(self.filename, "w", encoding="utf-8", errors='backslashreplace') as f:
            for e in self._loaded_strings:
                # Serialize using repr() so it can be read by ast.literal_eval
                f.write(f'{e!r}\n')

    def clear(self) -> None:
        """Clear the history"""
        self._loaded_strings = []
        with open(self.filename, "w", encoding="utf-8", errors='backslashreplace') as f:
            f.close()

class VgrHistory(LimitedFileHistory):
    def __init__(self, filename, max_lines):
        super().__init__(filename, max_lines)

    def append_string(self, string: str) -> None:
        # No need to stuff these into the history
        if string.strip().casefold() not in ["exit", "history"]:
            super().append_string(string)

class VgrRepl:

    _CD_PARSER: ArgumentParser = (ParserBuilder()
                    .argument('path', nargs=OPTIONAL, type=str, default='~')
                    .parser())
    _HISTORY_PARSER: ArgumentParser = (ParserBuilder()
                    .argument('--clear', action="store_const", const=True, default=None)
                    .argument('--max', type=int)
                    .parser())
    _MULTILINE_PARSER: ArgumentParser = (ParserBuilder()
                    .argument('multiline', nargs=OPTIONAL, type=poly_to_boolean)
                    .parser())
    _NO_ARGS_PARSER: ArgumentParser = ParserBuilder().parser()

    _PROMPT_ESCAPES = {
        "\\": lambda: '\\',                               # Escaped backslash
        "$": lambda: '$',
        "d": lambda: time.strftime('%a %b %d'),           # Date
        "e": lambda: '\033',                              # Escape character
        "H": socket.gethostname,                          # Full hostname
        "h": lambda: socket.gethostname().split('.')[0],  # Short hostname
        "n": lambda: '\n',
        "t": lambda: time.strftime('%H:%M:%S'),           # Time
        "u": lambda: os.getenv('USER', 'unknown'),
        "w": os.getcwd,                                   # Full path
        "W": lambda: os.path.basename(os.getcwd()),       # Name only
    }

    def __init__(self, ctx: ExecContext):
        assert ctx
        self._ctx = ctx
        self._history_filename = os.getenv("VGR_HISTORY", '~/.vgr_history')
        self._max_history_entries = os.getenv("VGR_HISTORY_SIZE", 100)
        self.print_verbose("Loading history from", self.history_filename)
        self.print_verbose("Max history entries is", self.max_history_entries)
        self._history = VgrHistory(self.history_filename, self.max_history_entries)
        self.multiline = False
        self._dispatch = {}
        self.add_cmd("cd", self._exec_cd)
        self.add_cmd("help", repl_help)
        self.add_cmd("history", self._exec_history)
        self.add_cmd("multiline", self._exec_multiline)
        self.add_cmd("pwd", self._exec_pwd)
        self.add_cmd("shell", self._exec_subshell)

    def add_cmd(self, cmd: str, func) -> None:
        self._dispatch[cmd] = func

    def _exec_cd(self, *args) -> None:
        values = self._parse(self._CD_PARSER, *args)
        if values is not None:
            path = os.path.abspath(os.path.expanduser(values.path))
            try:
                os.chdir(path)
                self.print_verbose('Changed to', os.getcwd())
            except FileNotFoundError:
                print(path, 'does not exist')
            except PermissionError:
                print('You do not have permission to access', path)

    def _exec_pwd(self, *args) -> None:
        values = self._parse(self._NO_ARGS_PARSER, *args)
        if values is not None: print(os.getcwd())

    def _exec_history(self, *args):
        values = self._parse(self._HISTORY_PARSER, *args)
        if values is not None:
            if all(value is None for value in vars(values).values()):
                for i, line in enumerate(self._history.get_strings(), start=1): print(f"{i}: {line}")
            else:
                if values.clear is not None:
                    self._history.clear()
                    self.print_verbose('History cleared')
                if values.max is not None:
                    try:
                        self._max_history_entries = int(values.max)
                    except ValueError:
                        self._max_history_entries = 100
                    self.print_verbose('History max entries =', values.max)

    def _exec_multiline(self, *args):
        values = self._parse(self._MULTILINE_PARSER, *args)
        if values is not None:
            if values.multiline is not None: self.multiline = values.multiline
            self.print_verbose('Multiline mode is', self.multiline)
            # TODO get better def for "meta" on win/linux/mac and display nicely
            if self.multiline: print('Use Meta-Return to execute commands')

    def _exec_subshell(self, *args) -> None:
        if os.name == "nt":
            ps_env = any(var.endswith("PSModulePath") for var in os.environ)
            ps = which("powershell.exe")
            if ps_env and ps:
                shell = ps
                cmd_flag = "-Command"
            else:
                shell = "cmd.exe"
                cmd_flag = "/c"
        else:
            # POSIX (Linux, macOS, WSL, etc.)
            shell = os.environ.get('SHELL', '/bin/sh')
            cmd_flag = "-c"
        old_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
        try:
            if args:
                # Command(s) executed by the shell
                subprocess.run([shell, cmd_flag, args[0]], check=False)
            else:
                # Interactive shell for a human
                subprocess.run([shell], check=False)
        except OSError as e:
            # Only failure we care about: shell could not be created
            raise RuntimeError(f"Unable to start '{shell}': {e}") from e
        finally:
            signal.signal(signal.SIGINT, old_handler)

    def _parse_command(self, line: str):
        """Q&D parsing of a command line so we can check for REPL commands"""
        def remove_quotes(s: str) -> str:
            return  s[1:-1] if len(s) >= 2 and ((s[0] == s[-1]) and s[0] in ('"', "'")) else s
        stripped = line.lstrip()
        if not stripped: return None
        # Split on spaces, string quoted args
        tokens = list(re.finditer(r'"[^"]*"|\'[^\']*\'|\S+|^\S*[!]', stripped))
        if not tokens: return None
        first_match = tokens.pop(0)
        first = remove_quotes(first_match.group(0))
        if first.lower() in ("!", "shell"):
            # Everything after first token becomes a single argument
            rest_start = first_match.end()
            rest = stripped[rest_start:]
            return "shell", [rest] if rest else []
        # Otherwise, return first + cleaned tokens
        return first, [remove_quotes(m.group(0)) for m in tokens]

    def _expand_prompt(self) -> str:
        """Expands the Bash-like prompt sequences"""
        # replaces /<x> from _PROMPT_ESCAPES and handling //<x> to escape one
        # does not handle other backslash escaping or anything sophisticated
        return re.sub(r'[\\](.)',
                    lambda match : self._PROMPT_ESCAPES.get(match.group(1), lambda : match.group(1))(),
                    self.prompt)

    def _parse(self, parser: ArgumentParser, *args) -> Namespace:
        try:
            return parser.parse_args(args)
        except (ArgumentError, ArgumentTypeError, TypeError, ValueError) as e:
            # NB: no internal redirection here!
            if self._ctx.verbose:
                print(e, file=sys.stderr)
            else:
                print(e.args[0] if e.args else f'{poly_type(e)!r}', file=sys.stderr)
            return None

    def print_verbose(self, *args, **kwargs) -> None:
        self._ctx.print_verbose(*args, **kwargs)

    @abstractmethod
    def execute_statements(self, text: str) -> bool: pass

    @property
    def prompt(self) -> str:
        prompt = self._ctx.get_var("env", "VGR_PROMPT")
        return 'vgr> ' if prompt is None else prompt

    @property
    def history_filename(self) -> str: return expand_filename(self._history_filename)

    @property
    def max_history_entries(self) -> int: return self._max_history_entries

    def run(self) -> int:
        md_println("\n", f"`VGR {__version__} ({__version_date__})`", "_Type **help** for more information_")
        self._ctx.set_var(True, 'vgr', 'repl')
        session = PromptSession(history=self._history)
        while True:
            try:
                prompt = self._expand_prompt()
                if self.multiline and not prompt.endswith('\n'): prompt += '\n'
                text: str = session.prompt(prompt, multiline=self.multiline)
            except KeyboardInterrupt:
                continue
            except EOFError:
                return 0
            else:
                if not text.isspace():
                    # Determine if the user entered a REPL command rather than
                    # a statement to be executed
                    r = self._parse_command(text)
                    if r is not None:
                        command, options = r
                        if command in self._dispatch:
                            self._dispatch[command](*options)
                            continue
                    # Didn't look like a REPL command, so it must be a statement
                    loop, exit_code = self.execute_statements(text)
                    if not loop:
                        return exit_code

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
