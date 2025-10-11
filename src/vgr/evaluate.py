"""
Functions to:
    * Bind operations to an parsed expression
    * Evaluate the expression
"""

from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, Iterable
import textwrap

from lark import v_args, Tree, Token, Transformer

from .app_exceptions import VgrRuntimeError
from .data_dict import DataDictionary
from .exec_context import ExecContext
from .user_callable import UserFunction
from .functions import get_function_op, build_list, build_dict, logical_and, logical_or
from .mathpak import (
    poly_add,
    poly_bit_and,
    poly_bit_or,
    poly_bit_xor,
    poly_ceil,
    poly_contains_all,
    poly_contains_any,
    poly_div,
    poly_eq,
    poly_exact_eq,
    poly_false,
    poly_floor,
    poly_ge,
    poly_gt,
    poly_imatches,
    poly_in,
    poly_le,
    poly_lt,
    poly_matches_all,
    poly_matches,
    poly_mod,
    poly_mul,
    poly_ne,
    poly_not_imatches,
    poly_not_in,
    poly_not_matches,
    poly_pow,
    poly_repr,
    poly_shl,
    poly_shr,
    poly_sub,
    poly_true,
    type_str,
)

def shorten(s: str, width: int=64) -> str:
    """
    Limits output that can appear in debug/verbose content.
    Should be used with poly_repr(...) when you don't know the object size.
    """
    return textwrap.shorten(s, width=width, placeholder="\u2026")

def do_set(ctx: ExecContext, value: Any, *path) -> None:
    """
    After calculations are done, use this to set a value.
    Generates verbose output.
    Path should be a vetted
    """
    new_value = ctx.set_var(value, *path)
    if ctx.verbose: ctx.print_verbose('Set', '.'.join(path), 'To', shorten(repr(new_value)))

def do_unset(ctx: ExecContext, *path) -> None:
    """
    Use this to unset a value.
    Generates verbose output.
    """
    old_value = ctx.dd.unset_var(*path)
    if ctx.verbose: ctx.print_verbose('Removed', shorten(repr(old_value)), 'From', '.'.join(path))

def get_writable_var_path(ctx: ExecContext, node: Tree) -> tuple:
    """Determine the path and validate it for writability"""
    try:
        return ctx.dd.validate_user_set_path(*_var_name_path(node))
    except ValueError as e:
        raise VgrRuntimeError(node, e) from e

def create_param_list(ctx: ExecContext, node: Tree) -> tuple:
    """Create list of param paths making sure they are unique and non-overlapping and can be used as writable paths"""
    if not isinstance(node, Tree) or not node.data == 'params': return []
    param_source: Iterable = node.children
    seen_paths = set()
    param_paths = []
    # First pass: extract and check for valid and unique names
    for node in param_source:
        path = get_writable_var_path(ctx, node)
        if path in seen_paths:
            raise VgrRuntimeError(node, ValueError(f'Duplicate parameter {".".join(path)!r}'))
        seen_paths.add(path)
        param_paths.append((path, node))
    # Second pass: check for prefix overlaps
    for i, (p1, node) in enumerate(param_paths):
        for j, (p2, _) in enumerate(param_paths):
            if i != j:
                # You can't set "a.b" and "a.b.c" regardless of order
                # because you won't get expected results
                if (len(p1) < len(p2) and p2[:len(p1)] == p1 or
                    len(p2) < len(p1) and p1[:len(p2)] == p2):
                    raise VgrRuntimeError(node, ValueError(f'Parameters {".".join(p1)!r} and {".".join(p2)!r} overlap'))
    return [entry[0] for entry in param_paths]

def assert_has_meta(tree: Tree):
    """Correct error handling relies on the metadata, so we need to check correctness"""
    assert hasattr(tree, 'meta'), f"Tree node {tree.data} is missing .meta"
    meta = tree.meta
    missing = []
    for attr in ('start_pos', 'end_pos', 'line', 'column', 'end_line', 'end_column'):
        if not hasattr(meta, attr) or getattr(meta, attr) is None:
            missing.append(attr)
    assert not missing, (f"Tree node {tree.data} has incomplete meta: missing {', '.join(missing)}")

