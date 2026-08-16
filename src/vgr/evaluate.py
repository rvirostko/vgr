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
from .functions import get_function_op
from .builtins import (
    bound_ops,
    build_dict,
    build_list,
    get_requires_exec_context,
    poly_add,
    poly_bit_and,
    poly_bit_or,
    poly_bit_xor,
    poly_ceil,
    poly_contains_all,
    poly_contains,
    poly_div,
    poly_eq,
    poly_exact_eq,
    poly_is_false,
    poly_floor,
    poly_ge,
    poly_gt,
    poly_in,
    poly_is_empty,
    poly_is_even,
    poly_is_negative,
    poly_is_odd,
    poly_is_positive,
    poly_le,
    poly_lt,
    poly_matches_all,
    poly_matches,
    poly_mod,
    poly_mul,
    poly_ne,
    poly_not_contains,
    poly_not_empty,
    poly_not_in,
    poly_not_match,
    poly_pow,
    poly_repr,
    poly_shl,
    poly_shr,
    poly_sub,
    poly_subscript,
    poly_is_true,
    poly_type,
    poly_shorten,
)

def do_set(ctx: ExecContext, value: Any, *path) -> None:
    """
    After calculations are done, use this to set a value.
    Generates verbose output.
    Path should be a vetted
    """
    new_value = ctx.set_var(value, *path)
    if ctx.verbose: ctx.print_verbose('Set', '.'.join(path), 'To', poly_shorten(repr(new_value)))

def do_unset(ctx: ExecContext, *path) -> None:
    """
    Use this to unset a value.
    Generates verbose output.
    """
    old_value = ctx.dd.unset_var(*path)
    if ctx.verbose: ctx.print_verbose('Removed', poly_shorten(repr(old_value)), 'From', '.'.join(path))

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

    __slots__ = ("_meta",)

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

    __slots__ = ("_op", "_requires_ctx")

    def __init__(self, base: Tree, op):
        super().__init__(base)
        self._op = op
        self._requires_ctx = get_requires_exec_context(op)

    def execute(self, ctx: ExecContext, args: list) -> Any:
        # We evaluate all the arguments and execute the operation
        positional_args = tuple(ctx.eval_expr(arg) for arg in args)
        # Pass in the context if required, but as a kwargs value
        return self._op(*positional_args, ctx=ctx) if self._requires_ctx else self._op(*positional_args)

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

# Reserved: not working in the grammar
#class AssignmentExpr(Operation):
#    """
#    Perform an in-line assignment, returning the
#    calculated value
#
#    * (*variable* := *expression*)
#
#    Note that the parenthesises are required.
#    """
#
#    def execute(self, ctx: ExecContext, args: list) -> Any:
#        path = get_writable_var_path(ctx, self.children[0])
#        value = ctx.eval_expr(self.children[1])
#        do_set(ctx, value, *path)
#        return value

#    def op_name(self) -> str:
#        return 'assignment_expr'

def get_function(ctx: ExecContext, statement: Tree):
    fn = ctx.get_var(*_var_name_path(statement))
    if fn is None:
        raise VgrRuntimeError(statement, ValueError('Function is not defined'))
    return fn

class InvokeFunctionOperation(Operation):
    """
    Invoke a user function stand-alone

    ```
    Function adder to (a, b) -> a.DefaultTo(0) + b.DefaultTo(0)
    Print @adder(1,2)
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

    ```vgr
    Function adder(a, b) -> a.DefaultTo(0) + b.DefaultTo(0)
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

class Subscript(Operation):
    """
    Dereference a value using a subscript or key value
    """
    def execute(self, ctx: ExecContext, args: list) -> Any:
        # <expr>[<expr>]...
        value = ctx.eval_expr(args[0]) # the in-line <expr>
        for arg in args[1:]:
            value = poly_subscript(value, ctx.eval_expr(arg))
        return value

    def op_name(self) -> str:
        return 'subscript'

def is_var_constant(ctx: ExecContext, expr: Tree) -> bool:
    # Actual constants (string, ints, None, inf, etc) are constants
    if _is_constant(expr): return True
    # References to a variable might be constants
    # Critically, they have to exist
    return _is_var_ref(expr) and (expr.children[0] in ctx.dd.immutable_prefixes) and ctx.var_exists(*_var_name_path(expr))[0]


class IsVarConstant(Operation):
    @bound_ops("Is Constant")
    def execute(self, ctx: ExecContext, args: list) -> Any:
        """
**Check to see if a variable is a constant**

* *x* Is Constant

