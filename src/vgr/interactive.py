"""
The base of a Unix-like editable command line. Include some commands for history control
and simple file control. Also the base of a "help" system.
"""

from abc import ABC, abstractmethod
from argparse import ArgumentParser, ArgumentError, ArgumentTypeError, Namespace, OPTIONAL
from typing import Iterable
import ast
import os
import re
import socket
import subprocess
import time

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from .mathpak import poly_bool, expand_filename

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
        with open(self.filename, "r", encoding="utf-8") as f:
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
        with open(self.filename, "w", encoding="utf-8") as f:
            for e in self._loaded_strings:
                # Serialize using repr() so it can be read by ast.literal_eval
                f.write(f'{e!r}\n')

    def clear(self) -> None:
        """Clear the history"""
        self._loaded_strings = []
        with open(self.filename, "w", encoding="utf-8") as f:
            f.close()

class VgrHistory(LimitedFileHistory):
    def __init__(self, filename, max_lines):
        super().__init__(filename, max_lines)

    def append_string(self, string: str) -> None:
        # No need to stuff these into the history
        if string.strip().casefold() not in ["exit", "history"]:
            super().append_string(string)

class CmdLine:
    _DEFAULT_HISTORY_SIZE = 100

    _CD_PARSER: ArgumentParser = (ParserBuilder()
                    .argument('path', nargs=OPTIONAL, type=str, default='~')
                    .parser())
    _HISTORY_PARSER: ArgumentParser = (ParserBuilder()
                    .argument('--clear', action="store_const", const=True, default=None)
                    .argument('--max', type=int)
                    .parser())
    _MULTILINE_PARSER: ArgumentParser = (ParserBuilder()
                    .argument('multiline', nargs=OPTIONAL, type=poly_bool)
                    .parser())
    _PROMPT_PARSER: ArgumentParser = (ParserBuilder()
                    .argument('template', nargs=OPTIONAL, type=str)
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

    def __init__(self):
        self._prompt = self._prompt or '> '
        self._history_filename = self._history_filename or '.history'
        self._max_history_entries = self._max_history_entries or 100
        self.print_verbose("Loading history from", self.history_filename)
        self.print_verbose("Max history entries is", self.max_history_entries)
        self._history = VgrHistory(self.history_filename, self.max_history_entries)
        self.multiline = False
        self._dispatch = {}
        self.add_cmd("cd", self._exec_cd)
        self.add_cmd("help", self._exec_help)
        self.add_cmd("history", self._exec_history)
        self.add_cmd("multiline", self._exec_multiline)
        self.add_cmd("prompt", self._exec_prompt)
        self.add_cmd("pwd", self._exec_pwd)
        self.add_cmd("!", self._exec_subshell)
        self.add_cmd("shell", self._exec_subshell)

    def add_cmd(self, cmd: str, func) -> None:
        self._dispatch[cmd] = func

    def _exec_cd(self, *args) -> None:
        """
**REPL: Change the current working directory**

* **cd** : changes to the user's home directory
* **cd _dir_** : changes to the given directory

Execution of statements are sandboxed to the current directory, so if you
need to change location after starting a session you can use this command.
"""
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
        """
**REPL: Print the current working directory**

* **pwd** : prints the name of the current directory
"""
        values = self._parse(self._NO_ARGS_PARSER, *args)
        if values is not None: print(os.getcwd())

    def _exec_history(self, *args):
        """
**REPL: Command History**

* **history** : display recent history
* **history --clear** : clear history
* **history --max _n_** : set the maximum commands saved
"""
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
                        self._max_history_entries = self._DEFAULT_HISTORY_SIZE
                    self.print_verbose('History max entries =', values.max)

    def _exec_multiline(self, *args):
        """
**REPL: Multiline Editing Mode**

* **multiline** : display the current setting
* **multiline [True | False]** : set multiline editing mode

When multiline editing mode is on, you can create multiple line statements to be executed;
Return starts a new line rather than executing the command.
To execute commands in multiline editing mode, use **META-Return** instead.
"""
        values = self._parse(self._MULTILINE_PARSER, *args)
        if values is not None:
            if values.multiline is not None: self.multiline = values.multiline
            self.print_verbose('Multiline mode is', self.multiline)
            if self.multiline: print('Use Meta-Return to execute commands')

    def _exec_prompt(self, *args):
        r"""
**REPL: Change the Prompt**

* **prompt** : print the template used to generate the interactive prompt
* **prompt _template_** : set the prompt to the template

The template supports a limited set of values that are defined by the
Bash Shell:

* **\d** - the date
* **\e** - the escape character
* **\h** - host name, short
* **\H** - host name, full
* **\n** - a new line
* **\t** - the time
* **\u** - user name
* **\w** - current directory
* **\W** - current directory, name only

On start up, the prompt template comes from **VGR_PROMPT** in the environment.
Changes made at runtime are not persistent.
"""
        values = self._parse(self._PROMPT_PARSER, *args)
        if values is not None:
            if values.template is None:
                print(f'prompt is {self.prompt!r}')
            else:
                self._prompt = values.template
                self.print_verbose(f'Prompt changed to {self.prompt!r}')

    def _exec_subshell(self, *args) -> None:
        """
**REPL: Open an OS sub-shell**

* **shell** : open an interactive sub-shell
* **shell** _command_: run the command in a sub-shell

You can use **!** as an alias for **shell**
"""
        if os.name == "nt":
            # Prefer MSYS2 / Git Bash / Cygwin if they set SHELL
            shell = os.environ.get('SHELL')
            if shell and shell.endswith('bash'):
                shell = [shell]
            else:
                # Fall back to cmd.exe only, never PowerShell
                shell = [os.environ.get('COMSPEC', 'cmd.exe')]
        else:
            # POSIX (Linux, macOS, WSL, etc.)
            shell = [os.environ.get('SHELL', '/bin/sh')]
        if args:
            cmd = ' '.join(args).strip()
            subprocess.run(cmd, shell=True, executable=shell[0], check=False)
        else:
            subprocess.run(shell, check=False)

    def _exec_help(self, *args) -> None: pass

    def _print_doc(self, func) -> None: pass

    def _parse_command(self, line: str):
        """Q&D parsing of a command line so we can check for REPL commands"""
        stripped = line.strip()
        if not stripped: return None
        # Detect sub-shell escape
        if stripped.startswith("!"):
            # parts: command marker "!", and the rest as a single string
            rest = stripped[1:].lstrip()
            return "!", [rest] if rest else []
        # Split on spaces, string quoted args
        parts = [next(filter(None, m.groups()), '') for m in re.finditer(r'"([^"]*)"|\'([^\']*)\'|(\S+)', stripped)]
        if not parts: return None
        return parts[0], parts[1:]

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
            self.print_exception(e)
            return None

    @abstractmethod
    def print_exception(self, e: Exception) -> None: pass

    @abstractmethod
    def print_verbose(self, *args, **kwargs) -> None: pass

    @abstractmethod
    def execute_statements(self, text: str) -> bool: pass

    @property
    def prompt(self) -> str: return self._prompt

    @property
    def history_filename(self) -> str: return expand_filename(self._history_filename)

    @property
    def max_history_entries(self) -> int: return self._max_history_entries

    def run(self) -> None:
        session = PromptSession(history=self._history)
        while True:
            try:
                prompt = self._expand_prompt()
                if self.multiline and not prompt.endswith('\n'): prompt += '\n'
                text: str = session.prompt(prompt, multiline=self.multiline)
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
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
                    if not self.execute_statements(text):
                        break
