"""
The Choose statements
"""

from collections.abc import Iterator
from typing import Any

from lark import Tree

from .builtins import (
    bound_ops,
    poly_is_between,
    poly_contains,
    poly_contains_all,
    poly_eq,
    poly_exact_eq,
    poly_false,
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
    poly_ne,
    poly_not_contains,
    poly_not_empty,
    poly_not_in,
    poly_not_match,
    poly_true,
)
from .evaluate import (
    bind_operations,
    is_var_constant,
    is_var_defined,
)

from .exec_context import ExecContext
from .tags import control_statement

@control_statement
@bound_ops("Choose")
def execute_choose(ctx: ExecContext, statement: Tree) -> None:
    """
**Choose from a set of statements based on a series of tests**

* Choose [All] [:]\\
  &emsp;&emsp;When *expression* [:] *statement*&hellip;\\
  &emsp;&emsp;Otherwise [:] *statement*&hellip;\\
  [End-Choose | End]

The values in `When` clauses are examined in order, and the first to
evaluate to `True` has its block of statements executed.

If none of the `When` clauses evaluates to `True` the `Otherwise` cause,
if provided, is selected. Note that this clause _must_ follow all the `When`
clauses, and that at least one `When` must be specified.

Both `Break` and `Continue` can be used within blocks of statements.

```vgr
Set month To time.today.month
Choose
    When month In [1, 2, 12]       Set season To "winter"
    When month ≥ 3 And month ≤ 5   Set season To "spring"
    When month ≥ 6 And month ≤ 8   Set season To "summer"
    When month ≥ 9 And month ≤ 11  Set season To "fall"
    Otherwise  Assert False: "Invalid month {}", month
End-Choose
Print "Month", month, "is a", season, "month"

For n = 1 To 15
    Choose All
        When (n % 3) == 0  Printf "Fizz"
        When (n % 5) == 0  Printf "Buzz"
        Otherwise          Printf "{}", n
    End-Choose
    Print ""
Next
```

Also see `Choose Using`
"""
    if len(statement.children):
        statement_children = iter(statement.children)
        do_all = False
        if isinstance(statement.children[0], Tree) and statement.children[0].data == 'choose_all':
            do_all = True
            next(statement_children)
        ctx.echo_source(statement, statement.children[min(1 if do_all else 0, len(statement.children) - 1)])
        _exec_choose(ctx, do_all, statement_children, None, None)
    else:
        ctx.echo_source(statement)

# Operation mapping for choose "when" comparisons
_CHOOSE_OPS = {
    'is_empty_block':     poly_is_empty,
    'is_even_block':      poly_is_even,
    'is_neg_block':       poly_is_negative,
    'is_not_empty_block': poly_not_empty,
    'is_odd_block':       poly_is_odd,
    'is_pos_block':       poly_is_positive,
    'not_range_block':    poly_false,
    'op_contains':        poly_contains,
    'op_contains_all':    poly_contains_all,
    'op_eq':              poly_eq,
    'op_ge':              poly_ge,
    'op_gt':              poly_gt,
    'op_is_in':           poly_in,
    'op_le':              poly_le,
    'op_lt':              poly_lt,
    'op_matches_all':     poly_matches_all,
    'op_matches':         poly_matches,
    'op_ne':              poly_ne,
    'op_not_contains':    poly_not_contains,
    'op_not_is_in':       poly_not_in,
    'op_not_matches':     poly_not_match,
    'op_xeq':             poly_exact_eq,
    'range_block':        poly_true,
}

# These apply only to values blocks
# Generally, operation results are "or"ed together, but if they
# appear in this list, then are "and"ed instead
_AND_OPS = [
    'op_contains_all',
    'op_matches_all',
    'op_ne',
    'op_not_contains',
    'op_not_is_in',
    'op_not_matches',
]

