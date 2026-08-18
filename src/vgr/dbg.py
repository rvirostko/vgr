"""
Code used for development testing
"""

from typing import Any

from lark import Tree, Token

from .builtins import poly_type
from .redir import print_stderr

def print_tree(item: Any, indent=2) -> None:
    """Prints the parse tree including position information"""
    def _fmt_pos(meta) -> str:
        if meta:
            values = tuple(getattr(meta, attr, None) for attr in ("line", "column", "end_line", "end_column"))
            if None not in values:
                return ' (Pos: {}:{}-{}:{})'.format(*values)
        return ''
    prefix = ' ' * indent  # Indentation for nested levels
    if isinstance(item, Tree):
        tree: Tree = item
        op = getattr(tree, "op_name", lambda: "")()
        pos_info = _fmt_pos(tree.meta)
        print_stderr(f'{prefix}({tree.data}:{op}{pos_info}',
                     end=('\n' if tree.children else ''))
        for child in tree.children: print_tree(child, indent + 2)
        print_stderr(f'{prefix if tree.children else ""})')  # close the rule
    else:
        if isinstance(item, Token):
            token: Token = item
            pos_info = _fmt_pos(token)
            print_stderr(f'{prefix}{token.type}: {token.value!r} {poly_type(token.value)!r}{pos_info}')
        else:
            # SNO: What else can there be?
            raise ValueError(item.type()) # pragma no cover
