"""
Functor compilation and execution
"""

from abc import ABC, abstractmethod
from typing import Any

from lark import Tree, Token

from app_exceptions import (
    VgrException,
    VgrStatementBreak,
    VgrStatementContinue,
    VgrStatementReturn,
)
from exec_context import ExecContext
from mathpak import type_str

class _VgrCallable(ABC):

    # we should show where it came from... file and start line/col
    # probably need a generic "meta" object that covers that and the source
    # which was kind of what SSM was supposed to be
    def __init__(self, param_paths: list[tuple[str]]):
        assert isinstance(param_paths, (list, tuple))
        self._param_paths = param_paths

    def __repr__(self): return self._sig() + '\u2192' + str(self)

    def _sig(self): return '(' +  ','.join('.'.join(t) for t in self._param_paths) + ')'

    def _create_locals_list(self, arg_values: list) -> list:
        # Pad values if not enough args were provided
        # In that way, we have a default value of "None"
        if len(arg_values) < len(self._param_paths):
            arg_values = arg_values + [None] * (len(self._param_paths) - len(arg_values))
        return list(zip(self._param_paths, arg_values))

class _AbstractUserFunction(_VgrCallable):
    _SELF_PATH = ('self',)

    def __str__(self): return '<function>'

    def evaluate(self, ctx: ExecContext, arg_values: list) -> Any:
        try:
            # Needs to be copy-on-write
            ctx.dd.push_frame(self._create_locals_list(arg_values))
        except Exception as e:
            # Push did not work, so we not only skip
            # evaluation, but also the pop
            raise e
        try:
            return self._evaluate(ctx)
        except (VgrStatementContinue, VgrStatementBreak) as e:
            # We can't let these popagate outside the function scope.
            # rewrap removes their special meaning.
            raise VgrException.rewrap(e) from e
        finally:
            ctx.dd.pop_frame()

    @abstractmethod
    def _evaluate(self, ctx: ExecContext) -> Any: pass

    def _create_locals_list(self, arg_values: list) -> list:
        # Adds the "self" after the named parameters
        rc = super()._create_locals_list(arg_values)
        rc.append((self._SELF_PATH, self))
        return rc

class UserFunction(_AbstractUserFunction):
    def __init__(self, param_paths: list[tuple[str]], statements: list):
        super().__init__(param_paths)
        assert statements is not None and isinstance(statements, list)
        self._statements = statements

    def _evaluate(self, ctx: ExecContext) -> Any:
        try:
            # If no "return" is encountered we return None
            ctx.dispatch_statements(self._statements)
            return None
        except VgrStatementReturn as e:
            return e.return_value

    @staticmethod
    def invoke(ctx: ExecContext, fn: Any, arg_values: list) -> Any:
        """
        Handles the attempted execution of an a user defined function.
        None is ignored, and the execution is distributed across lists
        """
        if fn is None: return None
        if isinstance(fn, _AbstractUserFunction): return fn.evaluate(ctx, arg_values)
        # Recursively process lists and dictionaries
        if isinstance(fn, (list, tuple)):
            return type(fn)(UserFunction.invoke(ctx, f1, arg_values) for f1 in fn)
        if isinstance(fn, dict):
            return {key: UserFunction.invoke(ctx, value, arg_values) for key, value in fn.items()}
        # This allows the user to be sloppy and for us to work through lists and dicts
        # without damaging the structure
        return fn

    @staticmethod
    def from_expression(source: str, expr: Tree, param_paths: list[tuple[str]]):
        return _ArrowFunction(source, expr, param_paths)

    @staticmethod
    def compile(ctx: ExecContext, source: Any, param_paths: list[tuple[str]]) -> Any:
        """Constructs an Arrow Function from source text"""
        if source is None: return None
        if isinstance(source, str):
            # Normally we expect a string to parse
            return _ArrowFunction(source, ctx.parse_expression(source), param_paths)
        if isinstance(source, _ArrowFunction):
            # This effectively changes the argument paths (maybe)
            return UserFunction.compile(ctx, source._source, param_paths)
        if isinstance(source, (list, tuple)):
            # Create a list of Arrow Functions
            return type(source)(UserFunction.compile(ctx, s1, param_paths) for s1 in source)
        if isinstance(source, (int, float, bool)):
            # These should end up being functions returning constants
            return UserFunction.compile(ctx, str(source), param_paths)
        raise TypeError(f'Cannot use {type_str(source)} as the source for an Arrow Function')

