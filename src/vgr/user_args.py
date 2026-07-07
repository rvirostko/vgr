
from .exec_context import ExecContext

USER_ARGS = 'args'

def set_user_args(ctx: ExecContext, data: list) -> None:
    assert data is None or isinstance(data, list)
    ctx.set_var(data or [], USER_ARGS)
