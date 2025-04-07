"""
Utility functions for working with the source associated with statements
"""

from lark import Tree

class StatementSourceMgr:
    def __init__(self):
        self._statement_text: str = ''
        self._origin: str = ''

    def set_statement(self, statement_text, origin: str='') -> None:
        self._statement_text: str = statement_text or ''
        self._origin: str = origin

    def source_for(self, tree: Tree, end_tree: Tree=None) -> str:
        if not self._statement_text or tree is None: return ''
        return self._statement_text[tree.meta.start_pos : tree.meta.end_pos if end_tree is None else end_tree.meta.start_pos]

    def origin(self) -> str:
        return self._origin

    def statement_text(self) -> str:
        return self._statement_text

SSM = StatementSourceMgr()
