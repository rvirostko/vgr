"""
Functor compilation and execution
"""

from typing import Any

from lark import Tree

from exec_context import ExecContext
from mathpak import type_str

class Functor:
    """
**Parameterized expressions which can be used multiple times**

Functors are compiled expressions that can take a set of arguments at runtime.
They can be dynamic and recursive.

See also *CompileFunctor()*
    """
    # For simplicity these all need to be simple names, not dotted paths
    _SELF_NAME = 'self'
    _ARG_NAMES = [ 'x', 'y', 'z', '$4', '$5', '$6', '$7', '$8', '$9', '$a', '$b', '$c', '$d', '$e', '$f']

    def __init__(self, source: str, expr: Tree):
        self._source = source
        self._expr = expr

    def __str__(self): return self._source
    def __repr__(self): return repr(self._source)

    def evaluate(self, ctx: ExecContext, args: list) -> Any:
        # Save existing values and set new ones from the args
        # As a function of zip() we end up ignoring arguments that
        # we don't have names for, or we don't set values for
        # variables we don't have values for.
        saved_values = {}
        # Handle the self reference as a special case
        saved_values[self._SELF_NAME] = ctx.get_var(self._SELF_NAME)
        ctx.set_var(self, self._SELF_NAME)
        for name, value in zip(self._ARG_NAMES, args):
            saved_values[name] = ctx.get_var(name)
            ctx.set_var(value, name)
        try:
            return ctx.eval_expr(self._expr)
        finally:
            # Restore the saved values
            for name, value in saved_values.items(): ctx.set_var(value, name)

    @staticmethod
    def compile(ctx: ExecContext, source: Any) -> Any:
        if source is None: return None
        if isinstance(source, Functor): return source # compile is idempotent
        if isinstance(source, (list, tuple)):
            return type(source)(Functor.compile(ctx, s1) for s1 in source)
        if isinstance(source, (int, float, bool)): source = str(source)
        if not isinstance(source, str): raise TypeError(f'Cannot use {type_str(source)} as the source for a functor')
        return Functor(source, ctx.parse_expression(source))

    @staticmethod
    def invoke(ctx: ExecContext, fn: Any, args: list) -> Any:
        if fn is None: return None
        if isinstance(fn, Functor): return fn.evaluate(ctx, args)
        if isinstance(fn, (list, tuple)):
            return type(fn)(Functor.invoke(ctx, f1, args) for f1 in fn)
        return Functor.invoke(ctx, Functor.compile(ctx, fn), args)