@control_statement
@bound_ops("Choose Using")
def execute_choose_using(ctx: ExecContext, statement: Tree) -> None:
    """
**Choose from a set of statements based on a value**

* Choose [All] Using *expression* [:]\\
  &emsp;&emsp;When [Not] Empty [:] *statement*&hellip;\\
  &emsp;&emsp;When [Not] [Defined | Undefined] [:] *statement*&hellip;\\
  &emsp;&emsp;When [Not] [Negative | Positive] [:] *statement*&hellip;\\
  &emsp;&emsp;When [Not] [Even | Odd] [:] *statement*&hellip;\\
  &emsp;&emsp;When [Not] Less Than *expression* [:] *statement*&hellip;\\
  &emsp;&emsp;When [Not] Greater Than *expression* [:] *statement*&hellip;\\
  &emsp;&emsp;When [Not] Matches *expression*[, *expression*]&hellip; [:] *statement*&hellip;\\
  &emsp;&emsp;When Matches All *expression*[, *expression*]&hellip; [:] *statement*&hellip;\\
  &emsp;&emsp;When [Not] Contains *expression*[, *expression*]&hellip; [:] *statement*&hellip;\\
  &emsp;&emsp;When Contains All *expression*[, *expression*]&hellip; [:] *statement*&hellip;\\
  &emsp;&emsp;When [Not] *expression*[, *expression*]&hellip; [:] *statement*&hellip;\\
  &emsp;&emsp;When [Not] *expression* [To | Through | Thru] *expression* [:] *statement*&hellip;\\
  &emsp;&emsp;When Is [Not] Equal To *expression*[, *expression*]&hellip; [:] *statement*&hellip;\\
  &emsp;&emsp;When Is [Not] In *expression*[, *expression*]&hellip; [:] *statement*&hellip;\\
  &emsp;&emsp;When === *expression*[, *expression*]&hellip; [:] *statement*&hellip;\\
  &emsp;&emsp;Otherwise [:] *statement*&hellip;\\
  [End-Choose | End]

The expression in the `Choose` statement is evaluated and it becomes the
*desired value* which is compared against values in `When` clauses.

The values in `When` clauses are examined in order. Matching values may
be specified as a single value, in comma separated groups, as ranges,
inequalities, or contents checks.

Testing of `When` clauses terminates after the first match _unless_ `All`
is specified.

If none of the `When` clauses match the desired value the `Otherwise` cause,
if provided, is selected. Note that this clause _must_ follow all the `When`
clauses. When `All` is specified `Otherwise` is skipped if another `When` clause has matched.

While complicated expressions can be used as the values in `When` it is recommended
that constants are used.

Note that `Defined` and `Undefined` only provide meaningful results when a
variable is used, not an expression; expressions, even if they evaluate to
`None` are considered defined.

```vgr
Set month To time.today.month
Choose Using month
    When 1, 2, 12   Set season To "winter"
    When 3, 4, 5    Set season To "spring"
    When 6, 7, 8    Set season To "summer"
    When 9, 10, 11  Set season To "fall"
    Otherwise       Assert False: "Invalid month {}", month
End-Choose
Print "Month", month, "is a", season, "month"

Choose Using user_input
    When Is None
        Print "Input required"
    When Matches "^[0-9]{5}$", "^[0-9]{5}-[0-9]{4}$"
        // ZIP with and without four digit extension
        Print "Looks like a ZIP code"
    When Matches "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$",
            "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\.[A-Za-z]{2,}$"
        // Email with and without subdomain
        Print "Looks like an email"
    When Matches "^\\+?[0-9]{10,15}$", "^[0-9]{3}-[0-9]{3}-[0-9]{4}$"
        // International digits or U.S. formatted
        Print "Looks like a phone number"
    Otherwise:
        Print "Unrecognized input"
End-Choose
```

Also see `Choose`
"""
    statement_children = iter(statement.children)
    do_all = False
    if isinstance(statement.children[0], Tree) and statement.children[0].data == 'choose_all':
        do_all = True
        next(statement_children)
    ctx.echo_source(statement, statement.children[min(2 if do_all else 1, len(statement.children) - 1)])
    # NB: Operation test may cause a TypeError if there is a mismatch
    #     betweeen the desired_value's type, which drives "casting"
    #     and the resulting type of the expression
    # The first child is the expression used in the value comparisons
    expr = bind_operations(next(statement_children, None))
    desired_value = ctx.eval_expr(expr)
    _exec_choose(ctx, do_all, statement_children, expr, desired_value)

