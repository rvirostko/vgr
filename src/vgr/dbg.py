"""
Code used for development testing
"""

from typing import Any

from lark import Tree, Token

from .builtins import poly_type
from .redir import print_stderr

def print_tree(item: Any, indent=2) -> None:
    """Prints the parse tree including position information"""
    prefix = ' ' * indent  # Indentation for nested levels
    if isinstance(item, Tree):
        tree: Tree = item
        op = getattr(tree, "op_name", lambda: "")()
        meta = tree.meta
        if meta:
            line = getattr(meta, "line", "?")
            column = getattr(meta, "column", "?")
            end_line = getattr(meta, "end_line", "?")
            end_column = getattr(meta, "end_column", "?")
            pos_info = f' (Pos: {line}:{column}-{end_line}:{end_column})'
        else:
            pos_info = ''
        print_stderr(f'{prefix}({tree.data}:{op}{pos_info}', end=('\n' if tree.children else ''))
        for child in tree.children: print_tree(child, indent + 2)
        print_stderr(f'{prefix if tree.children else ""})')  # close the rule
    else:
        if isinstance(item, Token):
            token: Token = item
            print_stderr(f'{prefix}{token.type}: {token.value!r} '
                        f'(Pos: {token.line}:{token.column}-{token.end_line}:{token.end_column} {poly_type(token.value)!r})')
        else:
            raise ValueError(item.type()) # SNO: What else can there be?
