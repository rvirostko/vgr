import atexit
import sys
from io import IOBase
from io import UnsupportedOperation

from ..mathpak import poly_type

class Redirection():
    """Redirection for a standard stream (stdin, stdout, stderr)"""
    def __init__(self, name: str):
        if name is None: raise ValueError('Missing attribute name')
        name = name.strip().lower()
        if name not in ('stdin', 'stdout', 'stderr'): raise ValueError(f'Cannot redirect {name}')
        self._name = name
        self._redirection = None
        self._shared = False

    def file(self) -> IOBase:
        return self._redirection if self._redirection else getattr(sys, self._name)

    def redirect_to(self, *args, **kwargs):
        if not args: return self
        first_arg = args[0]
        if first_arg is None: return self.end_redirect()
        # Redirect a shared output
        if isinstance(first_arg, IOBase):
            return self._redirect_to_file(first_arg, True)
        # Redirect to an output we own
        if isinstance(first_arg, str):
            return self._redirect_to_file(
                open(first_arg,
                    mode=kwargs.get('mode', 'w'),
                    encoding=kwargs.get('encoding', 'utf-8')))
        raise TypeError(f'Unsupported argument type: {poly_type(first_arg)!r}')

    def _redirect_to_file(self, destination: IOBase, shared: bool=False):
        self.end_redirect()
        if destination:
            self._redirection = destination
            self._shared = shared
        return self

    def end_redirect(self):
        try:
            # Close the active redirection if we own it
            if not self._shared and self._redirection and not self._redirection.closed:
                self._redirection.flush()
                self._redirection.close()
            return self
        finally:
            self._redirection = None
            self._shared = False

class IORedirector:
    """Singleton used to handle redirection that sits on top of stdin, stdout, stderr.
It does not change the actual versions in sys, but provides a layer in front of them.

The stdin(), stdout(), and stderr() methods are used to interact with the files.
They are polymorphic:
* With no arguments, you get the current stream
* With an file instance, redirection to this stream begins. This file is considered "shared".
* With a file name, the file is opened and redirection begins. You can pass in a mode and encoding
  keyword parameters. This file is considered "owned" by the redirection.
* With an argument of None, any current redirection is ended and you get the default stream.
  Outputs owned by the redirection are closed, shared outputs simply stop being redirected.

At process termination, all redirections are ended.
"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(IORedirector, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_redirectors'):
            self._redirectors = (Redirection('stdin'), Redirection('stdout'), Redirection('stderr'))
            atexit.register(self.end_redirects)

    def stdin(self, *args, **kwargs) -> IOBase:
        return self._redirectors[0].redirect_to(*args, **kwargs).file()

    def stdout(self, *args, **kwargs) -> IOBase:
        return self._redirectors[1].redirect_to(*args, **kwargs).file()

    def stderr(self, *args, **kwargs) -> IOBase:
        return self._redirectors[2].redirect_to(*args, **kwargs).file()

    def end_redirects(self) -> None:
        for redirector in self._redirectors:
            try:
                redirector.end_redirect()
            except (OSError, UnsupportedOperation, ValueError):
                pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_redirects()