class Operation(Tree, ABC):
    """A replacement Tree node that adds a slot for execution"""

    def __init__(self, base: Tree):
        assert_has_meta(base)
        # Shallow copy of the children array
        super().__init__(base.data, base.children[:] or [])
        # Deep copy out of paranoia
        self._meta = deepcopy(base.meta)
        assert_has_meta(self)

    @abstractmethod
    def execute(self, ctx: ExecContext, args: list) -> Any:
        """Do it"""

    @abstractmethod
    def op_name(self) -> str:
        """The name"""

class SimpleOperation(Operation):
    """Instance that invokes another operation : part of an expression"""
    def __init__(self, base: Tree, op):
        super().__init__(base)
        self._op = op

    def execute(self, ctx: ExecContext, args: list) -> Any:
        # We evaluate all the arguments and execute the operation
        return self._op(*tuple(ctx.eval_expr(arg) for arg in args))

    def op_name(self) -> str:
        return self._op.__name__

class VarRef(Operation):
    """
    The children form the path to info in the data dictionary
    """

    def execute(self, ctx: ExecContext, args: list) -> Any:
        """
        This is the lookup of a top-level variable.
        args are the children of a var_ref Tree, comprising
        the path and are all NAME tokens
        """
        return ctx.get_var(*_var_name_path(self))

    def op_name(self) -> str:
        return 'var_ref'

class SetVarOperation(Operation):
    """
    Evaluate an expression, storing its value in a variable
    before returning it
    """
    def execute(self, ctx: ExecContext, args: list) -> Any:
        # <expr>.SetVar(<var_name>)
        value = ctx.eval_expr(args[0])
        var_path = get_writable_var_path(ctx, args[1])
        do_set(ctx, value, *var_path)
        return value

    def op_name(self) -> str:
        return 'set_var'

def get_function(ctx: ExecContext, statement: Tree):
    fn = ctx.get_var(*_var_name_path(statement))
    if fn is None:
        raise VgrRuntimeError(statement.children[0], ValueError('Function is not defined'))
    return fn

class InvokeFunctionOperation(Operation):
    """
    Invoke a user function stand-alone

    ```
    set adder to (a, b) -> a.DefaultTo(0) + b.DefaultTo(0)
    print @adder(1,2)
    ````
    """
    def execute(self, ctx: ExecContext, args: list) -> Any:
        # @<var-name>(<expr>...)
        fn = get_function(ctx, args[0])
        values = [ctx.eval_expr(arg) for arg in args[1:]]
        return UserFunction.invoke(ctx, fn, values)

    def op_name(self) -> str:
        return 'invoke_func'

class InvokeInlineFunctionOperation(Operation):
    """
    Invoke a user function inline

    ```
    set adder to (a, b) -> a.DefaultTo(0) + b.DefaultTo(0)
    print 1.@adder(2)
    ````
    """
    def execute(self, ctx: ExecContext, args: list) -> Any:
        # <expr>.@<var-name>(<expr>...)
        inline_value = ctx.eval_expr(args[0]) # the in-line <expr>
        fn = get_function(ctx, args[1])
        values = [ctx.eval_expr(arg) for arg in args[2:]]
        values.insert(0, inline_value)
        return UserFunction.invoke(ctx, fn, values)

    def op_name(self) -> str:
        return 'invoke_in_linefunc'

class AndOperation(Operation):

    def execute(self, ctx: ExecContext, args: list) -> Any:
        return logical_and(lambda arg: poly_true(ctx.eval_expr(arg)), args)

    def op_name(self) -> str:
        return 'and'

class OrOperation(Operation):

    def execute(self, ctx: ExecContext, args: list) -> Any:
        return logical_or(lambda arg: poly_true(ctx.eval_expr(arg)), args)

    def op_name(self) -> str:
        return 'or'

class NotOperation(Operation):

    def execute(self, ctx: ExecContext, args: list) -> Any:
        # NB: grammar defines this as taking a single arg
        return poly_false(ctx.eval_expr(args[0]))

    def op_name(self) -> str:
        return 'not'

# TODO needs to move for doc reasons...
class Ternary(Operation):
    """
    Instance that handles the implemenation of ternary expressions.
    """

    def __init__(self, base: Tree, seq: tuple):
        """
        seq : tuple of three digits
            first : the index of the predicate expression
            second : the index of the "true" expression
            third : the index of the "false" expression
        """
        super().__init__(base)
        self._seq = seq

    def execute(self, ctx: ExecContext, args: list) -> Any:
        """
        Using the sequence indicies, execute the predicate.
        Then depending upon the truth value, execute the "true" or
        "false" part and return the result.
        """
        if poly_true(ctx.eval_expr(args[self._seq[0]])):
            return ctx.eval_expr(args[self._seq[1]])
        return ctx.eval_expr(args[self._seq[2]])

    def op_name(self) -> str:
        return 'ternary' + poly_repr(self._seq)

