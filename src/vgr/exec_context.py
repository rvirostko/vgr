"""
Execution context
"""

from abc import ABC, abstractmethod
from typing import Any, Iterable

from lark import Lark, Tree, Token

from .data_dict import DataDictionary, DynamicValue

class ExecContext(ABC):

    def __init__(self, parser: Lark, dd: DataDictionary):
        super().__init__()
        assert parser is not None
        self._parser = parser
        assert dd is not None
        self._dd = dd
        self._debug = False
        self._echo = False
        self._verbose = False
        self.set_var(DynamicValue(lambda: self.debug), 'vgr',  'debug')
        self.set_var(DynamicValue(lambda: self.echo), 'vgr', 'echo')
        self.set_var(DynamicValue(lambda: self.verbose), 'vgr', 'verbose')

    @property
    def parser(self) -> Lark:
        """Return the parser used by this context"""
        return self._parser

    @property
    def dd(self) -> DataDictionary:
        """Return the data dictionary used by this context"""
        return self._dd

    @property
    def debug(self) -> None:
        """Has the user requested debugging output"""
        return self._debug

    @debug.setter
    def debug(self, v: bool) -> None:
        """Turn debug mode on or off"""
        self._debug = bool(v)

    def print_debug(self, *args, **kwargs) -> None:
        """Print a debug message

        Although this checks for debug, check debug before calling
        if the arguments are not simple constants
        """
        if self.debug: self.print_stderr(*args, **kwargs)

    @property
    def echo(self) -> None:
        """Should statements be echoed"""
        return self._echo

    @echo.setter
    def echo(self, v: bool) -> None:
        """Turn statement echoing on and off"""
        self._echo = bool(v)

    @property
    def verbose(self) -> None:
        """Has the user requested detailed output"""
        return self._verbose

    @verbose.setter
    def verbose(self, v: bool) -> None:
        """Turn verbose mode on or off"""
        self._verbose = bool(v)

    def print_verbose(self, *args, **kwargs) -> None:
        """Print verbose output

        Although this checks for verbose, check verbose before calling
        if the arguments are not simple constants
        """
        if self.verbose: self.print_stderr(*args, **kwargs)

    def get_var(self, *path: str) -> Any:
        """Returns a value from the data dictionary given a path"""
        return self.dd.get_var(*path)

    def set_var(self, data: Any, /, *path: str) -> Any:
        """Sets a value in the data dictionary given a path"""
        return self.dd.set_var(data, *path)

    def var_exists(self, *path: str) -> tuple[bool, str, Any]:
        """
        Checks to see if a value exists in the data dictionary,
        returning a boolean indicator, the full name of the
        variable, and its current value if any.
        """
        return self.dd.var_exists(*path)

    def set_var_user(self, data: Any, /, *path: str) -> Any:
        """Deprecated: should make sure path is checked before calling set_var()"""
        return self.dd.set_var_user(data, *path)

    @abstractmethod
    def parse_expression(self, expr_text: str) -> Tree:
        """Parse the text as an expression

        Args:
            expr_text: the expression text
        """

    @abstractmethod
    def execute_statements(self, statement_text: str, origin: str, start: str=None) -> None:
        """Parse the text and execute the resulting statements

        Args:
            statement_text: Source text containing statements
            origin: Human readable origin of the statements, typically file name or
                &lt;name&gt; for transient source
            start: Name of a parser rule, ie how this should be interpreted
        """

    @abstractmethod
    def dispatch_statements(self, statements: Iterable[Tree]) -> None:
        """Given a sequence of parsed statements dispatch them to their handlers"""

    @abstractmethod
    def eval_expr(self, expr: Any) -> Any: pass

    @abstractmethod
    def eval_expr_or_const(self, expr: Any) -> Any: pass

    def eval_to_str(self, expr: Tree, name: str, allow_none: bool=False) -> str:
        """Helper that makes sure you got a string back from an expression

        Args:

            expr: a parsed expression
            name: the name of an argument or other source item
            allow_none: is None a valid value?
        """
        rc = self.eval_expr(expr)
        if rc is None and allow_none: return None
        if not isinstance(rc, str): raise self.type_error(expr, name, "string", rc)
        return rc

    def eval_filename_expr(self, expr: Any, allow_none: bool=False) -> str:
        """Helper that gets a string that should be a relative filename

        Args:

            expr: a parsed expression
            allow_none: is None a valid value?
        """
        filename = self.eval_to_str(expr, 'File name', allow_none)
        try:
            return self.verify_relative_path(filename)
        except OSError as e:
            raise self.wrap_error(expr, e) from e

    def eval_to_int(self, expr: Tree, name: str, allow_none: bool=False) -> int:
        value = self.eval_expr(expr)
        if value is None and allow_none: return None
        if isinstance(value, (bool, int)): return int(value)
        import math
        if isinstance(value, float):
            if math.isfinite(value): return int(value)
            raise self.wrap_error(expr, ValueError(f'Cannot convert {value!r} to an integer'))
        if isinstance(value, str):
            try:
                if rc := self.str_to_int(value) is not None: return rc
                raise self.wrap_error(expr, ValueError(f'Cannot convert {value!r} to an integer'))
            except ValueError as e:
                raise self.wrap_error(expr, e) from e
        raise self.type_error(expr, name, "integer", value)

    def eval_to_number(self, expr: Tree, name: str, allow_none: bool=False):
        """Helper that evaluate an expression to a number

        Ints and floats are returned as-is.
        Strings are converted to numbers via str_to_number().
        Booleans are converted to 0 or 1.
        May return None, Inf, or Nan.
        """
        value = self.eval_expr(expr)
        if value is None and allow_none: return None
        if isinstance(value, bool): return int(value)
        if isinstance(value, (int, float)): return value
        if isinstance(value, str):
            try:
                if (rc := self.str_to_number(value)) is not None: return rc
                raise self.wrap_error(expr, ValueError(f'Cannot convert {value!r} to a number'))
            except ValueError as e:
                raise self.wrap_error(expr, e) from e
        raise self.type_error(expr, name, "number", value)

    def eval_to_bool(self, expr: Tree, name: str, allow_none: bool=False) -> bool:
        # TODO see other conv routines
        rc = self.eval_expr(expr)
        if rc is None and allow_none: return None
        if isinstance(rc, (bool, int, float)): return bool(rc)
        if isinstance(rc, str):
            try:
                return self.str_to_bool(rc)
            except ValueError:
                # Not, null, and not empty, so Python truthy
                return True
        raise self.type_error(expr, name, "boolean", rc)

    def echo_source(self, tree: Tree, end_tree :Tree=None) -> None:
        """Echo the source for the tree to stderr if echo is on"""
        if self.echo:
            src = self.get_source(tree, end_tree)
            src = src.splitlines()[0] if src else '--unknown--'
            if self.verbose:
                # prefix the source with file and line number
                self.print_stderr(f'{self.source_name()}{self.source_location(tree)} :', src)
            else:
                # just the source
                self.print_stderr(src)

    def type_error(self, item, name: str, desired_type: str, value_found:Any) -> Exception:
        """Create a TypeError in context with a parsed item

        Args:
            item: either a Tree or a Token from the parsed source
            name: the name of an argument or other source item
            desired_type: string name for what would be acceptable
            value_found: what was found instead
        """
        return self.wrap_error(item, TypeError(f'{name} must be a {desired_type}; found {self.type_name(value_found)!r}'))

    def print_tree(self, item: Any, indent: int=2) -> None:
        """Prints the parse tree including position information to stderr

        Args:

            item: the parsed item, either a Tree or Token
        """
        def _fmt_pos(meta) -> str:
            if meta:
                values = tuple(getattr(meta, attr, None) for attr in ("line", "column", "end_line", "end_column"))
                if None not in values:
                    return ' (Pos: {}:{}-{}:{})'.format(*values)
            return ''

        prefix = ' ' * indent # Indentation for nested levels
        if isinstance(item, Tree):
            tree: Tree = item
            op = getattr(tree, "op_name", lambda: "")()
            pos_info = _fmt_pos(tree.meta)
            self.print_stderr(f'{prefix}({tree.data}:{op}{pos_info}',
                            end=('\n' if tree.children else ''))
            for child in tree.children: self.print_tree(child, indent + 2)
            self.print_stderr(f'{prefix if tree.children else ""})')  # close the rule
        else:
            if isinstance(item, Token):
                token: Token = item
                pos_info = _fmt_pos(token)
                self.print_stderr(f'{prefix}{token.type}: {token.value!r} {self.type_name(token.value)!r}{pos_info}')
            else:
                # SNO: What else can there be?
                raise ValueError(item.type()) # pragma no cover

    @abstractmethod
    def get_source(self, tree: Tree, end_tree: Tree=None) -> str:
        """Return the source for the parsed statements"""

    @abstractmethod
    def source_name(self) -> str:
        """Return an abbreviated name for the current source"""

    @abstractmethod
    def source_location(self, tree: Tree) -> str:
        """Return a string containing the line and column for the tree's source"""

    @abstractmethod
    def print_stderr(*args, **kwargs) -> None:
        """Like print() except output goes to where "Error" stream is directed (see Open)"""

    @abstractmethod
    def wrap_error(self, item, error: Exception) -> Exception:
        """Wrap the error, giving it context with the parsed item

        Args:
            item: either a Tree or a Token from the parsed source
            error: the exception reflecting the problem at hand
        """

    @abstractmethod
    def type_name(self, value: Any) -> str:
        """Return a string representation for value's type"""

    @abstractmethod
    def verify_relative_path(self, filename: str) -> str:
        """
        The filename must be relative to the current directory.
        Returns filename unchanged.
        """

    @abstractmethod
    def str_to_number(self, string: str) -> Any:
        """
        Attempts to convert a string to a number value

        Returns None for blank (zero length) and empty (all spaces) strings.
        Can return Inf and Nan. Raises ValueError if conversion to a float cannot be performed.
        """

    @abstractmethod
    def str_to_int(self, string: str) -> Any:
        """Attempts to convert a string to an integer value

        See str_to_number() - forces an integer result.
        May return None.
        """

    @abstractmethod
    def str_to_bool(self, string: str) -> bool:
        """Attempts to convert a string to a boolean.

        Understand "true" and "false" and other versions.
        If the string can be converted to a number,
        it is compared against zero.
        """
