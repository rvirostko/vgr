
from lark import Tree, Token

class StatementSourceMgr:
    def __init__(self):
        self._statement_text: str = ''
        self._origin: str = ''

    def set_statement(self, statement_text, origin: str='') -> None:
        self._statement_text: str = statement_text or ''
        self._origin: str = origin

    def source_for(self, tree: Tree) -> str:
        if not self._statement_text or tree is None: return ''
        start, end = self._subtree_span(tree)
        return self._statement_text[start:end]

    def origin(self) -> str:
        return self._origin

    def statement_text(self) -> str:
        return self._statement_text

    def _subtree_span(self, node):
        """
        Recursively finds the start and end positions of a subtree in the source text.

        Returns:
            (start_pos, end_pos) where:
            - start_pos is the earliest character index of any token in the subtree.
            - end_pos is the last character index + 1 of any token in the subtree.
            If no tokens are found, returns (None, None).
        """
        start_pos = None
        end_pos = None

        def traverse(n):
            nonlocal start_pos, end_pos
            if isinstance(n, Token):
                if n.start_pos is not None:
                    if start_pos is None or n.start_pos < start_pos:
                        start_pos = n.start_pos
                    if end_pos is None or (n.end_pos is not None and n.end_pos > end_pos):
                        end_pos = n.end_pos
            elif isinstance(n, Tree):
                for child in n.children: traverse(child)
                # Some Tree nodes have meta positions, but we can't fully trust it.
                if hasattr(n, "meta") and n.meta:
                    if hasattr(n.meta, "start_pos") and n.meta.start_pos is not None:
                        if start_pos is None or n.meta.start_pos < start_pos:
                            start_pos = n.meta.start_pos
                    if hasattr(n.meta, "end_pos") and n.meta.end_pos is not None:
                        if end_pos is None or n.meta.end_pos > end_pos:
                            end_pos = n.meta.end_pos
        traverse(node)
        return start_pos, end_pos

SSM = StatementSourceMgr()

