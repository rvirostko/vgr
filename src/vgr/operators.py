from functools import lru_cache
from typing import Any, Callable

from .evaluate import AndOperation, OrOperation

from .builtins import (
    build_dict,
    build_list,
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
    poly_iseven,
    poly_isnegative,
    poly_isodd,
    poly_ispositive,
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
    poly_shl,
    poly_shr,
    poly_sub,
)

# Needs to include all items bound to operators
_OP_FUNCS: list[Callable[..., Any]] = [
    poly_false, # ! (not) TODO is this really used?!?
    build_dict, # dict
    build_list, # array
    AndOperation.execute, # and_op
    OrOperation.execute, # or_op
    poly_add, # add_op
    poly_bit_and, # bit_and_op
    poly_bit_or, # bit_or_op
    poly_bit_xor, # bit_xor_op
    poly_ceil, # poly_ceil_op
    poly_contains_all, # contains_all_op
    poly_contains_any, # contains_op
    poly_div, # div_op
    poly_eq, # eq_op
    poly_exact_eq, # exact_eq_op
    poly_floor, # poly_floor_op
    poly_ge, # ge_op
    poly_gt, # gt_op
    poly_imatches, # imatches_op
    poly_in, # in_op
    poly_iseven, # is_even_op
    poly_isnegative, # is_negative_op
    poly_isodd, # is_odd_op
    poly_ispositive, # is_positive_op
    poly_le, # le_op
    poly_lt, # lt_op
    poly_matches_all, # matches_all_op
    poly_matches, # matches_op
    poly_mod, # mod_op
    poly_mul, # mul_op
    poly_ne, # neq_op
    poly_not_imatches, # not_imatches_op
    poly_not_in, # not_in_op
    poly_not_matches, # not_matches_op
    poly_pow, # pow_op
    poly_shl, # shl_op
    poly_shr, # shr_op
    poly_sub, # sub_op
    # TODO doc shim for c_ternary...
    # def c_ternary(self, tree): return Ternary(tree, (0, 1, 2))
    # def py_ternary(self, tree): return Ternary(tree, (1, 0, 2))
]

@lru_cache
def get_operator_entries() -> dict[str, tuple]:
    entries = {}
    for func in _OP_FUNCS:
        # See builtins/common for the bound_ops decorator
        if hasattr(func, 'bound_ops'):
            for op in func.bound_ops:
                entries[op] = (func, op.lower().replace(' ', ''), (func.__doc__ or '').lower())
    return entries
