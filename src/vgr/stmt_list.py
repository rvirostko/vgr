"""
Handlers for list related statements
"""

from typing import Any

from lark import Tree

from .app_exceptions import VgrRuntimeError
from .evaluate import get_writable_var_path
from .exec_context import ExecContext
from .mathpak import bound_ops

@bound_ops("Append")
def execute_list_append(ctx: ExecContext, statement: Tree) -> None:
    """
**Add one or more items to the end of a list**

* Append _item_ To [List] _variable_ [;]
* Append All _item_ To [List] _variable_ [;]

In the first form _item_ is added to the specified list, regardless of its type.
In the second form when _All_ is specified, if _item_ is a list, all of its
members are added to the specified list.
If _item_ is not a list itself, there is no difference between the first and
second forms.

If _variable_ is not defined it is created as an empty list.
If _variable_ is not a list, it is converted to a list.

```vgr
// Assume animals is ["cat", "dog", "fish"]

Append None To animals  → ["cat", "dog", "fish", None]

Append "rabbit" To animals → ["cat", "dog", "fish", "rabbit"]

Append ["bird"] To animals → ["cat", "dog", "fish", ["bird"]]

Append ["mouse", "rat"] To animals → ["cat", "dog", "fish", ["mouse", "rat"]]

Append All ["mouse", "rat"] To animals → ["cat", "dog", "fish", "mouse", "rat"]
```

Also see `Prepend` and `Insert`
"""
    idx, do_all = _extract_list_all(statement)
    idx, src = _eval_list_src(ctx, statement, idx, do_all)
    idx, path, dst = _eval_list_target(ctx, statement, idx)
    if src:
        dst.extend(src)
        if ctx.verbose: ctx.print_verbose('Appended', len(src), f'item{"s" if len(src) != 1 else ""} To', '.'.join(path))
    else:
        if ctx.verbose: ctx.print_verbose('List', '.'.join(path), 'unchanged')

@bound_ops("Prepend")
def execute_list_prepend(ctx: ExecContext, statement: Tree) -> None:
    """
**Add one or more items to the beginning of a list**

* Prepend _item_ To [List] _variable_ [;]
* Prepend All _item_ To [List] _variable_ [;]

In the first form _item_ is added to the specified list, regardless of its type.
In the second form when _All_ is specified, if _item_ is a list, all of its
members are added to the specified list.
If _item_ is not a list itself, there is no difference between the first and
second forms.

If _variable_ is not defined it is created as an empty list.
If _variable_ is not a list, it is converted to a list.

```vgr
// Assume animals is ["cat", "dog", "fish"]

Prepend None To animals → [None, "cat", "dog", "fish"]

Prepend "rabbit" To animals → ["rabbit", "cat", "dog", "fish"]

Prepend ["bird"] To animals → [["bird"], "cat", "dog", "fish"]

Prepend ["mouse", "rat"] To animals → [["mouse", "rat"], "cat", "dog", "fish"]

Prepend All ["mouse", "rat"] To animals → ["mouse", "rat", "cat", "dog", "fish"]
```

Also see `Append` and `Insert`
"""
    idx, do_all = _extract_list_all(statement)
    idx, src = _eval_list_src(ctx, statement, idx, do_all)
    idx, path, dst = _eval_list_target(ctx, statement, idx)
    if src:
        dst[:0] = src
        if ctx.verbose: ctx.print_verbose('Prepended', len(src), f'item{"s" if len(src) != 1 else ""} To', '.'.join(path))
    else:
        if ctx.verbose: ctx.print_verbose('List', '.'.join(path), 'unchanged')

