

from typing import Any
import sys
from lark import Tree, Token

def print_tree(item: Any, indent=2) -> None:
    prefix = ' ' * indent  # Indentation for nested levels
    if isinstance(item, Tree):
        tree: Tree = item
        op = getattr(tree, "op_name", lambda: "")()
        print(f'{prefix}({tree.data}:{op}', end=('\n' if tree.children else ''), file=sys.stderr)
        for child in tree.children: print_tree(child, indent + 2)
        print(f'{prefix if tree.children else ""})', file=sys.stderr)  # close the rule
    else:
        if isinstance(item, Token):
            token: Token = item
            print(f'{prefix}{token.type}: {token.value} (Pos: {token.line}:{token.column} {type(token.value).__name__})', file=sys.stderr)
        else:
            raise ValueError(item.type()) # What else can there be?
