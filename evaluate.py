"""
Functions to:
    * Bind operations to an parsed expression
    * Evaluate the expression
"""

from abc import ABC, abstractmethod
import copy
from typing import Any

from lark import v_args, Tree, Token, Transformer

from data_dict import DataDictionary
from functions import get_function_op
from mathpak import poly_vadd, poly_vbit_and, poly_vbit_xor, poly_vdiv
from mathpak import poly_bool, poly_int, poly_vbit_or
from mathpak import poly_eq, poly_vpow, poly_vfdiv, poly_ge, poly_imatches, poly_gt
from mathpak import poly_in, poly_le, poly_lt, poly_matches, poly_vmod, poly_vmul
from mathpak import poly_ne, poly_not_imatches, poly_not_in
from mathpak import poly_not_matches, poly_matches_all, poly_vshl, poly_vshr, poly_vsub, poly_not
from mathpak import poly_contains_all, poly_contains_any, type_str
from output import verify_relative_path

class Operation(Tree, ABC):

    def __init__(self, base: Tree):
        super().__init__(base.data, base.children or [])

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

class StashOperation(Operation):
    """
    Evaluate an expression, storing its value in a variable
    before returning it
    """
    def execute(self, dd: DataDictionary, args: list) -> Any:
        # <expr>.Stash(<var_name>)
        value = eval_expr(dd, args[0])
        v2 = copy.deepcopy(value) if isinstance(value, (list, dict)) else value
        dd.set_var_user(v2, *tuple(arg.value for arg in args[1].children))
        return value

    def op_name(self) -> str:
        return 'stash'

class AndOperation(Operation):
    """A short-circuiting And"""

    def execute(self, dd: DataDictionary, args: list) -> Any:
        """Return False on the first expression that evaluates to False"""
        for arg in args:
            if not poly_bool(eval_expr(dd, arg)):
                return False
        return True

    def op_name(self) -> str:
        return 'and'

class OrOperation(Operation):
    """A short-circuiting Or"""

    def execute(self, dd: DataDictionary, args: list) -> Any:
        """Return True on the first expression that evaluates to True"""
        for arg in args:
            if poly_bool(eval_expr(dd, arg)):
                return True
        return False

    def op_name(self) -> str:
        return 'or'

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
        if poly_bool(eval_expr(dd, args[self._seq[0]])):
            return eval_expr(dd, args[self._seq[1]])
        return eval_expr(dd, args[self._seq[2]])

    def op_name(self) -> str:
        return 'ternary' + repr(self._seq)

def build_array(*values: Any) -> list[Any]:
    """Builds an array from the collected values"""
    return None if values is None else list(values)

def deref_var(data: Any, /, *path: str) -> Any:
    """
    This is the lookup of a path relative to data.
    It does NOT use a data dictionary.
    """
    for key in path:
        if not isinstance(data, dict) or key not in data: return None
        data = data[key]
    return data

# pylint: disable=too-many-public-methods
# disabled because we MUST have a method for each rule
# it is the way Transformer works
@v_args(tree=True)
class OperationBinder(Transformer):
    """Binds functions to expression operations"""
    # Fundemental boolean logic
    def and_op(self, tree): return AndOperation(tree)
    def or_op(self, tree): return OrOperation(tree)
    def unary_not(self, tree): return SimpleOperation(tree, poly_not)

    # Comparisons of some type with two operands that return booleans
    def contains_op(self, tree): return SimpleOperation(tree, poly_contains_any)
    def contains_all_op(self, tree): return SimpleOperation(tree, poly_contains_all)
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
    def add_op(self, tree): return SimpleOperation(tree, poly_vadd)
    def bit_and_op(self, tree): return SimpleOperation(tree, poly_vbit_and)
    def bit_or_op(self, tree): return SimpleOperation(tree, poly_vbit_or)
    def bit_xor_op(self, tree): return SimpleOperation(tree, poly_vbit_xor)
    def div_op(self, tree): return SimpleOperation(tree, poly_vdiv)
    def fdiv_op(self, tree): return SimpleOperation(tree, poly_vfdiv)
    def mod_op(self, tree): return SimpleOperation(tree, poly_vmod)
    def mul_op(self, tree): return SimpleOperation(tree, poly_vmul)
    def pow_op(self, tree): return SimpleOperation(tree, poly_vpow)
    def shl_op(self, tree): return SimpleOperation(tree, poly_vshl)
    def shr_op(self, tree): return SimpleOperation(tree, poly_vshr)
    def sub_op(self, tree): return SimpleOperation(tree, poly_vsub)

    # Ternary operations: indicies are for predicate, true-sise, false-side
    def c_ternary(self, tree): return Ternary(tree, (0, 1, 2))
    def py_ternary(self, tree): return Ternary(tree, (1, 0, 2))

    # Other operations
    def array(self, tree): return SimpleOperation(tree, build_array)
    def deref(self, tree): return SimpleOperation(tree, deref_var)
    def function(self, tree): return SimpleOperation(tree, get_function_op(tree.children.pop(0).value))
    def var_ref(self, tree): return VarRef(tree)
    def stash(self, tree): return StashOperation(tree)
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
            return expr.execute(dd, expr.children)
        raise NotImplementedError(f'Unhandled type {repr(expr.data)}') #SNO
    if isinstance(expr, Token): return expr.value
    raise NotImplementedError(f'Unknown type {type_str(expr)}') #SNO

def eval_to_str(dd: DataDictionary, expr: Tree, name: str, allow_none: bool=False) -> str:
    """Helper that makes sure you got a string back from an expression"""
    rc = eval_expr(dd, expr)
    if rc is None and allow_none: return None
    if not isinstance(rc, str): raise TypeError(f'{name} must be a string; found {type_str(rc)}')
    return rc

def eval_to_int(dd: DataDictionary, expr: Tree, name: str, allow_none: bool=False) -> int:
    rc = eval_expr(dd, expr)
    if rc is None and allow_none: return None
    if not isinstance(rc, (int, float, str)):
        raise TypeError(f'{name} must be an integer; found {type_str(rc)}')
    return poly_int(rc)

def eval_to_bool(dd: DataDictionary, expr: Tree, name: str, allow_none: bool=False) -> bool:
    rc = eval_expr(dd, expr)
    if rc is None and allow_none: return None
    if not isinstance(rc, (int, float, bool, str)):
        raise TypeError(f'{name} must be an boolean; found {type_str(rc)}')
    return poly_bool(rc)

def eval_filename_expr(dd: DataDictionary, expr: Tree, allow_none: bool=False) -> str:
    """Helper that gets a string that should be a relative filename"""
    return verify_relative_path(eval_to_str(dd, expr, 'File name', allow_none))

def eval_to_list_str(dd: DataDictionary, clause: Tree, name: str) -> list[str]:
    """Helper that returns a list of strings. No 'None's are allowed."""
    return [eval_to_str(dd, expr, name) for expr in clause.children]