** TODO
Also See `Is Not Constant`
"""
        expr = args[0]
        ctx.eval_expr(expr) # evaluated for side effects
        return is_var_constant(ctx, expr)

    def op_name(self) -> str:
        return 'is_constant'

class IsVarNotConstant(Operation):
    @bound_ops("Is Not Constant")
    def execute(self, ctx: ExecContext, args: list) -> Any:
        """
**Check to see if a variable is constant**

* *x* Is Not Constant

** TODO
Also See `Is Constant`
"""
        expr = args[0]
        ctx.eval_expr(expr) # evaluated for side effects
        return not is_var_constant(ctx, expr)

    def op_name(self) -> str:
        return 'is_not_constant'

def is_var_defined(ctx: ExecContext, expr: Tree) -> bool:
    # non-var references are defined (expr or constant)
    if not _is_var_ref(expr): return True
    return ctx.var_exists(*_var_name_path(expr))[0]

class IsVarDefined(Operation):
    @bound_ops("Is Defined", "Is Not Undefined")
    def execute(self, ctx: ExecContext, args: list) -> Any:
        """
**Check to see if a variable is defined**

* *x* Is Defined
* *x* Is Not Undefined

** TODO
Also See `Is Undefined`
"""
        expr = args[0]
        ctx.eval_expr(expr) # evaluated for side effects
        return is_var_defined(ctx, expr)

    def op_name(self) -> str:
        return 'is_defined'

class IsVarUndefined(Operation):
    @bound_ops("Is Undefined", "Is Not Defined")
    def execute(self, ctx: ExecContext, args: list) -> Any:
        """
**Check to see if a variable is undefined**

* *x* Is Undefined
* *x* Is Not Defined

** TODO
Also See `Is Defined`
"""
        expr = args[0]
        ctx.eval_expr(expr) # evaluated for side effects
        return not is_var_defined(ctx, expr)

    def op_name(self) -> str:
        return 'is_undefined'

class AndOperation(Operation):

    @bound_ops("And", "&&", "∧")
    def execute(self, ctx: ExecContext, args: list) -> Any:
        """
**Logical And operation**

* *x* && *y*
* *x* And *y*
* *x* ∧ *y*

The values for *x* and *y* are evaluated as booleans.
A full `And` expression can contain more than two operands.

***Optimized Evaluation : Short-Circuit Behavior***

The logical AND operation uses short-circuit evaluation:
Evaluation of operands ends after the first `False` result is
encountered.

* *x* is evaluated first and tested using `IsTrue()`
* If the result is `False`, `False` is returned and *y* is not evaluated
* If the result is `True`, *y* is evaluated and its value determines the result

Expressions that call functions and have side effects beyond a returned
value may produce unexpected results because of this behavior.

```vgr
# None is always False
None && True → False

# Numbers: zero is False, non-zero is True
0 && True → False
0.0 && True → False
1 && True → True
-3 && True → True
2.5 && True → True

# All strings are True
"" && True → True
"false" && True → True

# Lists and dictionaries are True
[] && True → True
{} && True → True
```

```vgr
Set gcounter To Zero
Define Function gcount()
    Add 1 to gcounter
    Return IsZero(gcounter % 2)
End-Function

Print @gcount() && @gcount() && @gcount()
False
Print gcounter
1
```

Also see `And` and `IsTrue()`

"""
        for arg in args:
            # Short circuit, ending evaluation after first False
            if not poly_is_true(ctx.eval_expr(arg)): return False
        return True

    def op_name(self) -> str:
        return 'and'

class OrOperation(Operation):

    @bound_ops("Or", "||", "∨")
    def execute(self, ctx: ExecContext, args: list) -> Any:
        """
**Logical Or operation**

* *x* || *y*
* *x* Or *y*
* *x* ∨ *y*

The values for *x* and *y* are expressions evaluated to booleans.
A full `Or` expression can contain more than two operands.

***Optimized Evaluation : Short-Circuit Behavior***

The logical OR operation uses short-circuit evaluation:
Evaluation of operands ends after the first `True` result is
encountered.

* *x* is evaluated first and tested using `IsTrue()`
* If the result is `True`, `True` is returned and *y* is not evaluated
* If the result is `False`, *y* is evaluated and its value determines the result

Expressions that call functions and have side effects beyond a returned
value may produce unexpected results because of this behavior.

```vgr
# None is always False
None Or True → True
None Or False → False

# Non-zero numbers are True
0 || False → False
0 || True → True
0.0 || False → False
0.0 || True → True

# All strings are True
"" || False → True
"true" || False → True
" false " || False → True

# Lists and dictionaries are True
[] || False → True
{} || False → True
```

```vgr
Set gcounter To Zero
Define Function gcount()
    Add 1 to gcounter
    Return IsZero(gcounter % 2)
End-Function

Print @gcount() || @gcount() || @gcount()
True
Print gcounter
2
```