# TODO needs to be replaced with a more sophisticated
# sig: path is a set of strings now, not the tokens
# so error messages have no context
def deref_var(data: Any, /, *path: str) -> Any:
    """
    This is the lookup of a path relative to data.
    It does NOT use a data dictionary except to
    validate the step names in the path.
    """
    for step in path:
        try:
            DataDictionary.valid_path_step(step)
            if not isinstance(data, dict) or step not in data: return None
            data = data[step]
        except ValueError as e:
            raise VgrRuntimeError(step, e) from e
    return data

def _is_name_token(node) -> bool:
    return isinstance(node, Token) and node.type == 'NAME'

def _is_var_name(node) -> bool:
    return isinstance(node, Tree) and node.data == 'var_name'

def _is_var_ref(node) -> bool:
    return isinstance(node, Tree) and node.data == 'var_ref'

def _var_name_path(node: Tree) -> tuple[str]:
    """
    Returns a path into the data dictionary, typically used with lvalues.

    * var_name tree: path from children which should be NAME tokens
    * var_ref tree: same as var_name
    * NAME token: single level path

    The path is partially validate: steps are checked, but we
    can't check for valid write because we don't know the context.

    See get_writable_var_path()
    """
    def _step_name(token: Token) -> str:
        # extracts and validates the parts of the path
        try:
            if not _is_name_token(token): raise ValueError('Expected NAME') # SNO
            return DataDictionary.valid_path_step(token.value)
        except ValueError as e:
            raise VgrRuntimeError(token, e) from e

    if _is_var_name(node) or _is_var_ref(node): return tuple(_step_name(name) for name in node.children)
    if _is_name_token(node): return (_step_name(node),)
    raise VgrRuntimeError(node, TypeError('Expected var_name, var_ref or NAME')) # SNO

def eval_expr_or_const(ctx: ExecContext, expr: Any) -> Any:
    """
    This lets values be unquoted as arguments.
    For example it allows

        Vault CreateMount secrets Type is **KV2**

    to be used interchangably with

        Vault CreateMount "secrets" Type is **"KV2"**

    If _KV2_ is not defined in the data dictionary.

    It also handles

        Vault CreateMount "secrets" Type **from KV2**

    where _KV2_ is stored as a _var_name_,
    disambiguating the previous checks.

    If none of these conditions apply, the expression is handled as a normal
    expression (see eval_expr())
    """
    if isinstance(expr, Tree):
        # var_name is typically used as a lvalue, but here the
        # syntax is an explicit "value of" rather than a constant value
        if _is_var_name(expr): return ctx.get_var(*_var_name_path(expr))
        # This allows for arguments to be unquoted if it is a simple (one part) name
        # and its value is not known in the data dictionary
        if _is_var_ref(expr) and len(expr.children) == 1 and _is_name_token(expr.children[0]):
            name = expr.children[0].value
            exists, _, value = ctx.var_exists(name)
            return value if exists else name
    # If not one of the special cases, treat this as an expression
    return ctx.eval_expr(expr)

