"""
The Choose statements
"""

from typing import Any

from lark import Tree

from .builtins import (
    bound_ops,
    poly_contains_any,
    poly_eq,
    poly_false,
    poly_ge,
    poly_gt,
    poly_isempty,
    poly_iseven,
    poly_isnegative,
    poly_isodd,
    poly_ispositive,
    poly_le,
    poly_lt,
    poly_matches,
    poly_matches_all,
    poly_ne,
    poly_not_match,
    poly_notempty,
    poly_true,
)
from .evaluate import bind_operations
from .exec_context import ExecContext
from .tags import control_statement

@control_statement
@bound_ops("Choose")
def execute_choose(ctx: ExecContext, statement: Tree) -> None:
    """
**Choose from a set of statements based on a series of tests**

* Choose [All]:\\
  &emsp;&emsp;When *expression* : *statement*&hellip;\\
  &emsp;&emsp;Otherwise : *statement*&hellip;\\
  [End-Choose | End] [;]

The values in `When` clauses are examined in order, and the first to
evaluate to `True` has its block of statements executed.

If none of the `When` clauses evaluates to `True` the `Otherwise` cause,
if provided, is selected. Note that this clause _must_ follow all the `When`
clauses, and that at least one `When` must be specified.

Both `Break` and `Continue` can be used within blocks of statements.

```vgr
Set month To time.today.month
Choose :
    When month In [1, 2, 12]:      Set season To "winter"
    When month ≥ 3 And month ≤ 5:  Set season To "spring"
    When month ≥ 6 And month ≤ 8:  Set season To "summer"
    When month ≥ 9 And month ≤ 11: Set season To "fall"
    Otherwise: Assert False: "Invalid month {}", month
End-Choose
Print "Month", month, "is a", season, "month"

For n = 1 To 15
    Choose All:
        When (n % 3) == 0: Printf "Fizz"
        When (n % 5) == 0: Printf "Buzz"
        Otherwise:         Printf "{}", n
    End-Choose
    Print ""
Next
```

Also see `Choose Using`
"""
    statement_children = iter(statement.children)
    do_all = False
    if isinstance(statement.children[0], Tree) and statement.children[0].data == 'choose_all':
        do_all = True
        next(statement_children)
    ctx.echo_source(statement, statement.children[1 if do_all else 0])
    _exec_choose(ctx, do_all, statement_children)

# Operation mapping for choose "when" comparisons
_CHOOSE_OPS = {
    # top-level block names
    'is_empty_block':     poly_isempty,
    'is_even_block':      poly_iseven,
    'is_neg_block':       poly_isnegative,
    'is_not_empty_block': poly_notempty,
    'is_odd_block':       poly_isodd,
    'is_pos_block':       poly_ispositive,
    'not_range_block':    poly_false,
    'not_values_block':   poly_ne,
    'range_block':        poly_true,
    'values_block':       poly_eq,
    # Found in ineq_block
    'op_ge':              poly_ge,
    'op_gt':              poly_gt,
    'op_le':              poly_le,
    'op_lt':              poly_lt,
    # Found in values_block
    'op_eq':              poly_eq,
    'op_ne':              poly_ne,
    'op_contains':        poly_contains_any,
    'op_not_contains':    lambda x, y : poly_false(poly_contains_any(x, y)),
    'op_matches':         poly_matches,
    'op_not_matches':     poly_not_match,
    'op_matches_all':     poly_matches_all,
}

# These apply only to values blocks, not ranges or inequalities
_CHOOSE_NEG_OPS = ['not_values_block', 'op_ne', 'op_not_contains', 'op_not_matches', 'op_not_imatches']

