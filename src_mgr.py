"""
Utility functions for working with the source associated with statements
"""

from lark import Tree, Token

class StatementSourceMgr:
    def __init__(self):
        self._stack = []

    @property
    def current(self) -> tuple:
        return self._stack[-1]

    def push(self, origin: str, text) -> None:
        self._stack.append((origin or '', text or ''))

    def pop(self) -> None:
        self._stack.pop()


    def source_for(self, node: Tree, end_node: Tree=None) -> str:
        """
        Retrurn the source for a part of a parse graph.
        For a single argument, the source for it is returned.
        When end_node is provided, it is for the source up to but
        not including that node.
        """
        _, text = self.current
        if not text or node is None: return ''
        start_pos, end_pos = StatementSourceMgr.span(node)
        if end_node is not None:
            # Up to, but not including the end node
            end_pos = max(end_pos, StatementSourceMgr.span(end_node)[0])
        return text[start_pos : end_pos]

    @staticmethod
    def span(item: Tree) -> tuple:
        """
        Return (start_pos, end_pos) for a lark Tree or Token.
        We need to do this because of the way expression
        trees can be re-arranged
        """
        if isinstance(item, Token): return item.start_pos, item.end_pos
        assert isinstance(item, Tree)
        start, end = item.meta.start_pos, item.meta.end_pos

        def _walk(node: Tree) -> None:
            nonlocal start, end
            if isinstance(node, Tree):
                start = min(start, node.meta.start_pos)
                end = max(end, node.meta.end_pos)
                for child in node.children: _walk(child)
            else:
                start = min(start, node.start_pos)
                end = max(end, node.end_pos)

        if item.children: _walk(item)
        return start, end

    @staticmethod
    def line_number(item: Tree) -> int:
        """
        Return the starting line number for a lark Tree or Token.
        """
        if isinstance(item, Token): return item.line
        assert isinstance(item, Tree)
        line = item.meta.line

        def _walk(node: Tree) -> None:
            nonlocal line
            if isinstance(node, Tree):
                line = min(line, node.meta.line)
                for child in node.children: _walk(child)
            else:
                line = min(line, node.line)

        if item.children: _walk(item)
        return line

SSM = StatementSourceMgr()