@bound_ops("Insert")
def execute_list_insert(ctx: ExecContext, statement: Tree) -> None:
    """
**Insert one or more items into a list**

* Insert _item_ Into [List] _variable_ At [Position | Index] _position_ [;]
* Insert All _item_ Into [List] _variable_ At [Position | Index] _position_ [;]

In the first form _item_ is inserted to the specified list, regardless of its type.
In the second form when _All_ is specified, if _item_ is a list, all of its
members are inserted to the specified list.
If _item_ is not a list itself, there is no difference between the first and
second forms.

The _position_ argument must be a number and be greater than or equal to zero
and less than the length of the existing list.

If _variable_ is not defined it is created as an empty list.
If _variable_ is not a list, it is converted to a list.

```vgr
// Assume animals is ["cat", "dog", "fish"]

Insert None Into animals At 1 → ["cat", None, "dog", "fish"]

Insert "rabbit" Into animals At 1 → ["cat", "rabbit", "dog", "fish"]

Insert ["bird"] Into animals At 1 → ["cat", ["bird"], "dog", "fish"]

Insert ["mouse", "rat"] Into animals At 1 → ["cat", ["mouse", "rat"], "dog", "fish"]

Insert All ["mouse", "rat"] Into animals At 1 → ["cat", "mouse", "rat", "dog", "fish"]
```

Also see `Append` and `Prepend`
"""
    idx, do_all = _extract_list_all(statement)
    idx, src = _eval_list_src(ctx, statement, idx, do_all)
    idx, path, dst = _eval_list_target(ctx, statement, idx)
    pos_expr = statement.children[idx]
    pos = ctx.eval_to_int(pos_expr, 'Position')
    if pos < 0 or pos > len(dst):
        raise VgrRuntimeError(pos_expr, ValueError(f'Position {pos} is invalid'))
    if src:
        dst[pos:pos] = src
        if ctx.verbose: ctx.print_verbose('Inserted', len(src), f'item{"s" if len(src) != 1 else ""} Into', '.'.join(path), 'At', pos)
    else:
        if ctx.verbose: ctx.print_verbose('List', '.'.join(path), 'unchanged')

# Combine doc with list_remove
def execute_list_remove_first(ctx: ExecContext, statement: Tree) -> None:
    idx, path, dst = _eval_list_target(ctx, statement, 0)
    gexpr, giving_path = _eval_list_giving(ctx, statement, idx)
    if dst:
        if giving_path:
            _set_list_giving(ctx, giving_path, dst.pop(0), gexpr)
        else:
            del dst[0]
        if ctx.verbose: ctx.print_verbose('Removed first item from', '.'.join(path))
    else:
        if giving_path:
            _set_list_giving(ctx, giving_path, None, gexpr)
        if ctx.verbose: ctx.print_verbose('List', '.'.join(path), 'unchanged')

# Combine doc with list_remove
def execute_list_remove_last(ctx: ExecContext, statement: Tree) -> None:
    idx, path, dst = _eval_list_target(ctx, statement, 0)
    gexpr, giving_path = _eval_list_giving(ctx, statement, idx)
    if dst:
        if giving_path:
            _set_list_giving(ctx, giving_path, dst.pop(), gexpr)
        else:
            del dst[-1]
        if ctx.verbose: ctx.print_verbose('Removed last item from', '.'.join(path))
    else:
        if giving_path:
            _set_list_giving(ctx, giving_path, None, gexpr)
        if ctx.verbose: ctx.print_verbose('List', '.'.join(path), 'unchanged')

@bound_ops("Remove")
def execute_list_remove(ctx: ExecContext, statement: Tree) -> None:
    """
**Remove one or more items from a list by position**

* Remove First [Item] From [List] _variable_ [Giving _removed_var_] [;]
* Remove Last [Item] From [List] _variable_ [Giving _removed_var_] [;]
* Remove _position_ From [List] _variable_ [Giving _removed_var_ ] [;]

The _position_ argument must be a number, or a list of numbers,
which are greater than or equal to zero
and less than the length of the existing list.

If _variable_ is not defined it is created as an empty list.
If _variable_ is not a list, it is converted to a list.

The _removed_var_ receives a list of the items removed from the list.

```vgr
**TODO**
```
"""
    idx, positions = _eval_and_advance(ctx, statement, 0)
    idx, path, dst = _eval_list_target(ctx, statement, idx)
    gexpr, giving_path = _eval_list_giving(ctx, statement, idx)
    rcount, removed = _remove_items(dst, _normalize_positions(positions))
    if rcount:
        if giving_path:
            # if caller only asked for one item, return one item
            if not isinstance(positions, (list, tuple)): removed = removed[0]
            _set_list_giving(ctx, giving_path, removed, gexpr)
        if ctx.verbose: ctx.print_verbose('Removed', rcount, f'item{"s" if rcount != 1 else ""} From', '.'.join(path))
    else:
        if giving_path:
            _set_list_giving(ctx, giving_path, None, gexpr)
        if ctx.verbose: ctx.print_verbose('List', '.'.join(path), 'unchanged')

