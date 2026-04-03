import atexit
import sys
from io import IOBase
from io import UnsupportedOperation

_STDIN = 'stdin'
_STDOUT = 'stdout'
_STDERR = 'stderr'
_ALL_STREAMS = (_STDIN, _STDOUT, _STDERR)

_OPEN_STREAMS = {}

class Redirection():
    """Redirection for a standard stream (stdin, stdout, stderr)"""
    def __init__(self, name: str):
        if name is None: raise ValueError('Missing attribute name')
        assert name in _ALL_STREAMS
        self._name = name
        _OPEN_STREAMS[self._name] = None
        self._filename = None

    def _stream(self) -> IOBase:
        """Avoid 'pickle' issue with Dynamic value"""
        return _OPEN_STREAMS[self._name]

    def file(self) -> IOBase:
        """Get the file associated with the redirection"""
        return self._stream() if self._stream() else getattr(sys, self._name)

    def filename(self) -> str:
        """Get the file name associated with the redirection"""
        return self._filename or ("<" + self._name + ">")

    def isatty(self) -> bool:
        return self.file().isatty()

    def redirect_to(self, *args, **kwargs):
        """
* With an file instance, redirection to this stream begins. This file is considered "shared".
* With a file name, the file is opened and redirection begins. You can pass in a mode and encoding
  keyword parameters. This file is considered "owned" by the redirection.
"""
        if not args: return self
        filename = args[0]
        mode = kwargs.get('mode', 'w')
        dest = open(filename,
                    mode=mode,
                    encoding=kwargs.get('encoding', 'utf-8-sig' if mode == 'r' else 'utf-8'),
                    errors=kwargs.get('errors', 'replace'))
        self.end_redirect()
        _OPEN_STREAMS[self._name] = dest
        self._filename = filename
        return self

    def end_redirect(self):
        """Close the active redirect if it is not shared"""
        try:
            # This gets the value from _OPEN_STREAMS...
            stream = self._stream()
            if stream and not stream.closed:
                stream.flush()
                stream.close()
            return self
        finally:
            _OPEN_STREAMS[self._name] = None
            self._filename = None

class IORedirector:
    """Singleton used to handle redirection that sits on top of stdin, stdout, stderr.
It does not change the actual versions in sys, but provides a layer in front of them.

The stdin(), stdout(), and stderr() methods are used to interact with the files.
They are polymorphic:

At process termination, all redirections are ended.
"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(IORedirector, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_redirectors'):
            self._redirectors = {}
            for name in ('stdin', 'stdout', 'stderr'): self._redirectors[name] = Redirection(name)
            atexit.register(self.end_redirects)

    def get_stream(self, stream: str) -> Redirection: return self._redirectors[stream]

    def stdin(self) -> Redirection: return self.get_stream('stdin')

    def stdout(self) -> Redirection: return self.get_stream('stdout')

    def stderr(self) -> Redirection: return self.get_stream('stderr')

    def end_redirects(self) -> None:
        for redirector in self._redirectors.values():
            try:
                redirector.end_redirect()
            except (OSError, UnsupportedOperation, ValueError):
                pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_redirects()
