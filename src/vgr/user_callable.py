"""
Function creation and execution
"""

from abc import abstractmethod
from typing import Any

from lark import Tree, Token

from .app_exceptions import (
    VgrException,
    VgrStatementBreak,
    VgrStatementContinue,
    VgrStatementReturn,
)
from .builtins import poly_type
from .exec_context import ExecContext
from .result_cache import ResultCacheRegistry, ResultCache
from .src_mgr import SSM
from .vgr_callable import VgrCallable

_CACHE_REGISTRY = ResultCacheRegistry()

def clear_caches() -> None:
    # NB: _CACHE_REGISTRY.clear() clears out the registry itself!
    for key in _CACHE_REGISTRY.keys(): _CACHE_REGISTRY[key].clear()

def cache_keys() -> list:
    return _CACHE_REGISTRY.keys()

class AbstractUserCallable(VgrCallable):
    _SELF_PATH = ('$self',)
    _ARGS_PATH = ('$args',)

    # we should show where it came from: file and start line/col
    # probably need a generic "meta" object that covers that and the source
    # which was kind of what SSM was supposed to be
    def __init__(self, statement: Tree, cache_size: int, param_paths: list[tuple[str]]):
        assert isinstance(param_paths, list)
        self._param_paths = param_paths
        # NB: this may return NONE, which is correct based on the cache size
        self._result_cache = _CACHE_REGISTRY.create(f"{SSM.current[0]}::{statement.meta.line}::{statement.meta.column}::{id(self)}", cache_size)

    def __repr__(self): return self._sig() + '\u2192' + str(self)

    def evaluate(self, ctx: ExecContext, arg_values: list) -> Any:
        result_key = None
        if self._result_cache is not None:
            found, result_key, value = self._result_cache.fetch(ResultCache.create_key(*arg_values))
            if found: return value
        ctx.dd.push_frame(self._create_locals_list(arg_values))
        try:
            result = self._evaluate(ctx)
            if self._result_cache is not None:
                self._result_cache.store(result_key, result)
            return result
        except (VgrStatementContinue, VgrStatementBreak) as e:
            # We can't let these popagate outside the function scope.
            # rewrap removes their special meaning.
            raise VgrException.rewrap(e) from e
        finally:
            ctx.dd.pop_frame()

    @property
    def cache_key(self) -> str:
        return None if self._result_cache is None else self._result_cache.key

    @property
    def cache_info(self) -> dict:
        return None if self._result_cache is None else self._result_cache.info

    def clear_cache(self) -> None:
        if self._result_cache: self._result_cache.clear()

    @abstractmethod
    def _evaluate(self, ctx: ExecContext) -> Any: pass

    def _create_locals_list(self, arg_values: list) -> list:
        # Pad values if not enough args were provided
        # In that way, we have a default value of "None"
        if len(arg_values) < len(self._param_paths):
            arg_values = arg_values + [None] * (len(self._param_paths) - len(arg_values))
        rc = list(zip(self._param_paths, arg_values))
        # Adds the "self" and "args" after the named parameters
        rc.append((self._SELF_PATH, self))
        rc.append((self._ARGS_PATH, arg_values))
        return rc

    def _sig(self): return '(' +  ','.join('.'.join(t) for t in self._param_paths) + ')'

class UserFunction(AbstractUserCallable):
    def __init__(self, statement: Tree, cache_size: int, param_paths: list[tuple[str]], statements: list):
        super().__init__(statement, cache_size, param_paths)
        assert statements is not None and isinstance(statements, list)
        self._statements = statements

    def __str__(self): return '<function>'

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
        None is ignored, and the execution is distributed across lists and dictionaries.

        """
        if fn is None: return None
        if isinstance(fn, AbstractUserCallable): return fn.evaluate(ctx, arg_values)
        # Recursively process lists and dictionaries
        if isinstance(fn, list):
            return list(UserFunction.invoke(ctx, f1, arg_values) for f1 in fn)
        if isinstance(fn, dict):
            return {key: UserFunction.invoke(ctx, value, arg_values) for key, value in fn.items()}
        # By returning "fn" unmodified we can work through lists and dicts without problems
        return fn

    @staticmethod
    def compile(ctx: ExecContext, statement: Tree, source: Any, cache_size: int, param_paths: list[tuple[str]]) -> Any:
        """Construct a function from source text"""
        if source is None: return None
        if isinstance(source, str):
            # Normally we expect a string to parse
            return ArrowFunction(statement, cache_size, source, ctx.parse_expression(source), param_paths)
        if isinstance(source, (int, float, bool)):
            # These should end up being functions returning constants
            # TODO regex?
            return UserFunction.compile(ctx, statement, str(source), cache_size, param_paths) # TODO use poly_repr
        if isinstance(source, list):
            # Create a list of Arrow Functions
            return list(UserFunction.compile(ctx, statement, s1, cache_size, param_paths) for s1 in source)
        # NB: we can execute a dict as a template, but to compile it, everything
        #     would need to be either expressions as strings or constants. You COULD
        #     have string constants returned by using "ToString('const string')" but
        #     it seems like a hack, so we don't support it.
        raise TypeError(f'Cannot use {poly_type(source)!r} as the source for an Arrow Function')

class ArrowFunction(AbstractUserCallable):

    def __init__(self, statement: Tree, cache_size: int, source: str, expr: Tree, param_paths: list[tuple[str]]):
        super().__init__(statement, cache_size, param_paths)
        assert source and isinstance(source, str)
        self._source = source
        assert expr and isinstance(expr, (Tree, Token))
        self._expr = expr

    def __str__(self): return self._source

    def _evaluate(self, ctx: ExecContext) -> Any:
        return ctx.eval_expr(self._expr)