# 1) Replace 5 in lst with "a" -- item[5] = "a"
# 2) Replace 5 in lst with ["a", "b"] -- item[5] = ["a", "b"]
# 3) Replace [5, 6] in lst with "a" -- replaces both 5 and 6 with "a"
# 4) Replace [5, 6] in lst with ["a", "b"] -- replaces both 5 and 6 with ["a", "b"]

#list_replace: "Replace"i expr "In"i "List"i? var_name "With"i expr list_giving? _SEMICOLON?
@bound_ops("Replace")
def execute_list_replace(ctx: ExecContext, statement: Tree) -> None:
    """
**Replace one or more items in a list by position**

* Replace _position_ In [List] _variable_ [Giving _replaced_var_ ] [;]

The _position_ argument must be a number, or a list of numbers,
which are greater than or equal to zero
and less than the length of the existing list.

If _variable_ is not defined it is created as an empty list.
If _variable_ is not a list, it is converted to a list.

The _replaced_var_ receives a list of the items removed from the list.

```vgr
**TODO**
```
"""
    # finish!

#-----------------------------------------------------------

def _extract_list_all(statement: Tree, idx: int=0) -> tuple[int, bool]:
    if isinstance(statement.children[idx], Tree) and statement.children[0].data == "list_all":
        return idx + 1, True
    return idx, False

def _eval_and_advance(ctx: ExecContext, statement: Tree, idx: int) -> tuple[int, Any]:
    return idx + 1, ctx.eval_expr(statement.children[idx])

def _eval_list_src(ctx: ExecContext, statement: Tree, idx: int, do_all: bool) -> tuple[int, Any]:
    idx, src = _eval_and_advance(ctx, statement, idx)
    if do_all and isinstance(src, (list, tuple)): return idx, src
    return idx, [src]

def _eval_list_target(ctx: ExecContext, statement: Tree, idx: int) -> tuple[int, tuple[str], list]:
    var_path = get_writable_var_path(ctx, statement.children[idx])
    idx += 1
    value = ctx.get_var(*var_path)
    if value is None: return idx, var_path, ctx.set_var([], *var_path)
    if isinstance(value, tuple): return idx, var_path, ctx.set_var([*value], *var_path)
    if not isinstance(value, list): return idx, var_path, ctx.set_var([value], *var_path)
    return idx, var_path, value

def _eval_list_giving(ctx: ExecContext, statement: Tree, idx: int) -> tuple[Tree, tuple[str]]:
    """Returned path is vetted so that is valid and writable"""
    # NB: since this relies on length alone, it can be fragile
    giving_expr = statement.children[idx] if idx < len(statement.children) else None
    return giving_expr, get_writable_var_path(ctx, giving_expr) if giving_expr else None

def _set_list_giving(ctx: ExecContext, path: tuple[str], value: Any, expr: Tree) -> None:
    # TODO: if of length one, should we unpack
    # TODO is value always going to be an list
    try:
        ctx.set_var(value, *path)
    except Exception as e:
        raise VgrRuntimeError(expr, e) from e

def _normalize_positions(positions) -> list:
    """By the end, we should have a list filled with ints or Nones"""
    if positions is None: return []
    if isinstance(positions, tuple): positions = [*positions]
    if not isinstance(positions, list): positions = [positions]
    return [_to_int(pos) for pos in positions]

def _to_int(item: Any) -> int:
    if isinstance(item, int): return item
    if isinstance(item, float): return int(item)
    if isinstance(item, str):
        try:
            return int(float(item.strip()))
        except ValueError:
            return None
    return None

def _remove_items(dst: list, removals: list) -> list:
    removal_mapping = {}
    for index, pos in enumerate(removals):
        if pos is not None: removal_mapping.setdefault(pos, []).append(index)
    count = 0
    removed = [None] * len(removals)
    # For each, remove the item at pos, and update result
    # using indicies where the removal was requested
    # Sort positions in descending order
    for pos, indices in sorted(removal_mapping.items(), key=lambda mapping: mapping[0], reverse=True):
        # Invalid positions are ignored
        # TODO should generate an error
        if 0 <= pos < len(dst):
            removed_value = dst[pos]
            del dst[pos]
            count += 1
            # If we pulled out a None, no need to update removed[]
            if removed_value is not None:
                for index in indices:
                    removed[index] = removed_value
    return count, removed
