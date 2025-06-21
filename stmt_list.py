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

def _extract_list_all(statement: Tree) -> tuple[int, bool]:
    if isinstance(statement.children[0], Tree) and statement.children[0].data == "list_all":
        return 1, True
    return 0, False

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
    idx, removals = _eval_and_advance(dd, statement, 0)
    idx, path, dst = _eval_list_target(dd, statement, idx)
    gexpr, giving_path = _eval_list_giving(statement, idx)
    #giving_array = isinstance(removals, (list, tuple))
    rcount, removed = _remove_items(dst, _normalize_removals(removals))
    if rcount:
        if giving_path:
            # if caller only asked for one item, return one item
            if not isinstance(removals, (list, tuple)): removed = removed[0]
            _set_list_giving(dd, giving_path, removed, gexpr)
        if dd.verbose:
            print_stderr('Removed', rcount, f'item{"s" if l != 1 else ""} From', '.'.join(path), 'At', pos)
    else:
        if giving_path:
            _set_list_giving(dd, giving_path, None, gexpr)
        if dd.verbose:
            print_stderr('List', '.'.join(path), 'unchanged')

def _normalize_removals(removals) -> list:
    """By the end, we should have a list filled with ints or Nones"""
    if removals is None: return []
    if isinstance(removals, tuple): removals = [*removals]
    if not isinstance(removals, list): removals = [removals]
    return [_to_int(item) for item in removals]

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
    positions = {}
    for index, pos in enumerate(removals):
        if pos is not None: positions.setdefault(pos, []).append(index)
    count = 0
    removed = [None] * len(removals)
    # For each, remove the item at pos, and update result
    # using indicies where the removal was requested
    # Sort positions in descending order
    for pos, indexes in sorted(positions.items(), key=lambda item: item[0], reverse=True):
        # Invalid positions are ignored
        if 0 <= pos < len(dst):
            removed_value = dst[pos]
            del dst[pos]
            count += 1
            if removed_value is not None:
                for i in indexes:
                    removed[i] = removed_value
    return count, removed