Also see `And` and `IsTrue()`
"""
        for arg in args:
            # Short circuit, ending evaluation after first True
            if poly_is_true(ctx.eval_expr(arg)): return True
        return False

    def op_name(self) -> str:
        return 'or'

class NotOperation(Operation):

    def execute(self, ctx: ExecContext, args: list) -> Any:
        # NB: grammar defines this as taking a single arg
        return poly_is_false(ctx.eval_expr(args[0]))

    def op_name(self) -> str:
        return 'not'

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
        if poly_is_true(ctx.eval_expr(args[self._seq[0]])):
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

def _is_constant(node) -> bool:
    return isinstance(node, Token) and node.type == 'CONST'

def _var_name_path(node: Tree) -> tuple[str]:
    """
    Returns a path into the data dictionary, typically used with lvalues.

    * var_name tree: path from children which should be NAME tokens
    * var_ref tree: same as var_name
    * NAME token: single level path

    The path is partially validated: steps are checked, but we
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
    def contains_op(self, tree): return SimpleOperation(tree, poly_contains)
    def not_contains_op(self, tree): return SimpleOperation(tree, poly_not_contains)
    def contains_all_op(self, tree): return SimpleOperation(tree, poly_contains_all)
    def exact_eq_op(self, tree): return SimpleOperation(tree, poly_exact_eq)
    def eq_op(self, tree): return SimpleOperation(tree, poly_eq)
    def ge_op(self, tree): return SimpleOperation(tree, poly_ge)
    def gt_op(self, tree): return SimpleOperation(tree, poly_gt)
    def in_op(self, tree): return SimpleOperation(tree, poly_in)
    def le_op(self, tree): return SimpleOperation(tree, poly_le)
    def lt_op(self, tree): return SimpleOperation(tree, poly_lt)
    def matches_op(self, tree):
        child = tree.children[1]
        if isinstance(child, Tree) and child.data == 'op_matches':
            del tree.children[1]
        return SimpleOperation(tree, poly_matches)
    def matches_all_op(self, tree):
        child = tree.children[1]
        if isinstance(child, Tree) and child.data == 'op_matches_all':
            del tree.children[1]
        return SimpleOperation(tree, poly_matches_all)
    def neq_op(self, tree): return SimpleOperation(tree, poly_ne)
    def not_in_op(self, tree): return SimpleOperation(tree, poly_not_in)
    def not_matches_op(self, tree):
        child = tree.children[1]
        if isinstance(child, Tree) and child.data == 'op_not_matches':
            del tree.children[1]
        return SimpleOperation(tree, poly_not_match)

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
    def is_negative_op(self, tree): return SimpleOperation(tree, poly_is_negative)
    def is_positive_op(self, tree): return SimpleOperation(tree, poly_is_positive)
    def is_even_op(self, tree): return SimpleOperation(tree, poly_is_even)
    def is_odd_op(self, tree): return SimpleOperation(tree, poly_is_odd)
    def is_defined_op(self, tree): return IsVarDefined(tree)
    def is_undefined_op(self, tree): return IsVarUndefined(tree)
    def is_const_op(self, tree): return IsVarConstant(tree)
    def is_not_const_op(self, tree): return IsVarNotConstant(tree)
    def is_empty_op(self, tree): return SimpleOperation(tree, poly_is_empty)
    def is_not_empty_op(self, tree): return SimpleOperation(tree, poly_not_empty)

    # Ternary operations: indicies are for predicate, true-side, false-side
    def c_ternary(self, tree): return Ternary(tree, (0, 1, 2))

    # Other operations
    def array(self, tree): return SimpleOperation(tree, build_list)
    def dict(self, tree): return SimpleOperation(tree, build_dict)
    def deref(self, tree): return SimpleOperation(tree, deref_var)
    def var_ref(self, tree): return VarRef(tree)
    #def assignment_expr(self, tree): return AssignmentExpr(tree)
    def invoke_func(self, tree): return InvokeFunctionOperation(tree)
    def invoke_func_inline(self, tree): return InvokeInlineFunctionOperation(tree)
    def subscript(self, tree): return Subscript(tree)

    # Transformational pipeline style: "foo".Upper()
    def dotfunction_call(self, tree):
        # The expression becomes the first argument to the function,
        # and it takes the place of the wrapper from parsing
        expr, func = tree.children
        rc = SimpleOperation(func, get_function_op(func.children.pop(0).value))
        rc.children.insert(0, expr)
        return rc

    # Functional-style: Upper("foo")
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
    raise VgrRuntimeError(expr, NotImplementedError(f'Unknown type {poly_type(expr)!r}')) #SNO
