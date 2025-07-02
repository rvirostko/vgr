"""
Handlers for list related statements
"""

from typing import Any

from lark import Tree

from app_exceptions import VgrRuntimeError
from data_dict import DataDictionary
from dd_config import dd_path
from evaluate import eval_expr, eval_to_int
from redir import print_stderr

def _extract_list_all(statement: Tree, idx: int=0) -> tuple[int, bool]:
    if isinstance(statement.children[idx], Tree) and statement.children[0].data == "list_all":
        return idx + 1, True
    return idx, False

def _eval_and_advance(dd: DataDictionary, statement: Tree, idx: int) -> tuple[int, Any]:
    return idx + 1, eval_expr(dd, statement.children[idx])

def _eval_list_src(dd: DataDictionary, statement: Tree, idx: int, do_all: bool) -> tuple[int, Any]:
    idx, src = _eval_and_advance(dd, statement, idx)
    if do_all and isinstance(src, (list, tuple)): return idx, src
    return idx, [src]

def _eval_list_target(dd: DataDictionary, statement: Tree, idx: int) -> tuple[int, tuple[str], list]:
    path = dd_path(statement.children[idx])
    idx += 1
    value = dd.get_var_user(*path)
    if value is None: return idx, path, dd.set_var_user([], *path)
    if isinstance(value, tuple): return idx, path, dd.set_var_user([*value], *path)
    if not isinstance(value, list): return idx, path, dd.set_var_user([value], *path)
    return idx, path, value

def _eval_list_giving(statement: Tree, idx: int) -> tuple[Tree, tuple[str]]:
    # NB: since this relies on length alone, it can be fragile
    gexpr = statement.children[idx] if idx < len(statement.children) else None
    return gexpr, dd_path(gexpr) if gexpr else None

def _set_list_giving(dd: DataDictionary, path: tuple[str], value: Any, expr: Tree) -> None:
    try:
        dd.set_var_user(value, *path)
    except Exception as e:
        raise VgrRuntimeError(expr, e) from e

def execute_list_append(dd: DataDictionary, statement: Tree) -> None:
    idx, do_all = _extract_list_all(statement)
    idx, src = _eval_list_src(dd, statement, idx, do_all)
    idx, path, dst = _eval_list_target(dd, statement, idx)
    if src:
        dst.extend(src)
        if dd.verbose:
            l = len(src)
            print_stderr('Appended', l, f'item{"s" if l != 1 else ""} To', '.'.join(path))
    else:
        if dd.verbose:
            print_stderr('List', '.'.join(path), 'unchanged')

def execute_list_prepend(dd: DataDictionary, statement: Tree) -> None:
    idx, do_all = _extract_list_all(statement)
    idx, src = _eval_list_src(dd, statement, idx, do_all)
    idx, path, dst = _eval_list_target(dd, statement, idx)
    if src:
        dst[:0] = src
        if dd.verbose:
            l = len(src)
            print_stderr('Prepended', l, f'item{"s" if l != 1 else ""} To', '.'.join(path))
    else:
        if dd.verbose:
            print_stderr('List', '.'.join(path), 'unchanged')

def execute_list_insert(dd: DataDictionary, statement: Tree) -> None:
    idx, do_all = _extract_list_all(statement)
    idx, src = _eval_list_src(dd, statement, idx, do_all)
    idx, path, dst = _eval_list_target(dd, statement, idx)
    pos_expr = statement.children[idx]
    pos = eval_to_int(dd, pos_expr, 'Position')
    if pos < 0 or pos > len(dst):
        raise VgrRuntimeError(pos_expr, ValueError(f'Position {pos} is invalid'))
    if src:
        dst[pos:pos] = src
        if dd.verbose:
            l = len(src)
            print_stderr('Inserted', l, f'item{"s" if l != 1 else ""} Into', '.'.join(path), 'At', pos)
    else:
        if dd.verbose:
            print_stderr('List', '.'.join(path), 'unchanged')