def _exec_choose(ctx: ExecContext, do_all: bool, statement_children: Iterator, expr: Tree, desired_value: Any) -> None:
    """Internal method that handles both forms"""
    choice_made = False
    for when_block in statement_children:
        chosen_block = None
        values_children = iter(when_block.children)
        block_name = when_block.data
        # This section is for the Choose that doesn't have a desired value
        if block_name == "choice_block":
            choice_children = iter(when_block.children)
            # The first child is the expression to test
            # We do a Pythonic test for "True" here, avoiding internal conversions
            if ctx.eval_expr(bind_operations(next(choice_children, None))):
                ctx.echo_source(when_block, when_block.children[1])
                # After the expression to test the iterator
                # points to the following statements
                chosen_block = choice_children
        elif block_name in ('is_const_block', 'is_not_const_block'):
            if is_var_constant(ctx, expr) is not (block_name == 'is_not_const_block'):
                ctx.echo_source(when_block, when_block.children[0])
                chosen_block = values_children
        elif block_name in ('is_defined_block', 'is_undefined_block'):
            if is_var_defined(ctx, expr) is not (block_name == 'is_undefined_block'):
                ctx.echo_source(when_block, when_block.children[0])
                chosen_block = values_children
        # These tests don't use an expression
        elif block_name in ('is_empty_block', 'is_not_empty_block', 'is_neg_block', 'is_pos_block', 'is_even_block', 'is_odd_block'):
            test_op = _CHOOSE_OPS.get(when_block.data)
            if test_op(desired_value):
                ctx.echo_source(when_block, when_block.children[0])
                chosen_block = values_children
        elif block_name in ('values_block', 'not_values_block'):
            # If there is a node in front of our list of values
            # it is a specialized operator rather than one
            # implied by the block name
            when_end_index = 1
            if when_block.children[0].data == 'value_list':
                op_name = 'op_eq' if block_name == 'values_block' else 'op_ne'
            else:
                op_name = next(values_children).data
                when_end_index += 1
            test_op = _CHOOSE_OPS.get(op_name)
            assert test_op is not None, f"Missing binding: {op_name!r}"
            # These tests treat the comma as an "and":
            #     "when not 1, 2, 3" -> "when not 1 <and> not 2 <and> not 3"
            # All tests must pass, ending evaluation on the first failure
            if op_name in _AND_OPS:
                chosen_block = values_children
                for target_expr in next(values_children, None).children:
                    if not test_op(desired_value, ctx.eval_expr(bind_operations(target_expr))):
                        chosen_block = None
                        break
            else:
                # Otherwise, tests treat the comma as an "or":
                #     "when 1,2,3" -> "when 1 <or> 2 <or> 3"
                # The first test to pass ends evaluation and selects the block
                for target_expr in next(values_children, None).children:
                    if test_op(desired_value, ctx.eval_expr(bind_operations(target_expr))):
                        chosen_block = values_children
                        break
            if chosen_block:
                ctx.echo_source(when_block, when_block.children[when_end_index])
        elif block_name in ('range_block', 'not_range_block'):
            test_op = _CHOOSE_OPS.get(when_block.data)
            lo_value = ctx.eval_expr(bind_operations(next(values_children)))
            hi_value = ctx.eval_expr(bind_operations(next(values_children)))
            if test_op(poly_is_between(desired_value, lo_value, hi_value)):
                ctx.echo_source(when_block, when_block.children[2])
                chosen_block = values_children
        elif block_name == 'ineq_block':
            test_op = _CHOOSE_OPS.get(next(values_children).data)
            if test_op(desired_value, ctx.eval_expr(bind_operations(next(values_children)))):
                ctx.echo_source(when_block, when_block.children[2])
                chosen_block = values_children
        elif block_name == 'otherwise_block':
            # the block is automatically selected if none others have been
            if not choice_made:
                ctx.echo_source(when_block, when_block.children[0])
                chosen_block = values_children
        else:
            raise ValueError(f'{block_name} not implemented') # SNO
        # If a block of statements was chosen execute them
        if chosen_block is not None:
            choice_made = True
            ctx.dispatch_statements(chosen_block)
            # do_all can let multiple when blocks execute, but
            # when it is off, the first one chosen ends the loop
            if not do_all: break
    # end of "for when_block"