@control_statement
@bound_ops("Choose Using")
def execute_choose_using(ctx: ExecContext, statement: Tree) -> None:
    """
**Choose from a set of statements based on a value**

* Choose [All] Using *expression* :\\
  &emsp;&emsp;When [Not] Empty : *statement*&hellip;\\
  &emsp;&emsp;When [Not] Negative : *statement*&hellip;\\
  &emsp;&emsp;When [Not] Positive : *statement*&hellip;\\
  &emsp;&emsp;When [Not] Even : *statement*&hellip;\\
  &emsp;&emsp;When [Not] Odd : *statement*&hellip;\\
  &emsp;&emsp;When [Not] *expression* [, *expression*]&hellip; : *statement*&hellip;\\
  &emsp;&emsp;When [Not] *expression* [To | Through | Thru] *expression* : *statement*&hellip;\\
  &emsp;&emsp;When [< | Less Than] *expression*: *statement*&hellip;\\
  &emsp;&emsp;When [>= | Not Less Than] *expression*: *statement*&hellip;\\
  &emsp;&emsp;When [> | Greater Than] *expression*: *statement*&hellip;\\
  &emsp;&emsp;When [<= | Not Greater Than] *expression*: *statement*&hellip;\\
  &emsp;&emsp;When [Not] Matches *expression* [, *expression*]&hellip; : *statement*&hellip;\\
  &emsp;&emsp;When Matches All *expression* [, *expression*]&hellip; : *statement*&hellip;\\
  &emsp;&emsp;When [Not] Contains *expression* [, *expression*]&hellip; : *statement*&hellip;\\
  &emsp;&emsp;Otherwise : *statement*&hellip;\\
  [End-Choose | End] [;]

The expression in the `Choose` statement is evaluated and it becomes the
*desired value* which is compared against values in `When` clauses.

The values in `When` clauses are examined in order. Matching values may
be specified as a single value, in comma separated groups, as ranges,
inequalities, or contents checks.
These may be prefixed with a `Not` to invert the matching.

Testing of `When` clauses terminates after the first match _unless_ `All`
is specified.

If none of the `When` clauses match the desired value the `Otherwise` cause,
if provided, is selected. Note that this clause _must_ follow all the `When`
causes, and that at least one `When` must be specified. When `All` is specified
`Otherwise` is skipped if another `When` clause has matched.

While complicated expressions can be used as the values in `When` it is recommended
that constant or references to constants be used.

```vgr
Set month To time.today.month
Choose Using month:
    When 1, 2, 12:  Set season To "winter"
    When 3, 4, 5:   Set season To "spring"
    When 6, 7, 8:   Set season To "summer"
    When 9, 10, 11: Set season To "fall"
    Otherwise: Assert False: "Invalid month {}", month
End-Choose
Print "Month", month, "is a", season, "month"

Choose Using user_input:
    When Is None:
        Print "Input required"
    When Matches "^[0-9]{5}$", "^[0-9]{5}-[0-9]{4}$":
        // ZIP with and without four digit extension
        Print "Looks like a ZIP code"
    When Matches "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$",
            "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\.[A-Za-z]{2,}$":
        // Email with and without subdomain
        Print "Looks like an email"
    When Matches "^\\+?[0-9]{10,15}$", "^[0-9]{3}-[0-9]{3}-[0-9]{4}$":
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
    ctx.echo_source(statement, statement.children[2 if do_all else 1])
    # NB: Operation test may cause a TypeError if there is a mismatch
    #     betweeen the desired_value's type, which drives "casting"
    #     and the resulting type of the expression
    # The first child is the expression used in the value comparisons
    desired_value = ctx.eval_expr(bind_operations(next(statement_children, None)))
    _exec_choose(ctx, do_all, statement_children, desired_value)

def _exec_choose(ctx: ExecContext, do_all: bool, statement_children, desired_value: Any=None) -> None:
    """Internal method that handles both forms"""
    choice_made = False
    for when_block in statement_children:
        chosen_block = None
        values_children = iter(when_block.children)
        # This section is for the Choose that doesn't have a desired value
        if when_block.data == "choice_block":
            choice_children = iter(when_block.children)
            # The first child is the expression to test
            # We do a Pythonic test for "True" here, avoiding internal conversions
            if ctx.eval_expr(bind_operations(next(choice_children, None))):
                ctx.echo_source(when_block, when_block.children[1])
                # After the expression to test the iterator
                # points to the following statements
                chosen_block = choice_children
        # This section is for tests that don't use an expression
        # TODO future "is_defined" "is not defined"
        elif when_block.data in ['is_empty_block', 'is_not_empty_block', 'is_neg_block', 'is_pos_block', 'is_even_block', 'is_odd_block']:
            test_op = _CHOOSE_OPS.get(when_block.data)
            if test_op(desired_value):
                ctx.echo_source(when_block, when_block.children[0])
                chosen_block = values_children
        elif when_block.data in ['values_block', 'not_values_block']:
            # If there is a node in front of our list of values
            # it is a specialized operator rather than the one encoded
            # in the name of the block itself
            when_end_index = 1
            if when_block.children[0].data == 'value_list':
                op_name = when_block.data
            else:
                op_name = next(values_children).data
                when_end_index += 1
            test_op = _CHOOSE_OPS.get(op_name)
            # Negative tests distribute the not treating the comma to an "and":
            #     "when not 1, 2, 3" -> "when not 1 <and> not 2 <and> not 3"
            # All tests must pass, ending evaluation on the first failure
            if op_name in _CHOOSE_NEG_OPS:
                chosen_block = values_children
                for target_expr in next(values_children, None).children:
                    if not test_op(desired_value, ctx.eval_expr(bind_operations(target_expr))):
                        chosen_block = None
                        break
            else:
                # Positive tests treat the comma as an "or":
                #     "when 1,2,3" -> "when 1 <or> 2 <or> 3"
                # The first test to pass ends evaluation and executes the block
                for target_expr in next(values_children, None).children:
                    if test_op(desired_value, ctx.eval_expr(bind_operations(target_expr))):
                        chosen_block = values_children
                        break
            if chosen_block:
                ctx.echo_source(when_block, when_block.children[when_end_index])
        elif when_block.data in ['range_block', 'not_range_block']:
            test_op = _CHOOSE_OPS.get(when_block.data)
            lo_value = ctx.eval_expr(bind_operations(next(values_children)))
            hi_value = ctx.eval_expr(bind_operations(next(values_children)))
            if poly_lt(hi_value, lo_value): lo_value, hi_value = hi_value, lo_value
            if test_op(poly_ge(desired_value, lo_value) and poly_le(desired_value, hi_value)):
                ctx.echo_source(when_block, when_block.children[2])
                chosen_block = values_children
        elif when_block.data == 'ineq_block':
            test_op = _CHOOSE_OPS.get(next(values_children).data)
            if test_op(desired_value, ctx.eval_expr(bind_operations(next(values_children)))):
                ctx.echo_source(when_block, when_block.children[2])
                chosen_block = values_children
        else:
            if not choice_made:
                # it is 'otherwise_block' which is automatically selected
                ctx.echo_source(when_block, when_block.children[0])
                chosen_block = values_children
        # If a block of statements was chosen execute them
        if chosen_block is not None:
            choice_made = True
            ctx.dispatch_statements(chosen_block)
            # do_all can let multiple when blocks execute, but
            # when it is off, the first one chosen ends the loop
            if not do_all: break
    # end of "for when_block"