class _ArrowFunction(_AbstractUserFunction):
    """
**Arrow Functions - lightweight functions**

#### Definition
* Set _variable_ = () -> _expression_
* Set _variable_ = (_arg_ [, _arg_]...) -> _expression_
* Set _variable_ = (...) -> Compile( _expression_ )

#### Invocation
* @_variable_(_arg_...) - Stand-alone
* _value_.@_variable_(_arg_...) - Inline

Arrow Functions are for short expressions and recursive cases, not for full multi-statement functions.
Parameters need not be declared if empty. Names of parameters follow the rules for variables, but
are a single name, not a dotted path.
The arrow operator separates the parameter list from the body.
The body is either an expression or a dynamic expression using _Compile_(...).

### Special Rules
* Inside the function, the variable `self` is the same function for recursive calls
* If a parameter is `Unset` inside a function it exposes a global value if one exists
* When invoked inline, the preceeding _value_ is the first argument passed to the function
* Arrow Functions can read but not change global state except by acting on arguments that are
  passed by reference, such as lists and dictionaries

### Examples

Missing and extra arguments
```
    Set add = (x, y) -> x + y
    Print @add(5) → None     // x defaults to None
    Print @add(5, 6) → 11
    Print @add(5, 6, 7) → 11 // Extra arg ignored
```

Recursive function using compact notation
```
    fact(n) -> (n <= 1 ? 1 : n * @self(n - 1))
    Print @fact(5) → 120
```

Dynamically compiled expression
```
    Accept op From stdin
    Assert op in ["+", "-", "*", "/"]
    Set dyn = (x, y) -> Compile("(x {} y) + 10".Format(op))
```

Invocation of variables which are _not_ functions
```
    Unset a
    Print @a() → None
    Set a = "Hello"
    Print @a(1, 2) → "Hello"
```
    """

    def __init__(self, source: str, expr: Tree, param_paths: list[tuple[str]]):
        super().__init__(param_paths)
        assert source and isinstance(source, str)
        self._source = source
        assert expr and isinstance(expr, (Tree, Token))
        self._expr = expr

    def __str__(self): return self._source

    def _evaluate(self, ctx: ExecContext) -> Any:
        return ctx.eval_expr(self._expr)

class UserProcedure(_VgrCallable):
    def __init__(self, param_paths: list[tuple[str]], statements: list):
        super().__init__(param_paths)
        assert statements is not None and isinstance(statements, list)
        self._statements = statements
        self._restore_values = None

    def __str__(self): return '<procedure>'

    def execute(self, ctx: ExecContext, arg_values: list, restore_paths: list) -> None:
        try:
            # NEED TYPE
            # for setting:
            #.  if frame has it, use that (its a local)
            #.  if base has it, use that (its a global)
            #.  nobody had it, create it as a local
            ctx.dd.push_frame(self._create_locals_list(arg_values))
        except Exception as e:
            # Push did not work, so we not only skip
            # evaluation, but also the pop
            raise e
        try:
            ctx.dispatch_statements(self._statements)
        except VgrStatementReturn:
            # In procedures there is no return value
            # but the return does end its execution
            pass
        except (VgrStatementContinue, VgrStatementBreak) as e:
            # We can't let these popagate outside the procedure's scope.
            # rewrap removes their special meaning.
            raise VgrException.rewrap(e) from e
        finally:
            # get the values of the locals we set
            restore_values = [ctx.get_var_user(*path) for path in self._param_paths]
            # discard the frame that contained them
            ctx.dd.pop_frame()
            # now restore their values into the frame where they were defined
            for path, value in zip(restore_paths, restore_values):
                if path is not None: ctx.set_var_user(value, *path)