def execute_list_remove_first(dd: DataDictionary, statement: Tree) -> None:
    idx, path, dst = _eval_list_target(dd, statement, 0)
    gexpr, giving_path = _eval_list_giving(statement, idx)
    if dst:
        if giving_path:
            _set_list_giving(dd, giving_path, dst.pop(0), gexpr)
        else:
            del dst[0]
        if dd.verbose:
            print_stderr('Removed first item from', '.'.join(path))
    else:
        if giving_path:
            _set_list_giving(dd, giving_path, None, gexpr)
        if dd.verbose:
            print_stderr('List', '.'.join(path), 'unchanged')

def execute_list_remove_last(dd: DataDictionary, statement: Tree) -> None:
    idx, path, dst = _eval_list_target(dd, statement, 0)
    gexpr, giving_path = _eval_list_giving(statement, idx)
    if dst:
        if giving_path:
            _set_list_giving(dd, giving_path, dst.pop(), gexpr)
        else:
            del dst[-1]
        if dd.verbose:
            print_stderr('Removed last item from', '.'.join(path))
    else:
        if giving_path:
            _set_list_giving(dd, giving_path, None, gexpr)
        if dd.verbose:
            print_stderr('List', '.'.join(path), 'unchanged')

def execute_list_remove(dd: DataDictionary, statement: Tree) -> None:
    # While we allow "all" it does not change behavior
    idx, _do_all = _extract_list_all(statement)
    idx, positions = _eval_and_advance(dd, statement, idx)
    idx, path, dst = _eval_list_target(dd, statement, idx)
    gexpr, giving_path = _eval_list_giving(statement, idx)
    rcount, removed = _remove_items(dst, _normalize_positions(positions))
    if rcount:
        if giving_path:
            # if caller only asked for one item, return one item
            if not isinstance(positions, (list, tuple)): removed = removed[0]
            _set_list_giving(dd, giving_path, removed, gexpr)
        if dd.verbose:
            print_stderr('Removed', rcount, f'item{"s" if rcount != 1 else ""} From', '.'.join(path))
    else:
        if giving_path:
            _set_list_giving(dd, giving_path, None, gexpr)
        if dd.verbose:
            print_stderr('List', '.'.join(path), 'unchanged')

# All means treat as separate entities
# 1) Replace 5 in item with "a" -- item[5] = "a"
# 2) Replace 5 in item with All "a" -- item[5] = "a", All superflous because on single index
# 3) Replace [5, 6] in item with "a" -- replaces both 5 and 6 with "a"
# 4) Replace [5, 6] in item with All "a" -- Same as #3, following reasoning of #2
# 5) Replace 5 in item with ["a", "b"] -- item[5] = ["a", "b"]; effectively the same as #1
# 6) Replace 5 in item with All ["a", "b"] -- same as #1 and "b" is unused
# 7) Replace [5, 6] in item with ["a", "b"] -- same as #3
# 8) Replace [5, 6] in item with All ["a", "b"] -- item[5] = "a", item[6] = "b"
# 8a) ...All ["a"] -- item[6] is either skipped or set to None
# 8b) ...All ["a", "b", "c"] -- "c" is ignored

# The general logic seems to be to create a zip longest between indicies values
# But, for the source is shorter than the indicies, and you have a single value, you repeat it
#    expr - indicies
#    var_name - target
#    list_all? - do_all
#    expr - source
#    list_giving?

def execute_list_replace(dd: DataDictionary, statement: Tree) -> None:
    idx, positions = _eval_and_advance(dd, statement, 0)
    idx, path, dst = _eval_list_target(dd, statement, idx)
    idx, do_all = _extract_list_all(statement, idx)
    gexpr, giving_path = _eval_list_giving(statement, idx)

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
        if 0 <= pos < len(dst):
            removed_value = dst[pos]
            del dst[pos]
            count += 1
            if removed_value is not None:
                for index in indices:
                    removed[index] = removed_value
    return count, removed