# pylint: disable=too-many-public-methods
# disabled because we MUST have a method for each rule
# it is the way Transformer works
@v_args(tree=True)
class OperationBinder(Transformer):
    """Binds functions to expression operations"""
    # Fundemental boolean logic
    def and_op(self, tree): return AndOperation(tree)
    def or_op(self, tree): return OrOperation(tree)
    def unary_not(self, tree): return NotOperation(tree)

    # Comparisons of some type with two operands that return booleans
    def contains_op(self, tree): return SimpleOperation(tree, poly_contains_any)
    def contains_all_op(self, tree): return SimpleOperation(tree, poly_contains_all)
    def exact_eq_op(self, tree): return SimpleOperation(tree, poly_exact_eq)
    def eq_op(self, tree): return SimpleOperation(tree, poly_eq)
    def ge_op(self, tree): return SimpleOperation(tree, poly_ge)
    def gt_op(self, tree): return SimpleOperation(tree, poly_gt)
    def imatches_op(self, tree): return SimpleOperation(tree, poly_imatches)
    def in_op(self, tree): return SimpleOperation(tree, poly_in)
    def le_op(self, tree): return SimpleOperation(tree, poly_le)
    def lt_op(self, tree): return SimpleOperation(tree, poly_lt)
    def matches_op(self, tree): return SimpleOperation(tree, poly_matches)
    def matches_all_op(self, tree): return SimpleOperation(tree, poly_matches_all)
    def neq_op(self, tree): return SimpleOperation(tree, poly_ne)
    def not_imatches_op(self, tree): return SimpleOperation(tree, poly_not_imatches)
    def not_in_op(self, tree): return SimpleOperation(tree, poly_not_in)
    def not_matches_op(self, tree): return SimpleOperation(tree, poly_not_matches)

    # Polymorphic operations with two or more operands
    def add_op(self, tree): return SimpleOperation(tree, poly_add)
    def bit_and_op(self, tree): return SimpleOperation(tree, poly_bit_and)
    def bit_or_op(self, tree): return SimpleOperation(tree, poly_bit_or)
    def bit_xor_op(self, tree): return SimpleOperation(tree, poly_bit_xor)
    def div_op(self, tree): return SimpleOperation(tree, poly_div)
    def mod_op(self, tree): return SimpleOperation(tree, poly_mod)
    def mul_op(self, tree): return SimpleOperation(tree, poly_mul)
    def pow_op(self, tree): return SimpleOperation(tree, poly_pow)
    def shl_op(self, tree): return SimpleOperation(tree, poly_shl)
    def shr_op(self, tree): return SimpleOperation(tree, poly_shr)
    def sub_op(self, tree): return SimpleOperation(tree, poly_sub)

    # Polymorphic operations with a single arg
    def ceil_op(self, tree): return SimpleOperation(tree, poly_ceil)
    def floor_op(self, tree): return SimpleOperation(tree, poly_floor)

    # Ternary operations: indicies are for predicate, true-side, false-side
    def c_ternary(self, tree): return Ternary(tree, (0, 1, 2))
    def py_ternary(self, tree): return Ternary(tree, (1, 0, 2))

    # Other operations
    def array(self, tree): return SimpleOperation(tree, build_list)
    def dict(self, tree): return SimpleOperation(tree, build_dict)
    def deref(self, tree): return SimpleOperation(tree, deref_var)
    def var_ref(self, tree): return VarRef(tree)
    def set_var(self, tree): return SetVarOperation(tree)
    def invoke_func(self, tree): return InvokeFunctionOperation(tree)
    def invoke_func_inline(self, tree): return InvokeInlineFunctionOperation(tree)

    # method-style invocation: "foo".Upper()
    def dotfunction_call(self, tree):
        # The expression becomes the first argument to the function,
        # and it takes the place of the wrapper from parsing
        expr, func = tree.children
        rc = SimpleOperation(func, get_function_op(func.children.pop(0).value))
        rc.children.insert(0, expr)
        return rc

    # functional-style invocation: Upper("foo")
    def function_call(self, tree):
        func = tree.children[0]
        return SimpleOperation(func, get_function_op(func.children.pop(0).value))

# pylint: enable=too-many-public-methods

# NB: Changes to OperationBinder() may fix issues
#     with double binding of functions which means
#     this should not be a public and there's no need
#     for diferentiating "control statements" etc
#     Out of FUD, we won't be doing that now...
def bind_operations(statement: Tree) -> Tree:
    """
    Transforms an expression and binds operations to nodes for
    execution by eval_expr() or helper methods.
    """
    return OperationBinder().transform(statement)

def eval_expr(ctx: ExecContext, expr: Any) -> Any:
    """Evalutates an expression"""
    if isinstance(expr, Tree):
        if isinstance(expr, Operation):
            try:
                return expr.execute(ctx, expr.children)
            except VgrRuntimeError as e:
                raise e
            except Exception as e:
                raise VgrRuntimeError(expr, e) from e
        raise VgrRuntimeError(expr, NotImplementedError(f'Unhandled type {expr.data!r}')) #SNO
    if isinstance(expr, Token):
        # All tokens should be CONSTs so we don't want users mucking them up
        return deepcopy(expr.value)
    raise VgrRuntimeError(expr, NotImplementedError(f'Unknown type {type_str(expr)}')) #SNO
