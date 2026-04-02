
import codecs

from lark import Tree

from .app_exceptions import VgrRuntimeError
from .builtins import (
    poly_type,
)
from .exec_context import ExecContext

def is_valid_encoding(name: str) -> bool:
    try:
        codecs.lookup(name)
        return True
    except LookupError:
        return False

def parse_encoding(ctx: ExecContext, opt: Tree) -> str:
    expr = opt.children[0]
    encoding = ctx.eval_expr_or_const(expr)
    if encoding is not None:
        if not isinstance(encoding, str):
            raise VgrRuntimeError(expr, TypeError(f'Encoding must be a string, found {poly_type(encoding)}'))
        encoding = encoding.strip()
        if encoding:
            if not is_valid_encoding(encoding):
                raise VgrRuntimeError(expr, TypeError(f'Encoding {encoding!r} is not valid'))
        else:
            encoding = None
    return encoding
