"""
Functions to:
    * Bind operations to an parsed expression
    * Evaluate the expression
"""

from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any

from lark import v_args, Tree, Token, Transformer

from app_exceptions import VgrRuntimeError
from data_dict import DataDictionary
from functions import get_function_op, build_list, build_dict, logical_and, logical_or
from mathpak import (
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
    poly_fdiv,
    poly_floor,
    poly_ge,
    poly_gt,
    poly_imatches,
    poly_in,
    poly_int,
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
    poly_number,
    poly_pow,
    poly_shl,
    poly_shr,
    poly_sub,
    poly_true,
    type_str,
)
from output import verify_relative_path

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
    def execute(self, dd: DataDictionary, args: list) -> Any:
        """Do it"""

    @abstractmethod
    def op_name(self) -> str:
        """The name"""

class SimpleOperation(Operation):
    """Instance that invokes another operation : part of an expression"""
    def __init__(self, base: Tree, op):
        super().__init__(base)
        self._op = op

    def execute(self, dd: DataDictionary, args: list) -> Any:
        # We evaluate all the arguments and execute the operation
        return self._op(*tuple(eval_expr(dd, arg) for arg in args))

    def op_name(self) -> str:
        return self._op.__name__

class VarRef(Operation):
    """
    The children form the path to info in the data dictionary
    """

    def execute(self, dd: DataDictionary, args: list) -> Any:
        """This is the lookup of a top-level variable"""
        # The args are all NAME tokens
        return dd.get_var_user(*tuple(arg.value for arg in args))

    def op_name(self) -> str:
        return 'var_ref'

class SetVarOperation(Operation):
    """
    Evaluate an expression, storing its value in a variable
    before returning it
    """
    def execute(self, dd: DataDictionary, args: list) -> Any:
        # <expr>.SetVar(<var_name>)
        return dd.set_var_user(eval_expr(dd, args[0]), *tuple(arg.value for arg in args[1].children))

    def op_name(self) -> str:
        return 'set_var'

class AndOperation(Operation):

    def execute(self, dd: DataDictionary, args: list) -> Any:
        return logical_and(lambda arg: poly_true(eval_expr(dd, arg)), args)

    def op_name(self) -> str:
        return 'and'

class OrOperation(Operation):

    def execute(self, dd: DataDictionary, args: list) -> Any:
        return logical_or(lambda arg: poly_true(eval_expr(dd, arg)), args)

    def op_name(self) -> str:
        return 'or'

class NotOperation(Operation):

    def execute(self, dd: DataDictionary, args: list) -> Any:
        # NB: grammar defines this as taking a single arg
        return poly_false(eval_expr(dd, args[0]))

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

    def execute(self, dd: DataDictionary, args: list) -> Any:
        """
        Using the sequence indicies, execute the predicate.
        Then depending upon the truth value, execute the "true" or
        "false" part and return the result.
        """
        if poly_true(eval_expr(dd, args[self._seq[0]])):
            return eval_expr(dd, args[self._seq[1]])
        return eval_expr(dd, args[self._seq[2]])

    def op_name(self) -> str:
        return 'ternary' + repr(self._seq)

def deref_var(data: Any, /, *path: str) -> Any:
    """
    This is the lookup of a path relative to data.
    It does NOT use a data dictionary.
    """
    for key in path:
        if not isinstance(data, dict) or key not in data: return None
        data = data[key]
    return data

def var_name_path(node: Tree) -> tuple[str]:
    """
    Returns a path into the data dictionary from a parsed var_name.
    This is typically used for lvalues.
    """
    if isinstance(node, Tree) and node.data == "var_name":
        return tuple(name.value for name in node.children)
    raise VgrRuntimeError(node, TypeError('Expected var_name')) # SNO

def eval_expr_or_const(dd: DataDictionary, expr: Any) -> Any:
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
        if expr.data == "var_name":
            return dd.get_var_user(*var_name_path(expr))
        # This allows for arguments to be unquoted if it is a simple (one part) name
        # and its value is not known in the data dictionary
        if expr.data == "var_ref" and len(expr.children) == 1 and isinstance(expr.children[0], Token) and expr.children[0].type == "NAME":
            name = expr.children[0].value
            exists, value = dd.exists(name)
            return value if exists else name
    # If not one of the special cases, treat this as an expression
    return eval_expr(dd, expr)

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
    def fdiv_op(self, tree): return SimpleOperation(tree, poly_fdiv)
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
    def function(self, tree): return SimpleOperation(tree, get_function_op(tree.children.pop(0).value))
    def var_ref(self, tree): return VarRef(tree)
    def set_var(self, tree): return SetVarOperation(tree)
    def function_call(self, tree):
        # The expression becomes the first argument to the function,
        # and it takes the place of the wrapper from parsing
        expr, func = tree.children
        func.children.insert(0, expr)
        return func
# pylint: enable=too-many-public-methods

def bind_operations(statement: Tree) -> Tree:
    """
    Transforms an expression and binds operations to nodes for
    execution by eval_expr() or helper methods.
    """
    return OperationBinder().transform(statement)

def eval_expr(dd: DataDictionary, expr: Any) -> Any:
    """Evalutates an expression"""
    if isinstance(expr, Tree):
        if isinstance(expr, Operation):
            try:
                return expr.execute(dd, expr.children)
            except VgrRuntimeError as e:
                raise e
            except Exception as e:
                raise VgrRuntimeError(expr, e) from e
        raise VgrRuntimeError(expr, NotImplementedError(f'Unhandled type {repr(expr.data)}')) #SNO
    if isinstance(expr, Token):
        # All tokens should be CONSTs so we don't want users mucking them up
        return deepcopy(expr.value)
    raise VgrRuntimeError(expr, NotImplementedError(f'Unknown type {type_str(expr)}')) #SNO

def eval_to_str(dd: DataDictionary, expr: Tree, name: str, allow_none: bool=False) -> str:
    """Helper that makes sure you got a string back from an expression"""
    rc = eval_expr(dd, expr)
    if rc is None and allow_none: return None
    if not isinstance(rc, str):
        raise VgrRuntimeError(expr, TypeError(f'{name} must be a string; found {type_str(rc)}'))
    return rc

def eval_to_int(dd: DataDictionary, expr: Tree, name: str, allow_none: bool=False) -> int:
    rc = eval_expr(dd, expr)
    if rc is None and allow_none: return None
    if not isinstance(rc, (bool, int, float, str)):
        raise VgrRuntimeError(expr, TypeError(f'{name} must be an integer; found {type_str(rc)}'))
    return poly_int(rc)

def eval_to_number(dd: DataDictionary, expr: Tree, name: str, allow_none: bool=False):
    rc = eval_expr(dd, expr)
    if rc is None and allow_none: return None
    if isinstance(rc, bool): return int(rc)
    if isinstance(rc, (int, float)): return rc
    if isinstance(rc, str): return poly_number(rc)
    raise VgrRuntimeError(expr, TypeError(f'{name} must be an integer; found {type_str(rc)}'))

def eval_to_bool(dd: DataDictionary, expr: Tree, name: str, allow_none: bool=False) -> bool:
    rc = eval_expr(dd, expr)
    if rc is None and allow_none: return None
    if not isinstance(rc, (bool, int, float, str)):
        raise VgrRuntimeError(expr, TypeError(f'{name} must be an boolean; found {type_str(rc)}'))
    return poly_true(rc)

def eval_filename_expr(dd: DataDictionary, expr: Tree, allow_none: bool=False) -> str:
    """Helper that gets a string that should be a relative filename"""
    return verify_relative_path(eval_to_str(dd, expr, 'File name', allow_none))
