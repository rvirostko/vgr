"""
Functions is responsible for converting a requested function name to an implementation.
It also generates the grammar fragments used to identify the built-in functions.
"""

from collections import defaultdict
from functools import lru_cache
from typing import Any, Callable
import inspect

from .builtins.general import poly_unique
from .builtins.registry import BuiltinRegistry

# Binds a (pretty) name to the function to be executed
# Additionally, we should use functions here rather than lambdas
# so we can grab the __DOC__ for help functions.
_FUNC_OPS: dict[str, Callable[..., Any]] = {}

# This index provides a way to find functions independent of case.
# Use get_function_op() to find entries.
_FUNC_INDEX: list[str] = {}

@lru_cache
def get_function_entries() -> dict[str, tuple[Callable[..., Any], str, str]]:
    """
    key: function name
    value: function, name (lc), documentation
    """
    return {
        name: (func, name.lower(), (func.__doc__ or '').lower())
        for name, func in _FUNC_OPS.items()
    }

def function_names_pattern() -> str:
    """
    Return a regex string that will match built-in
    function names.
    """
    functions = sorted(_FUNC_OPS.keys(), key=len, reverse=True)
    return r"(?i)\b(?:" + "|".join(functions) + r")(?=\s*\()"

def add_builtin_functions() -> None:
    add_functions('built-in', BuiltinRegistry.items())

def add_functions(extn_name: str, function_mapping) -> None:
    for name, function in function_mapping:
        lc = name.lower()
        if lc in _FUNC_INDEX: raise ValueError(f'Extension {extn_name!r} tried to redefine {name!r}')
        _FUNC_OPS[name] = function
        _FUNC_INDEX[lc] = name

# The max value of an arg range when we have variable arguments
_IS_VARARGS = float('inf')

def get_function(name: str) -> tuple[str, Callable[..., Any]]:
    """Get the entry for the named function: (canonical_name, function)"""
    canonical_name = _FUNC_INDEX.get(name.lower(), None)
    if canonical_name is None:
        # SNO
        raise ValueError(f'Function {name!r} has no canonical name') # pragma no cover
    return (canonical_name, _FUNC_OPS.get(canonical_name))

def get_function_op(name: str) -> Callable[..., Any]:
    """Given a function name get the function that implements it"""
    function = get_function(name)
    if not function:
        # SNO
        raise NotImplementedError(f'Function {name!r} not implemented') # pragma no cover
    return function[1]

def get_function_defs(weight: int=99) -> str:
    """Dynamically generate the LARK patterns for functions based on our dictionary"""
    weight = str(weight)
    return (
                '// Functional style\n' +
                _gen_function_defs(weight, 'function', 'FNAME', False) +
                "\n\n" +
                '// Transformational pipeline style\n' +
                _gen_function_defs(weight, 'dotfunction', 'DOT_FNAME', True)
           )

def _gen_function_defs(weight: str, rule_name, group_label, dot_invocation: bool) -> str:
    # Group the functions acording to their argument counts
    # Take into account alias found in _FUNC_INDEX
    func_groups = defaultdict(list)
    for operation in _FUNC_OPS.values():
        arg_range = _get_arg_range(operation, dot_invocation)
        if arg_range is not None:
            func_groups[arg_range].extend(k for k, v in _FUNC_OPS.items() if v is operation)
    fnames = {}
    rc = ''
    # Generate the list of function names per arg count group
    for (min_args, max_args) in sorted(func_groups):
        label = f'{group_label}{min_args}'
        if min_args != max_args:
            label += f'_{"N" if max_args == _IS_VARARGS else max_args}'
        fnames[(min_args, max_args)] = label
        # We emit each by-arg-length group as a regex designed to eliminate
        # "prefix" problems. First we order the names longest to shortest, then end
        # the pattern in such as way that we look ahead for the open paren, but don't capture it.
        rc += '\n' + f'\n{label}.{weight}: /('
        rc += '|'.join(key for key in sorted(poly_unique(func_groups[(min_args, max_args)]), key=lambda x: (-len(x), x)))
        rc += ')\\s*(?=[(])/i'
    first = True
    # The function rule is a combination of the by-arg-length names and a pattern for their argument count
    for (min_args, max_args), label in fnames.items():
        if first:
            rc += f'\n{rule_name}.{weight}: '
            first = False
        else:
            rc += '    | '
        rc += label + ' "("'
        arg_count = 0
        # Required arguments patterns
        if min_args > 0:
            rc += ' expr'
            arg_count += 1
            for _ in range(min_args - 1):
                rc += ' _SEP expr'
                arg_count += 1
        # Do we have any optional arguments?
        if arg_count < max_args:
            if min_args == 0:
                rc += ' (expr'
                max_args = max_args if max_args == _IS_VARARGS else (max_args - 1)
            if max_args == _IS_VARARGS:
                rc += ' (_SEP expr)*'
            else:
                while arg_count < max_args:
                    rc += ' (_SEP expr)?'
                    arg_count += 1
            rc += ")?" if min_args == 0 else ''
        rc +=  ' ")"\n'
    return rc.strip()

def _get_arg_range(op, dot_invocation: bool) -> tuple:
    """Get the argument range for the function definition in the grammar"""
    if op is None: raise ValueError('Expected a function, but got None')
    # Get the signature of the function
    sig = inspect.signature(op)
    req_args = 0
    opt_args = 0
    positional = False
    for param in sig.parameters.values():
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            positional = True
        elif param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
            if param.default == inspect.Parameter.empty:
                req_args += 1
            else:
                opt_args += 1
    if dot_invocation:
        # Because the function is applied to something, we adjust
        if req_args > 0:
            req_args -= 1
        else:
            if opt_args > 0:
                opt_args -= 1
            else:
                # If the function can't be used as a dot function
                # because it has no args, so ignore it
                if not positional: return None
    return (req_args, _IS_VARARGS if positional else (req_args + opt_args))
