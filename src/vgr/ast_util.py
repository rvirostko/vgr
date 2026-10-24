from typing import Any
from copy import deepcopy

from lark import Token, Tree
from lark.tree import Meta

VAR_REF = 'var_ref'

def is_name_token(node) -> bool:
    return isinstance(node, Token) and node.type == 'NAME'

def is_var_name(node) -> bool:
    return isinstance(node, Tree) and node.data == 'var_name'

def is_var_ref(node) -> bool:
    return isinstance(node, Tree) and node.data == VAR_REF

def is_constant(node) -> bool:
    return isinstance(node, Token) and node.type == 'CONST'

def create_meta(node) -> Meta:
    if isinstance(node, Tree): return deepcopy(node.meta)
    if isinstance(node, Token):
        meta = Meta()
        meta.start_pos = node.start_pos
        meta.end_pos = node.end_pos
        meta.line = node.line
        meta.end_line = node.end_line
        meta.column = node.column
        meta.end_column = node.end_column
        return meta
    return None

def create_const_token(value: Any, meta_start, meta_end=None) -> Token:
    meta_end = meta_end or meta_start
    return Token('CONST', value,
                meta_start.start_pos, meta_start.line,     meta_start.column,
                meta_end.end_line,    meta_end.end_column, meta_end.end_pos)

def create_path_token(names, meta) -> Token:
    """names is a list/tuple of strings"""
    return Token('PATH', tuple(names),
                  line=meta.line,           column=meta.column,
                  end_line=meta.end_line,   end_column=meta.end_column,
                  start_pos=meta.start_pos, end_pos=meta.end_pos)
