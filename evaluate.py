from typing import Any

from lark import v_args, Tree, Token, Transformer

from mathpak import poly_add, poly_bit_and, poly_bit_or, poly_bit_xor, poly_div, poly_contains
from mathpak import poly_eq, poly_pow, poly_fdiv, poly_ge, poly_imatch, poly_gt
from mathpak import poly_in, poly_le, poly_lt, poly_match, poly_mod, poly_mul
from mathpak import poly_ne, poly_not_contains, poly_not_imatch, poly_not_in
from mathpak import poly_not_match, poly_or, poly_shl, poly_shr, poly_sub, poly_not
from mathpak import poly_bool, poly_int
from functions import get_function_op
from data_dict import DataDictionary
from output import verify_relative_path

class Operation(Tree):
    """Instance that invokes another operation : part of an expression"""
    def __init__(self, base: Tree, op):
        super().__init__(base.data, base.children or [])
        self._op = op

    def execute(self, args: tuple) -> Any:
        return self._op(*args)

    def op_name(self) -> str:
        return self._op.__name__ if self._op else 'None'

class VarRef(Tree):
    """
    Instance that gets a variable from a DataDictionary
    using a path from the root.
    Part of an expression.
    """
    def __init__(self, base: Tree):
        super().__init__(base.data, base.children or [])

    def execute(self, dd: DataDictionary, args: tuple) -> Any:
        """This is the lookup of a top-level variable"""
        return dd.get_var_user(*args)

    def op_name(self) -> str:
        return 'var_ref'

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
    def add_op(self, tree): return Operation(tree, poly_add)
    def array(self, tree): return Operation(tree, build_array)
    def bit_and_op(self, tree): return Operation(tree, poly_bit_and)
    def bit_or_op(self, tree): return Operation(tree, poly_bit_or)
    def bit_xor_op(self, tree): return Operation(tree, poly_bit_xor)
    def contains_op(self, tree): return Operation(tree, poly_contains)
    def deref(self, tree): return Operation(tree, deref_var)
    def div_op(self, tree): return Operation(tree, poly_div)
    def eq_op(self, tree): return Operation(tree, poly_eq)
    def pow_op(self, tree): return Operation(tree, poly_pow)
    def fdiv_op(self, tree): return Operation(tree, poly_fdiv)
    def function(self, tree): return Operation(tree, get_function_op(tree.children.pop(0).value))
    def ge_op(self, tree): return Operation(tree, poly_ge)
    def gt_op(self, tree): return Operation(tree, poly_gt)
    def imatch_op(self, tree): return Operation(tree, poly_imatch)
    def in_op(self, tree): return Operation(tree, poly_in)
    def le_op(self, tree): return Operation(tree, poly_le)
    def lt_op(self, tree): return Operation(tree, poly_lt)
    def match_op(self, tree): return Operation(tree, poly_match)
    def mod_op(self, tree): return Operation(tree, poly_mod)
    def mul_op(self, tree): return Operation(tree, poly_mul)
    def neq_op(self, tree): return Operation(tree, poly_ne)
    def not_contains_op(self, tree): return Operation(tree, poly_not_contains)
    def not_imatch_op(self, tree): return Operation(tree, poly_not_imatch)
    def not_in_op(self, tree): return Operation(tree, poly_not_in)
    def not_match_op(self, tree): return Operation(tree, poly_not_match)
    def or_op(self, tree): return Operation(tree, poly_or)
    def shl_op(self, tree): return Operation(tree, poly_shl)
    def shr_op(self, tree): return Operation(tree, poly_shr)
    def sub_op(self, tree): return Operation(tree, poly_sub)
    def unary_not(self, tree): return Operation(tree, poly_not)
    def var_ref(self, tree): return VarRef(tree)
    def function_call(self, tree):
        # The expression becomes the first argument to the function,
        # and it takes the place of the wrapper from parsing
        expr, func = tree.children
        func.children.insert(0, expr)
        return func
# pylint: enable=too-many-public-methods

def bind_operations(statement: Tree) -> Tree:
    return OperationBinder().transform(statement)

def eval_expr(dd: DataDictionary, expr: Any) -> Any:
    """Evalutates an expression"""
    if isinstance(expr, Tree):
        if isinstance(expr, VarRef):
            return expr.execute(dd, tuple(eval_expr(dd, arg_exp) for arg_exp in expr.children))
        if isinstance(expr, Operation):
            return expr.execute(tuple(eval_expr(dd, arg_exp) for arg_exp in expr.children))
        # TODO "arrays not working?"
        raise NotImplementedError(f'Unhandled type {repr(expr.data)}')
    if isinstance(expr, Token): return expr.value
    raise NotImplementedError(f'Unknown type {repr(expr.type())}')

def eval_to_str(dd: DataDictionary, expr: Tree, name: str, allow_none: bool=False) -> str:
    """Helper that makes sure you got a string back from an expression"""
    rc = eval_expr(dd, expr)
    if rc is None and allow_none: return None
    if not isinstance(rc, str): raise TypeError(f'{name} must be a string; found {type(rc).__name__}')
    return rc

def eval_to_int(dd: DataDictionary, expr: Tree, name: str, allow_none: bool=False) -> int:
    rc = eval_expr(dd, expr)
    if rc is None and allow_none: return None
    if not isinstance(rc, (int, float, str)): raise TypeError(f'{name} must be an integer; found {type(rc).__name__}')
    return poly_int(rc)

def eval_to_bool(dd: DataDictionary, expr: Tree, name: str, allow_none: bool=False) -> bool:
    rc = eval_expr(dd, expr)
    if rc is None and allow_none: return None
    if not isinstance(rc, (int, float, bool, str)): raise TypeError(f'{name} must be an boolean; found {type(rc).__name__}')
    return poly_bool(rc)

def eval_filename_expr(dd: DataDictionary, expr: Tree, allow_none: bool=False) -> str:
    """Helper that gets a string that should be a relative filename"""
    return verify_relative_path(eval_to_str(dd, expr, 'File name', allow_none))

def eval_to_list_str(dd: DataDictionary, clause: Tree, name: str) -> str:
    return [eval_to_str(dd, expr, name) for expr in clause.children]
