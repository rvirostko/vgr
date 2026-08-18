
from lark import Tree
import pwinput
import sys

from .app_exceptions import VgrRuntimeError
from .builtins import (
    bound_ops,
    poly_shorten,
)
from .evaluate import do_set
from .exec_context import ExecContext
from .stmt_exec import get_writable_var_path

@bound_ops("Accept Input")
def execute_accept_input(ctx: ExecContext, statement: Tree) -> None:
    """
**Get user input**

* Accept Input [To] *variable* [*option*]
* Accept Input From [Input | Stdin] [To] *variable* [*option*]

When at end-of-file (or when not interactive) or if the user hits return
without entering any information, the contents of *variable* remains
unchanged. There is no limit on the length of user input, but it is a single line.

Options are

* Echo - this is the default
* No Echo - no output is generated
* Secure - typing is masked with asterisks

```vgr
Accept Input value         // input displayed
Accept Input value Echo    // input displayed
Accept Input value No Echo // nothing displayed
Accept Input value Secure  // asterisks displayed
```
"""
    c = 0
    # ignore but here for future functionality...
    if statement.children[c].data == 'stdin': c +=1
    var_path = get_writable_var_path(ctx, statement.children[c])
    c += 1
    # Default is to echo what is typed
    option = 'echo'
    # All options are mutually exclusive, so last one wins
    for child in statement.children[c:]:
        option = child.data
    if option == 'echo' or sys.stdin.isatty() == False:
        line = sys.stdin.readline()
    elif option == 'no_echo':
        line = pwinput.pwinput(prompt='', mask='')
    elif option == 'secure':
        line = pwinput.pwinput(prompt='', mask='*')
    else:
        # SNO
        raise VgrRuntimeError(statement.children[-1], ValueError(f'Accept option {option!r} not implemented')) # pragma no cover
    # Remove the trailing newline
    line = line.rstrip('\n') if line else line
    if line:
        if option == 'echo':
            do_set(ctx, line, *var_path)
        else:
            # If they requested no echo or secure, don't leave the value with verbose
            ctx.set_var(line, *var_path)
            if ctx.verbose: ctx.print_verbose('Set', '.'.join(var_path), 'To', poly_shorten(repr('*' * len(line))))
